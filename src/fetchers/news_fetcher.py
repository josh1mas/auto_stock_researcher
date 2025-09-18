"""News fetcher utilities for stubbed and live NewsAPI headlines."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import logging
import os
import time
from typing import Any


LOGGER = logging.getLogger(__name__)
_SOURCES_PATH = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


def get_headlines(date_str: str) -> list[dict]:
    """Return a set of mock news headlines for the given date."""
    # Keep the mock data stable for tests yet vary timestamps using the date.
    timestamp = f"{date_str}T08:00:00Z"
    later_timestamp = f"{date_str}T14:00:00Z"

    return [
        {
            "title": "Apple's new AI features drive strong upgrade cycle",
            "url": "https://example.com/apple-upgrade-cycle",
            "source": "Reuters",
            "published_at": timestamp,
            "body": (
                "Apple is rolling out upgraded iPhone and Mac software with on-device"
                " generative AI, which analysts say could sustain record demand for"
                " Apple hardware this holiday season."
            ),
        },
        {
            "title": "Microsoft cloud growth beats expectations in latest quarter",
            "url": "https://example.com/microsoft-cloud-growth",
            "source": "Bloomberg",
            "published_at": later_timestamp,
            "body": (
                "Microsoft reported another quarter of Azure growth that beats Wall"
                " Street expectations as Windows and Teams adoption remains strong among"
                " enterprise clients."
            ),
        },
        {
            "title": "Nvidia GPUs power record data center demand",
            "url": "https://example.com/nvidia-data-center",
            "source": "Financial Times",
            "published_at": timestamp,
            "body": (
                "Cloud providers are racing to secure more Nvidia GPU supply to support"
                " artificial intelligence workloads, keeping Nvidia's data center"
                " revenue at record highs and sustaining strong growth guidance."
            ),
        },
        {
            "title": "Exxon Mobil faces new emissions disclosure lawsuit",
            "url": "https://example.com/exxon-lawsuit",
            "source": "Associated Press",
            "published_at": later_timestamp,
            "body": (
                "Environmental groups filed a lawsuit alleging ExxonMobil misled"
                " investors about long-term emissions impacts, adding legal pressure"
                " and the potential for negative headlines."
            ),
        },
    ]


@lru_cache(maxsize=1)
def _load_domains_allowlist() -> list[str] | None:
    """Return the optional NewsAPI domains allowlist from configuration."""

    try:
        import yaml
    except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
        LOGGER.debug("PyYAML not installed; skipping domains allowlist lookup")
        return None

    try:
        with _SOURCES_PATH.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError:
        return None
    except yaml.YAMLError as exc:  # pragma: no cover - defensive parsing guard
        LOGGER.debug("Failed to parse %s: %s", _SOURCES_PATH, exc)
        return None

    news_config = data.get("news") if isinstance(data, dict) else None
    if not isinstance(news_config, dict):
        return None

    allowlist = news_config.get("domains_allowlist")
    if isinstance(allowlist, list):
        cleaned = [str(domain).strip() for domain in allowlist if str(domain).strip()]
        return cleaned or None

    if isinstance(allowlist, str):
        domain = allowlist.strip()
        return [domain] if domain else None

    return None


def get_headlines_newsapi(date_str: str) -> list[dict]:
    """Fetch and normalise top headlines from the NewsAPI for a date."""

    try:
        import requests
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("The 'requests' package is required for NewsAPI support") from exc

    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise RuntimeError("NEWSAPI_KEY not set")

    url = "https://newsapi.org/v2/everything"
    params: dict[str, Any] = {
        "language": "en",
        "from": date_str,
        "to": date_str,
        "sortBy": "publishedAt",
        "pageSize": 50,
    }

    allowlist = _load_domains_allowlist()
    if allowlist:
        params["domains"] = ",".join(allowlist)

    headers = {"X-Api-Key": api_key}

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == requests.codes.too_many_requests:
                raise RuntimeError("NewsAPI rate limit exceeded")
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt >= 2:
                break
            time.sleep(1)
            continue
        else:
            articles = payload.get("articles", []) if isinstance(payload, dict) else []
            normalised: list[dict] = []
            for article in articles:
                if not isinstance(article, dict):
                    continue
                source_info = article.get("source") or {}
                source_name = ""
                if isinstance(source_info, dict):
                    source_name = source_info.get("name") or ""

                normalised.append(
                    {
                        "title": article.get("title") or "",
                        "url": article.get("url") or "",
                        "source": source_name,
                        "published_at": article.get("publishedAt") or "",
                        "body": article.get("content")
                        or article.get("description")
                        or "",
                    }
                )

            return normalised

    assert last_error is not None
    raise last_error


__all__ = ["get_headlines", "get_headlines_newsapi"]
