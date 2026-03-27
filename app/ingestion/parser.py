GEOPOLITICAL_KEYWORDS = [
    "israel",
    "iran",
    "red sea",
    "suez",
    "middle east",
    "gaza",
    "houthi",
    "strait of hormuz",
    "yemen",
]

SUPPLY_CHAIN_KEYWORDS = [
    "oil",
    "fuel",
    "shipping",
    "tanker",
    "freight",
    "cargo",
    "logistics",
    "supply chain",
    "diesel",
    "crude",
    "energy",
    "port",
    "trade disruption",
]


def is_relevant_article(article: dict) -> bool:
    title = article.get("title") or ""
    description = article.get("description") or ""
    content = article.get("content") or ""

    text = f"{title} {description} {content}".lower()

    geo_matches = sum(1 for keyword in GEOPOLITICAL_KEYWORDS if keyword in text)
    supply_matches = sum(1 for keyword in SUPPLY_CHAIN_KEYWORDS if keyword in text)

    return (geo_matches >= 1 and supply_matches >= 1) or (geo_matches + supply_matches >= 2)


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