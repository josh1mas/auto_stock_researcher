from src.scoring import score_day


def _idea_for(ideas, ticker):
    for idea in ideas:
        if idea["ticker"] == ticker:
            return idea
    raise AssertionError(f"Ticker {ticker} not found")


def test_dedupe_prefers_highest_quality_on_title_match():
    tagged = [
        {
            "source": "Reuters",
            "title": "MEGA beats expectations — update",
            "url": "https://example.com/reuters",
            "published_at": "2025-09-17T08:00:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Business Wire",
            "title": "MEGA beats expectations — update",
            "url": "https://example.com/businesswire",
            "published_at": "2025-09-17T07:00:00Z",
            "tickers": ["MEGA"],
        },
    ]

    ideas = score_day(tagged)
    mega = _idea_for(ideas, "MEGA")
    urls = [entry["url"] for entry in mega["links"]]
    assert urls == ["https://example.com/reuters"]
    assert mega["links"][0]["published_at"] == "2025-09-17T08:00:00Z"


def test_dedupe_collapses_duplicate_urls():
    tagged = [
        {
            "source": "Reuters",
            "title": "MEGA wins contract",
            "url": "https://example.com/shared",
            "published_at": "2025-09-17T08:00:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Bloomberg",
            "title": "MEGA beats rivals",
            "url": "https://example.com/shared",
            "published_at": "2025-09-17T09:00:00Z",
            "tickers": ["MEGA"],
        },
    ]

    ideas = score_day(tagged)
    mega = _idea_for(ideas, "MEGA")
    urls = [entry["url"] for entry in mega["links"]]
    assert urls == ["https://example.com/shared"]
    assert mega["links"][0]["published_at"] == "2025-09-17T08:00:00Z"
