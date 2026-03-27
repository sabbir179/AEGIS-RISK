def normalize_article(article: dict, topic: str | None = None) -> dict:
    return {
        "source": (article.get("source") or {}).get("name"),
        "title": article.get("title") or "Untitled",
        "url": article.get("url") or "",
        "published_at": article.get("publishedAt"),
        "summary": article.get("description"),
        "content": article.get("content"),
        "topic": topic,
    }
