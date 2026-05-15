from datetime import datetime, timedelta

import pytest

from app.rag.vectordb import VectorDB, VectorStoreError


class FakeCollection:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def query(self, **kwargs):
        if self.error:
            raise self.error
        return self.result


def make_vector_db(collection):
    db = VectorDB.__new__(VectorDB)
    db.collection = collection
    return db


def test_recency_score_decays_with_article_age():
    db = VectorDB.__new__(VectorDB)
    recent = (datetime.now() - timedelta(hours=6)).isoformat()
    stale = (datetime.now() - timedelta(days=7)).isoformat()

    assert db._recency_score(recent) == 2.0
    assert db._recency_score(stale) == 0.0


def test_search_memory_formats_ranks_and_dedupes_results():
    result = {
        "documents": [["oil tanker content", "duplicate tanker content", "suez content"]],
        "metadatas": [[
            {
                "source": "Source A",
                "title": "Oil tanker risk",
                "url": "https://example.com/a",
                "published_at": datetime.now().isoformat(),
                "topic": "oil transit",
            },
            {
                "source": "Source A",
                "title": "Oil tanker risk duplicate",
                "url": "https://example.com/a",
                "published_at": datetime.now().isoformat(),
                "topic": "oil transit",
            },
            {
                "source": "Source B",
                "title": "Suez route update",
                "url": "https://example.com/b",
                "published_at": datetime.now().isoformat(),
                "topic": "suez canal",
            },
        ]],
        "ids": [["a", "a-dup", "b"]],
        "distances": [[0.1, 0.2, 0.3]],
    }
    db = make_vector_db(FakeCollection(result=result))

    rows = db.search_memory("oil tanker", n_results=5)

    assert len(rows) == 2
    assert rows[0]["title"] == "Oil tanker risk"
    assert "_rank_score" not in rows[0]


def test_search_memory_returns_empty_for_blank_query():
    db = make_vector_db(FakeCollection(result={}))

    assert db.search_memory("   ") == []


def test_search_memory_raises_vector_store_error_on_query_failure():
    db = make_vector_db(FakeCollection(error=RuntimeError("chroma down")))

    with pytest.raises(VectorStoreError):
        db.search_memory("oil", n_results=5)
