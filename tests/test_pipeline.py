from src.pipeline import run_daily_pipeline
def test_pipeline_writes_file(tmp_path, monkeypatch):
    # run for a fixed date and write into repo reports/ (ok for now)
    p = run_daily_pipeline("2025-01-01")
    assert "daily_2025-01-01.html" in p
