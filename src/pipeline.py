from pathlib import Path
from datetime import datetime

def run_daily_pipeline(run_date: str | None = None) -> str:
    """Create a placeholder daily report and return its path."""
    date = datetime.strptime(run_date, "%Y-%m-%d") if run_date else datetime.utcnow()
    date_str = date.strftime("%Y-%m-%d")

    out_dir = Path("reports"); out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"daily_{date_str}.html"
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Daily Stock Ideas — {date_str}</title>
<style>body{{font-family:-apple-system,Segoe UI,Roboto,Arial;margin:24px}}</style>
</head><body><h1>Daily Stock Ideas — {date_str}</h1>
<p>Placeholder: next step is fetch → tag → score.</p></body></html>"""
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
