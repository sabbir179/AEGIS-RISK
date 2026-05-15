from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.main import app
from app.rag.vectordb import VectorStoreError


client = TestClient(app)


def test_root_endpoint_happy_path():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_refresh_endpoint_returns_scheduler_result(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.news.refresh_news_job",
        lambda: {"status": "success", "fetched": 3, "inserted": 2, "duplicates": 1},
    )

    response = client.post("/api/news/refresh")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "fetched": 3,
        "inserted": 2,
        "duplicates": 1,
    }


def test_latest_endpoint_returns_articles(monkeypatch):
    article = SimpleNamespace(
        id=1,
        source="Source A",
        title="Oil transit risk",
        url="https://example.com/a",
        published_at="2026-05-15",
        summary="Summary",
        topic="oil",
        risk_score=3,
    )
    monkeypatch.setattr(
        "app.api.routes.news.ArticleService.get_latest_articles",
        lambda db, topic=None, limit=20: [article],
    )

    response = client.get("/api/news/latest?topic=oil&limit=1")

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_latest_endpoint_returns_structured_error(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.api.routes.news.ArticleService.get_latest_articles", fail)

    response = client.get("/api/news/latest?topic=oil&limit=1")

    assert response.status_code == 500
    assert response.json()["detail"]["message"] == "Unable to load latest articles right now."


def test_ask_endpoint_rejects_blank_query():
    response = client.post("/api/news/ask", json={"query": ""})

    assert response.status_code == 400
    assert response.json()["message"] == "Please provide a question to analyze."


def test_ask_endpoint_happy_path(monkeypatch):
    class FakeVectorDB:
        def search_memory(self, query, n_results):
            return [{"title": "Oil risk", "content": "Context"}]

    class FakeAgent:
        def generate_consensus_report(self, query, search_results):
            return "Consensus answer"

    monkeypatch.setattr("app.api.routes.news.VectorDB", lambda: FakeVectorDB())
    monkeypatch.setattr("app.api.routes.news.AegisAgenticSystem", lambda: FakeAgent())

    response = client.post("/api/news/ask", json={"query": "Assess oil risk"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["verification_status"] == "Consensus Verified"


def test_ask_endpoint_handles_vector_store_failure(monkeypatch):
    class FailingVectorDB:
        def search_memory(self, query, n_results):
            raise VectorStoreError("down")

    monkeypatch.setattr("app.api.routes.news.VectorDB", lambda: FailingVectorDB())

    response = client.post("/api/news/ask", json={"query": "Assess oil risk"})

    assert response.status_code == 503
    assert response.json()["message"] == "Evidence search is temporarily unavailable."
