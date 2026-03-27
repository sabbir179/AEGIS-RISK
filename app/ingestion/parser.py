import re

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

HIGH_RISK_KEYWORDS = [
    "war",
    "conflict",
    "attack",
    "crisis",
    "blockade",
    "missile",
    "strike",
    "military",
]

MEDIUM_RISK_KEYWORDS = [
    "disruption",
    "delay",
    "shortage",
    "sanction",
    "rerouting",
    "volatility",
    "threat",
    "uncertainty",
]


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compute_risk_score(text: str) -> int:
    text = text.lower()
    score = 0

    for word in HIGH_RISK_KEYWORDS:
        if word in text:
            score += 2

    for word in MEDIUM_RISK_KEYWORDS:
        if word in text:
            score += 1

    return min(score, 5)


def is_relevant_article(article: dict) -> bool:
    title = clean_text(article.get("title"))
    description = clean_text(article.get("description"))
    content = clean_text(article.get("content"))

    text = f"{title} {description} {content}".lower()

    geo_matches = sum(1 for keyword in GEOPOLITICAL_KEYWORDS if keyword in text)
    supply_matches = sum(1 for keyword in SUPPLY_CHAIN_KEYWORDS if keyword in text)

    return (geo_matches >= 1 and supply_matches >= 1) or (geo_matches + supply_matches >= 2)


def normalize_article(article: dict, topic: str | None = None) -> dict:
    title = clean_text(article.get("title")) or "Untitled"
    summary = clean_text(article.get("description"))
    content = clean_text(article.get("content"))
    combined_text = f"{title} {summary} {content}"

    return {
        "source": clean_text((article.get("source") or {}).get("name")),
        "title": title,
        "url": article.get("url") or "",
        "published_at": article.get("publishedAt"),
        "summary": summary,
        "content": content,
        "topic": topic,
        "risk_score": compute_risk_score(combined_text),
    }