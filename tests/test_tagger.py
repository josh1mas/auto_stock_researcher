from src.tagger import link_articles_to_tickers


def test_link_articles_to_tickers_matches_aliases():
    articles = [
        {
            "title": "Apple and Microsoft extend rally",
            "body": "Analysts say Apple and microsoft continue to post strong growth.",
        }
    ]

    tagged = link_articles_to_tickers(articles)
    assert tagged[0]["tickers"] == ["AAPL", "MSFT"]


def test_link_articles_to_tickers_avoids_substring_matches():
    articles = [
        {
            "title": "Pineapple growers report record harvest",
            "body": "Tropical fruit demand surges globally.",
        }
    ]

    tagged = link_articles_to_tickers(articles)
    assert tagged[0]["tickers"] == []
