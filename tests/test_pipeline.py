from pathlib import Path

from src.pipeline import run_daily_pipeline


def _read_report(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_pipeline_writes_enriched_report(tmp_path):
    path = run_daily_pipeline("2025-01-01")
    assert "daily_2025-01-01.html" in path

    html = _read_report(path)
    assert "Top Ideas" in html
    assert "Articles Reviewed" in html
    assert "AAPL" in html  # Stubbed data should surface Apple as an idea


def test_pipeline_falls_back_to_stub(monkeypatch):
    monkeypatch.setattr("src.pipeline.USE_STUBS", False, raising=False)
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)

    path = run_daily_pipeline("2025-01-01")
    html = _read_report(path)

    assert "Data source: Stub" in html
    assert "AAPL" in html
