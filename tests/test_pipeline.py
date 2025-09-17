from pathlib import Path

from src.pipeline import run_daily_pipeline


def test_pipeline_writes_enriched_report(tmp_path):
    path = run_daily_pipeline("2025-01-01")
    assert "daily_2025-01-01.html" in path

    html = Path(path).read_text(encoding="utf-8")
    assert "Top Ideas" in html
    assert "Articles Reviewed" in html
    assert "AAPL" in html  # Stubbed data should surface Apple as an idea
