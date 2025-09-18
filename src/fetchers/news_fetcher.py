"""News fetcher utilities for stubbed and live NewsAPI headlines."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import csv
import logging
import os
import time
from typing import Any

LOGGER = logging.getLogger(__name__)
_SOURCES_PATH = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"
_UNIVERSE_PATH = Path(__file__).resolve().parents[2] / "config" / "universe.csv"

# ---------- STUB DATA ----------

def get_headlines(date_str: str) -> list[dict]:
    """Return a set of mock news headlines for the given date."""
    timestamp = f"{date_str}T08:00:00Z"
    later_timestamp = f"{date_str}T14:00:00Z"

    return [
        {
            "title": "Apple's new AI features drive strong upgrade cycle",
            "url": "https://example.com/apple-upgrade-cycle",
            "source": "Reuters",
            "published_at": timestamp,
            "body": "Apple is rolling out upgraded iPhone and Mac software with on-device AI.",
        },
        {
            "title": "Microsoft cloud growth beats expectations",
            "url": "https://example.com/microsoft-cloud-growth",
            "source": "Bloomberg",
            "published_at": later_timestamp,
            "body": "Microsoft reported another quarter of Azure growth that beat expectations.",
        },
        {
            "title": "Nvidia GPUs power record data center demand",
            "url": "https://example.com/nvidia-data-center",
            "source": "Financial Times",
            "published_at": timestamp,
            "body": "Cloud providers are racing to secure more Nvidia GPUs for AI workloads.",
        },
        {
            "title": "Exxon Mobil faces new emissions disclosure lawsuit",
            "url": "https://example.com/exxon-lawsuit",
            "source": "Associated Press",
            "published_at": later_timestamp,
            "body": "Environmental groups filed a lawsuit against ExxonMobil over emissions.",
        },
    ]


# ---------- CONFIG HELPERS ----------

@lru_cache(maxsize=1)
def _load_domains_allowlist() -> list[str] | None:
    """Return the optional NewsAPI domains allowlist from config/sources.yaml."""
    try:
        import yaml
    except ModuleNotFoundError:
        return None

    try:
        with _SOURCES_PATH.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return None
    except Exception as exc:
        LOGGER.debug("Failed to parse sources.yaml: %s", exc)
        return None

    news_cfg = data.get("news") if isinstance(data, dict) else None
    if not isinstance(news_cfg, dict):
        return None

    allowlist = news_cfg.get("domains_allowlist")
    if isinstance(allowlist, list):
        return [str(d).strip() for d in allowlist if str(d).strip()]
    if isinstance(allowlist, str):
        return [allowlist.strip()]
    return None


def _default_query_from_universe(max_terms: int = 12) -> str:
    """Build a NewsAPI query like 'AAPL OR MSFT ...' from universe.csv, fallback to generic."""
    try:
        terms: list[str] = []
        with _UNIVERSE_PATH.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                t = (row.get("ticker") or "").strip()
                if t:
                    terms.append(t)
                if len(terms) >= max_terms:
                    break
        if terms:
            return " OR ".join(terms)
    except Exception:
        pass
    return "stocks OR earnings OR merger OR acquisition OR guidance"


# ---------- LIVE FETCH (NewsAPI) ----------

def get_headlines_newsapi(date_str: str) -> list[dict]:
    """Fetch and normalise headlines from NewsAPI for a specific date."""
    try:
        import requests
    except ModuleNotFoundError as exc:
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
        "q": _default_query_from_universe(),  # Always include a query
        "apiKey": api_key,                    # Pass API key in query params
    }

    allowlist = _load_domains_allowlist()
    if allowlist:
        params["domains"] = ",".join(allowlist)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == requests.codes.too_many_requests:
                raise RuntimeError("NewsAPI rate limit exceeded")

            try:
                response.raise_for_status()
            except Exception as exc:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text[:300]
                raise RuntimeError(f"NewsAPI error {response.status_code}: {detail}") from exc

            payload = response.json()
            articles = payload.get("articles", []) if isinstance(payload, dict) else []
            normalised: list[dict] = []
            for art in articles:
                if not isinstance(art, dict):
                    continue
                source_info = art.get("source") or {}
                source_name = source_info.get("name") if isinstance(source_info, dict) else ""
                normalised.append(
                    {
                        "title": art.get("title") or "",
                        "url": art.get("url") or "",
                        "source": source_name or "",
                        "published_at": art.get("publishedAt") or "",
                        "body": art.get("content") or art.get("description") or "",
                    }
                )
            return normalised
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1)
                continue
            break

    assert last_error is not None
    raise last_error


__all__ = ["get_headlines", "get_headlines_newsapi"]