from src.scoring import score_day


def _idea_for(ideas, ticker):
    for idea in ideas:
        if idea["ticker"] == ticker:
            return idea
    raise AssertionError(f"Ticker {ticker} not found in ideas: {ideas}")


def test_score_day_filters_and_sorts_articles():
    tagged = [
        {
            "source": "Reuters",
            "title": "MEGA beats expectations — update",
            "url": "https://www.reuters.com/a",
            "published_at": "2025-09-17T12:00:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Business Wire",
            "title": "MEGA beats expectations — update",
            "url": "https://www.businesswire.com/a",
            "published_at": "2025-09-17T11:00:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Bloomberg",
            "title": "MEGA to raise guidance",
            "url": "https://www.bloomberg.com/b",
            "published_at": "2025-09-17T10:00:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "CNBC",
            "title": "MEGA strong profit growth",
            "url": "https://www.cnbc.com/c",
            "published_at": "2025-09-17T09:30:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Biztoc.com",
            "title": "MEGA hype blog",
            "url": "https://www.biztoc.com/d",
            "published_at": "2025-09-17T09:00:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Reuters",
            "title": "MEGA lawsuit risk",
            "url": "https://www.reuters.com/e",
            "published_at": "2025-09-17T08:30:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "AP News",
            "title": "MEGA upgrade and win",
            "url": "https://apnews.com/f",
            "published_at": "2025-09-17T07:30:00Z",
            "tickers": ["MEGA"],
        },
        {
            "source": "Financial Times",
            "title": "MEGA growth surge",
            "url": "https://www.ft.com/g",
            "published_at": "2025-09-17T06:30:00Z",
            "tickers": ["MEGA"],
        },
    ]

    ideas = score_day(tagged)
    mega = _idea_for(ideas, "MEGA")

    assert 0 <= mega["score"] <= 1
    assert mega["score"] > 0.6  # boosted by premium sources + positive keywords
    assert len(mega["why"]) <= 3
    assert "qInTitle match" in mega["why"]
    assert mega["why"][0].startswith("6 high-quality sources")

    links = mega["links"]
    assert len(links) == 5
    urls = [entry["url"] for entry in links]
    assert urls == [
        "https://www.reuters.com/a",
        "https://www.reuters.com/e",
        "https://www.bloomberg.com/b",
        "https://www.ft.com/g",
        "https://apnews.com/f",
    ]
    assert all("biztoc" not in url for url in urls)
    assert all("businesswire" not in url for url in urls)
    assert links[0]["published_at"] == "2025-09-17T12:00:00Z"
