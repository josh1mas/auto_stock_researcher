from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import logging
import os
from html import escape
from urllib.parse import urlparse

from src.fetchers.news_fetcher import get_headlines, get_headlines_newsapi
from src.scoring import score_day
from src.tagger import link_articles_to_tickers

# --- Logging ---------------------------------------------------------------
LOGGER = logging.getLogger(__name__)
if not logging.getLogger().handlers:  # init once if not already set elsewhere
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# --- Config switches -------------------------------------------------------
# Flip with an environment variable instead of editing code:
#   USE_STUBS=0  -> try live NewsAPI (fallback to stub on error)
#   USE_STUBS=1  -> use stub headlines
USE_STUBS: bool = os.getenv("USE_STUBS", "1") != "0"

# Default timezone for "today" when no run_date provided
DEFAULT_TZ = ZoneInfo(os.getenv("REPORT_TZ", "America/New_York"))


def _resolve_date(run_date: str | None) -> datetime:
    """Parse YYYY-MM-DD or use 'today' in DEFAULT_TZ, return a naive date at 00:00 local."""
    if run_date:
        return datetime.strptime(run_date, "%Y-%m-%d")
    now_local = datetime.now(tz=DEFAULT_TZ)
    # normalize to date only (naive) so downstream string is stable
    return datetime(year=now_local.year, month=now_local.month, day=now_local.day)


def _age_str(iso: str) -> str:
    """Return a human readable age string like '2h ago'."""

    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        seconds = max(0, int(delta.total_seconds()))
        if seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m ago"
        if seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        days = seconds // 86400
        return f"{days}d ago"
    except Exception:
        return ""


def _render_idea_block(idea: dict) -> str:
    bullets = (idea.get("why") or [])[:2]
    bullet_html = "".join(f"<li>{escape(str(point))}</li>" for point in bullets) or "<li>No additional context.</li>"

    links = idea.get("links") or []
    rendered_links: list[str] = []
    for link in links:
        if isinstance(link, dict):
            href = link.get("url")
            published_at = link.get("published_at", "")
        else:
            href = link
            published_at = ""
        if not href:
            continue
        domain = urlparse(str(href)).netloc or "link"
        age = _age_str(str(published_at))
        label = f"{domain} ({age})" if age else domain
        rendered_links.append(
            f'<a href="{escape(str(href))}" target="_blank" rel="noopener">{escape(label)}</a>'
        )

    link_html = " ".join(rendered_links) if rendered_links else "No links available."

    ticker = escape(str(idea.get("ticker", "UNK")))
    score = float(idea.get("score", 0.0))
    return (
        '<div class="idea">'
        f"<h3>{ticker} — Score {score:.2f}</h3>"
        f"<ul>{bullet_html}</ul>"
        f"<p>Links: {link_html}</p>"
        "</div>"
    )


def run_daily_pipeline(run_date: str | None = None) -> str:
    """Generate the daily report using either stubbed or live data sources."""
    date = _resolve_date(run_date)
    date_str = date.strftime("%Y-%m-%d")

    # 1) Fetch headlines (live if allowed, else stub; live falls back to stub on error)
    data_source = "Stub"
    if USE_STUBS:
        articles = get_headlines(date_str)
    else:
        try:
            articles = get_headlines_newsapi(date_str)
            data_source = "Live"
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Falling back to stub headlines: %s", exc)
            articles = get_headlines(date_str)
            data_source = "Stub"

    # 2) Tag to tickers (robust to empty)
    tagged_articles = link_articles_to_tickers(articles or [])

    # 3) Score ideas (robust to empty)
    ideas = score_day(tagged_articles or [])
    ideas = sorted(ideas, key=lambda x: x["score"], reverse=True)[:10]

    # 4) Render sections
    idea_section = (
        "".join(_render_idea_block(idea) for idea in ideas) if ideas else "<p>No ideas generated for this date.</p>"
    )

    article_list_items = "".join(
        f"<li><strong>{escape(item.get('title',''))}</strong> — "
        f"{', '.join(item.get('tickers', [])) or 'No tickers matched.'}</li>"
        for item in (tagged_articles or [])
    ) or "<li>No articles available.</li>"

    # Small header summary
    unique_tickers = sorted({t for it in (tagged_articles or []) for t in it.get("tickers", [])})
    summary_html = (
        f"<p><em>Data source: {data_source}</em> · "
        f"Articles scanned: {len(tagged_articles or [])} · "
        f"Tickers surfaced: {len(unique_tickers)}</p>"
    )

    # 5) Write HTML
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"daily_{date_str}.html"

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Daily Stock Ideas — {date_str}</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,Arial;margin:24px;line-height:1.5}}
.idea{{border:1px solid #ddd;border-radius:8px;padding:12px;margin-bottom:16px}}
.idea h3{{margin-top:0}}
summary{{cursor:pointer}}
</style>
</head><body>
<h1>Daily Stock Ideas — {date_str}</h1>
{summary_html}
<section><h2>Top Ideas</h2>{idea_section}</section>
<section><h2>Articles Reviewed</h2><ul>{article_list_items}</ul></section>
</body></html>"""

    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
