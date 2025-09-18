"""Scoring engine that turns tagged articles into investment ideas."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import re
from typing import Iterable, Sequence

POSITIVE_KEYWORDS: Sequence[str] = (
    "beats",
    "record",
    "upgrade",
    "raise",
    "surge",
    "strong",
    "growth",
    "profit",
    "accretive",
    "win",
)
NEGATIVE_KEYWORDS: Sequence[str] = (
    "lawsuit",
    "probe",
    "miss",
    "downgrade",
    "cut",
    "shortfall",
    "recall",
    "fraud",
    "decline",
    "weak",
)

SOURCE_QUALITY: dict[str, float] = {
    "Reuters": 1.00,
    "Bloomberg": 0.95,
    "Financial Times": 0.92,
    "AP News": 0.88,
    "Associated Press": 0.88,
    "Wall Street Journal": 0.90,
    "CNBC": 0.80,
    "The Verge": 0.75,
    "TechCrunch": 0.72,
    "GlobeNewswire": 0.60,
    "Business Wire": 0.60,
    "Yahoo Entertainment": 0.35,
    "Biztoc.com": 0.30,
    "Thefly.com": 0.30,
}
DEFAULT_SOURCE_QUALITY = 0.50
MIN_SOURCE_QUALITY = 0.50

_SOURCE_QUALITY_LOOKUP = {name.lower(): score for name, score in SOURCE_QUALITY.items()}
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def normalize_title(title: str) -> str:
    """Normalize article titles for deduplication."""

    if not title:
        return ""

    normalized = str(title).lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s+[—-]\s+.*$", "", normalized)
    normalized = normalized.rstrip(" .,;:!?-–—")
    return normalized


def _source_quality(source: str | None) -> float:
    if not source:
        return DEFAULT_SOURCE_QUALITY
    return _SOURCE_QUALITY_LOOKUP.get(source.strip().lower(), DEFAULT_SOURCE_QUALITY)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return _EPOCH
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return _EPOCH


def _keyword_hits(text: str, keywords: Sequence[str]) -> set[str]:
    hits: set[str] = set()
    for keyword in keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            hits.add(keyword)
    return hits


def _dedupe_articles(articles: list[dict]) -> list[dict]:
    unique: list[dict] = []
    title_index: dict[str, int] = {}
    url_index: dict[str, int] = {}

    for article in articles:
        title_key = article.get("normalized_title") or ""
        url_key = article.get("url") or ""

        idx: int | None = None
        if title_key:
            idx = title_index.get(title_key)
        if idx is None and url_key:
            idx = url_index.get(url_key)

        if idx is None:
            unique.append(article)
            idx = len(unique) - 1
        else:
            existing = unique[idx]
            if _is_candidate_better(article, existing):
                unique[idx] = article

        if title_key:
            title_index[title_key] = idx
        if url_key:
            url_index[url_key] = idx

    return unique


def _is_candidate_better(candidate: dict, existing: dict) -> bool:
    candidate_quality = candidate.get("source_quality", DEFAULT_SOURCE_QUALITY)
    existing_quality = existing.get("source_quality", DEFAULT_SOURCE_QUALITY)
    if candidate_quality != existing_quality:
        return candidate_quality > existing_quality

    candidate_dt = candidate.get("published_at_dt", _EPOCH)
    existing_dt = existing.get("published_at_dt", _EPOCH)
    return candidate_dt > existing_dt


def score_day(tagged: Iterable[dict]) -> list[dict]:
    """Aggregate tagged articles into ticker-level idea scores."""

    per_ticker: dict[str, list[dict]] = defaultdict(list)

    for article in tagged:
        tickers = article.get("tickers") or []
        if not tickers:
            continue

        source = str(article.get("source") or "").strip() or "Unknown Source"
        quality = _source_quality(source)
        if quality < MIN_SOURCE_QUALITY:
            continue

        title = str(article.get("title") or "").strip()
        normalized_title = normalize_title(title)
        url = str(article.get("url") or "").strip()
        published_at = str(article.get("published_at") or "").strip()
        published_dt = _parse_datetime(published_at)

        text_parts = [
            title,
            article.get("summary") or "",
            article.get("description") or "",
            article.get("body") or "",
        ]
        text = " ".join(part for part in text_parts if part).lower()
        positive_hits = _keyword_hits(text, POSITIVE_KEYWORDS)
        negative_hits = _keyword_hits(text, NEGATIVE_KEYWORDS)

        for ticker in tickers:
            info = {
                "ticker": ticker,
                "source": source,
                "source_quality": quality,
                "title": title,
                "normalized_title": normalized_title,
                "url": url,
                "published_at": published_at,
                "published_at_dt": published_dt,
                "positive_hits": set(positive_hits),
                "negative_hits": set(negative_hits),
            }
            per_ticker[ticker].append(info)

    ideas: list[dict] = []
    for ticker, articles in per_ticker.items():
        deduped = _dedupe_articles(articles)
        if not deduped:
            continue

        article_count = len(deduped)
        base_score = 0.30 if article_count >= 2 else 0.10

        positive_hits: set[str] = set()
        negative_hits: set[str] = set()
        ticker_word = re.compile(rf"\b{re.escape(ticker.lower())}\b")
        q_in_title = False
        for item in deduped:
            positive_hits.update(item.get("positive_hits", set()))
            negative_hits.update(item.get("negative_hits", set()))
            normalized_title = item.get("normalized_title") or ""
            if normalized_title and ticker_word.search(normalized_title):
                q_in_title = True

        positive_bonus = min(0.20, 0.05 * len(positive_hits))
        negative_penalty = min(0.20, 0.05 * len(negative_hits))

        top_sources = sorted(deduped, key=lambda art: art["source_quality"], reverse=True)[:2]
        if top_sources:
            avg_quality = sum(item["source_quality"] for item in top_sources) / len(top_sources)
            source_boost = (avg_quality - 0.5) * 0.4
        else:
            source_boost = 0.0

        score = base_score + positive_bonus - negative_penalty + source_boost
        if q_in_title:
            score += 0.05
        if article_count >= 3:
            score += 0.05
        score = max(0.0, min(1.0, score))

        top_quality_avg = sum(item["source_quality"] for item in top_sources) / len(top_sources) if top_sources else 0.0

        why: list[str] = []
        if article_count >= 3:
            if top_quality_avg >= 0.75:
                why.append(f"{article_count} high-quality sources")
            else:
                why.append(f"{article_count} confirming articles")
        elif article_count == 2:
            if top_quality_avg >= 0.75:
                why.append("2 high-quality sources")
            else:
                why.append("2 sources")
        else:
            if top_quality_avg >= 0.75:
                why.append("Premium single-source")
            else:
                why.append("Single-source read")

        if positive_hits:
            why.append(f"{len(positive_hits)} positive keywords")
        if q_in_title:
            why.append("qInTitle match")
        if negative_hits and len(why) < 3:
            why.append(f"{len(negative_hits)} negative keywords")

        why = why[:3]

        sorted_articles = sorted(
            deduped,
            key=lambda art: (art["source_quality"], art["published_at_dt"]),
            reverse=True,
        )
        link_entries = []
        for item in sorted_articles:
            url = item.get("url")
            if not url:
                continue
            link_entries.append({
                "url": url,
                "published_at": item.get("published_at", ""),
            })
            if len(link_entries) == 5:
                break

        idea = {
            "ticker": ticker,
            "score": round(score, 4),
            "why": why,
            "links": link_entries,
        }
        ideas.append(idea)

    ideas.sort(key=lambda item: item["score"], reverse=True)
    return ideas


__all__ = ["score_day"]
