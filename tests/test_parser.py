from app.ingestion.parser import (
    clean_text,
    compute_risk_score,
    is_relevant_article,
    normalize_article,
)


def test_clean_text_removes_html_noise_and_newsapi_truncation():
    raw = "<p>Iran oil tanker disruption</p> [+123 chars] --- more\ntext"

    assert clean_text(raw) == "Iran oil tanker disruption more text"


def test_normalize_article_builds_structured_payload_and_score():
    article = {
        "source": {"name": "Test Source"},
        "title": "Iran oil tanker attack raises Red Sea shipping risk",
        "url": "https://example.com/a",
        "publishedAt": "2026-05-15T10:00:00Z",
        "description": "Iran oil tanker attack creates disruption for shipping routes.",
        "content": "A naval attack and blockade risk created rerouting pressure for tankers.",
    }

    normalized = normalize_article(article, topic="middle-east-risk")

    assert normalized["source"] == "Test Source"
    assert normalized["title"] == article["title"]
    assert normalized["topic"] == "middle-east-risk"
    assert len(normalized["fingerprint"]) == 64
    assert normalized["risk_score"] == 5


def test_relevance_filter_accepts_geo_supply_chain_overlap():
    article = {
        "title": "Iran oil transit disruption affects shipping",
        "description": "Tanker movement through maritime routes faces new risk.",
        "content": "Energy and shipping operators are monitoring the Red Sea.",
    }

    assert is_relevant_article(article) is True


def test_relevance_filter_rejects_malformed_payload():
    assert is_relevant_article(None) is False


def test_compute_risk_score_caps_at_five():
    text = "war attack blockade missile crisis disruption delay uncertainty"

    assert compute_risk_score(text) == 5
