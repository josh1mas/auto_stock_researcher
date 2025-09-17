from pathlib import Path
from datetime import datetime

from src.fetchers.news_fetcher import get_headlines
from src.scoring import score_day
from src.tagger import link_articles_to_tickers


def _render_idea_block(idea: dict) -> str:
    bullets = idea.get("why") or []
    bullet_html = "".join(f"<li>{point}</li>" for point in bullets[:2])
    if not bullet_html:
        bullet_html = "<li>No additional context.</li>"

    links = idea.get("links") or []
    if links:
        link_html = " ".join(
            f'<a href="{href}" target="_blank" rel="noopener">Link {idx}</a>'
            for idx, href in enumerate(links, start=1)
        )
    else:
        link_html = "No links available."

    return (
        "<div class=\"idea\">"
        f"<h3>{idea['ticker']} — Score {idea['score']:.2f}</h3>"
        f"<ul>{bullet_html}</ul>"
        f"<p>Links: {link_html}</p>"
        "</div>"
    )


def run_daily_pipeline(run_date: str | None = None) -> str:
    """Fetch stubbed news, tag tickers, score ideas, and render an HTML report."""
    date = datetime.strptime(run_date, "%Y-%m-%d") if run_date else datetime.utcnow()
    date_str = date.strftime("%Y-%m-%d")

    articles = get_headlines(date_str)
    tagged_articles = link_articles_to_tickers(articles)
    ideas = score_day(tagged_articles)

    idea_section = (
        "".join(_render_idea_block(idea) for idea in ideas)
        if ideas
        else "<p>No ideas generated for this date.</p>"
    )

    article_list_items = "".join(
        f"<li><strong>{item['title']}</strong> — {', '.join(item['tickers']) or 'No tickers matched.'}</li>"
        for item in tagged_articles
    )

    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"daily_{date_str}.html"

    html = f"""<!doctype html><html><head><meta charset=\"utf-8\">
<title>Daily Stock Ideas — {date_str}</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,Arial;margin:24px;line-height:1.5}}
.idea{{border:1px solid #ddd;border-radius:8px;padding:12px;margin-bottom:16px}}
.idea h3{{margin-top:0}}
</style>
</head><body><h1>Daily Stock Ideas — {date_str}</h1>
<section><h2>Top Ideas</h2>{idea_section}</section>
<section><h2>Articles Reviewed</h2><ul>{article_list_items}</ul></section>
</body></html>"""

    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
