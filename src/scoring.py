"""Toy scoring engine that turns tagged articles into investment ideas."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

POSITIVE_KEYWORDS = {
    "beat",
    "beats",
    "growth",
    "surge",
    "record",
    "positive",
    "strong",
    "win",
    "upgraded",
    "expansion",
}
NEGATIVE_KEYWORDS = {
    "miss",
    "decline",
    "drop",
    "weak",
    "negative",
    "lawsuit",
    "loss",
    "downgrade",
    "pressure",
}

SOURCE_QUALITY = {
    "reuters": 1.0,
    "bloomberg": 0.95,
    "financial times": 0.9,
    "wall street journal": 0.9,
    "associated press": 0.7,
}
DEFAULT_SOURCE_QUALITY = 0.6


def _keyword_count(text: str, keywords: Iterable[str]) -> int:
    return sum(len(re.findall(rf"\b{re.escape(word)}\b", text)) for word in keywords)


def _score_article(article: dict) -> tuple[float, int, int]:
    title = article.get("title") or ""
    body = article.get("body") or ""
    text = f"{title} {body}".lower()

    pos = _keyword_count(text, POSITIVE_KEYWORDS)
    neg = _keyword_count(text, NEGATIVE_KEYWORDS)

    total = pos + neg
    if total == 0:
        sentiment = 0.5  # neutral
    else:
        sentiment = (pos - neg) / total
        sentiment = max(-1.0, min(1.0, sentiment))
        sentiment = (sentiment + 1.0) / 2.0

    source = (article.get("source") or "").lower()
    quality = SOURCE_QUALITY.get(source, DEFAULT_SOURCE_QUALITY)

    return sentiment * quality, pos, neg


def score_day(tagged: Iterable[dict]) -> list[dict]:
    """Aggregate tagged articles into ticker-level idea scores."""
    aggregated: dict[str, dict] = defaultdict(lambda: {"scores": [], "reasons": [], "links": []})

    for article in tagged:
        tickers = article.get("tickers") or []
        if not tickers:
            continue

        article_score, pos_count, neg_count = _score_article(article)
        source = article.get("source") or "Unknown Source"
        title = article.get("title") or "Untitled"
        url = article.get("url")

        snippet = f"{source} notes {pos_count} positive vs {neg_count} negative keywords in '{title}'."

        for ticker in tickers:
            bucket = aggregated[ticker]
            bucket["scores"].append(article_score)
            bucket["reasons"].append(snippet)
            if url and url not in bucket["links"]:
                bucket["links"].append(url)

    ideas: list[dict] = []
    for ticker, data in aggregated.items():
        if not data["scores"]:
            continue

        avg_score = sum(data["scores"]) / len(data["scores"])
        avg_score = max(0.0, min(1.0, avg_score))

        idea = {
            "ticker": ticker,
            "score": round(avg_score, 4),
            "why": data["reasons"],
            "links": data["links"],
        }
        ideas.append(idea)

    ideas.sort(key=lambda item: item["score"], reverse=True)
    return ideas


__all__ = ["score_day"]
