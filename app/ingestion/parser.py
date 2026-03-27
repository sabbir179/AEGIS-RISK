GEOPOLITICAL_KEYWORDS = [
    "israel",
    "iran",
    "red sea",
    "suez",
    "middle east",
    "gaza",
    "houthi",
    "strait of hormuz",
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

    has_geo = any(keyword in text for keyword in GEOPOLITICAL_KEYWORDS)
    has_supply = any(keyword in text for keyword in SUPPLY_CHAIN_KEYWORDS)

    return has_geo and has_supply


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