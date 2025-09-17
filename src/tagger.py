"""Utilities to link news articles to tickers in the research universe."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable


def _read_universe(universe_path: str | Path) -> dict[str, list[re.Pattern[str]]]:
    """Load ticker aliases and compile regex matchers for each ticker."""
    universe_file = Path(universe_path)
    if not universe_file.exists():
        raise FileNotFoundError(f"Universe file not found: {universe_file}")

    patterns: dict[str, list[re.Pattern[str]]] = {}
    with universe_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ticker = row["ticker"].strip()
            if not ticker:
                continue

            terms: set[str] = {ticker}
            name = (row.get("name") or "").strip()
            if name:
                terms.add(name)

            aliases = (row.get("aliases") or "").strip()
            if aliases:
                for alias in aliases.split(";"):
                    alias = alias.strip()
                    if alias:
                        terms.add(alias)

            compiled: list[re.Pattern[str]] = []
            for term in terms:
                escaped = re.escape(term)
                pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
                compiled.append(pattern)

            patterns[ticker] = compiled

    return patterns


def link_articles_to_tickers(
    articles: Iterable[dict], universe_path: str | Path = "config/universe.csv"
) -> list[dict]:
    """Attach matching tickers to each article based on its text content."""
    matchers = _read_universe(universe_path)
    tagged_articles: list[dict] = []

    for article in articles:
        title = article.get("title") or ""
        body = article.get("body") or ""
        text = f"{title} {body}"
        tickers: list[str] = []
        for ticker, patterns in matchers.items():
            if any(pattern.search(text) for pattern in patterns):
                tickers.append(ticker)

        unique_sorted = sorted(set(tickers))
        enriched = dict(article)
        enriched["tickers"] = unique_sorted
        tagged_articles.append(enriched)

    return tagged_articles


__all__ = ["link_articles_to_tickers"]
