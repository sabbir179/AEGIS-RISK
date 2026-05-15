from app.ingestion.dedupe import article_fingerprint


def test_article_fingerprint_is_case_and_whitespace_insensitive():
    first = article_fingerprint("  Iran Oil Transit  ", " HTTPS://EXAMPLE.COM/A ")
    second = article_fingerprint("iran oil transit", "https://example.com/a")

    assert first == second


def test_article_fingerprint_changes_when_url_changes():
    first = article_fingerprint("Iran Oil Transit", "https://example.com/a")
    second = article_fingerprint("Iran Oil Transit", "https://example.com/b")

    assert first != second
