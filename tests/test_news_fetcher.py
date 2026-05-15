from types import SimpleNamespace

from app.ingestion.news_fetcher import NewsFetcher


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_fetch_newsapi_returns_cleaned_articles_without_network(monkeypatch):
    fetcher = NewsFetcher()
    payload = {
        "status": "ok",
        "totalResults": 1,
        "articles": [
            {
                "source": {"name": "NewsAPI"},
                "title": "Iran oil tanker attack raises shipping risk",
                "url": "https://example.com/a",
                "publishedAt": "2026-05-15T10:00:00Z",
                "description": "Iran oil tanker attack disrupts Red Sea shipping routes.",
                "content": "Iran oil tanker attack disrupts Red Sea shipping routes and energy transit.",
            }
        ],
    }

    monkeypatch.setattr(
        "app.ingestion.news_fetcher.requests.get",
        lambda *args, **kwargs: FakeResponse(payload=payload),
    )

    articles = fetcher.fetch_newsapi("oil", page_size=1)

    assert len(articles) == 1
    assert articles[0]["title"].startswith("Iran oil tanker")


def test_fetch_newsapi_handles_malformed_json(monkeypatch):
    fetcher = NewsFetcher()
    monkeypatch.setattr(
        "app.ingestion.news_fetcher.requests.get",
        lambda *args, **kwargs: FakeResponse(payload=ValueError("bad json")),
    )

    assert fetcher.fetch_newsapi("oil", page_size=1) == []


def test_parse_rss_handles_non_200_response(monkeypatch):
    fetcher = NewsFetcher()
    monkeypatch.setattr(
        "app.ingestion.news_fetcher.requests.get",
        lambda *args, **kwargs: FakeResponse(status_code=503, text="unavailable"),
    )

    assert fetcher._parse_rss_via_requests("https://example.com/rss", "Example RSS") == []


def test_parse_rss_handles_feed_entries(monkeypatch):
    fetcher = NewsFetcher()
    monkeypatch.setattr(
        "app.ingestion.news_fetcher.requests.get",
        lambda *args, **kwargs: FakeResponse(text="<rss></rss>"),
    )
    monkeypatch.setattr(
        "app.ingestion.news_fetcher.feedparser.parse",
        lambda text: SimpleNamespace(
            bozo=0,
            entries=[
                {
                    "title": "Iran oil tanker attack raises Red Sea shipping risk",
                    "link": "https://example.com/a",
                    "summary": "Iran oil tanker attack disrupts Red Sea shipping and energy transit.",
                    "published": "2026-05-15",
                }
            ],
        ),
    )

    articles = fetcher._parse_rss_via_requests("https://example.com/rss", "Example RSS")

    assert len(articles) == 1
    assert articles[0]["source"]["name"] == "Example RSS"
