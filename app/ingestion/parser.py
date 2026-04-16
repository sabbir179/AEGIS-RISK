import re
import hashlib
from datetime import datetime


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
    "hormuz",
    "persian gulf",
    "lebanon",
    "tehran",
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
    "exports",
    "imports",
    "maritime",
    "transit",
    "vessel",
    "supertanker",
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
    "seizure",
    "sanction",
    "naval",
]

MEDIUM_RISK_KEYWORDS = [
    "disruption",
    "delay",
    "shortage",
    "rerouting",
    "volatility",
    "threat",
    "uncertainty",
    "pressure",
    "risk",
    "tension",
]


def clean_text(text: str | None) -> str:
    """
    Clean HTML, whitespace, obvious placeholder markers, and low-value boilerplate.
    """
    if not text:
        return ""

    text = str(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove common NewsAPI truncation marker: [+123 chars]
    text = re.sub(r"\[\+\d+\s*chars\]", " ", text)

    # Remove obvious repeated filler separators
    text = re.sub(r"\s*\.\.\.\s*", " ", text)
    text = re.sub(r"\s*---\s*", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def looks_like_placeholder(text: str) -> bool:
    """
    Detect weak content that should not be treated as strong evidence.
    """
    if not text:
        return True

    lowered = text.lower().strip()

    placeholder_patterns = [
        "read more",
        "click here",
        "subscribe",
        "sign up",
        "watch live",
        "breaking news",
        "follow us",
        "full story",
        "continue reading",
    ]

    if lowered in {"n/a", "none", "null", "untitled"}:
        return True

    if len(lowered) < 20:
        return True

    if any(p in lowered for p in placeholder_patterns):
        return True

    # Single repeated token or too little diversity
    words = re.findall(r"\b\w+\b", lowered)
    if len(words) <= 3:
        return True

    unique_ratio = len(set(words)) / max(len(words), 1)
    if len(words) > 8 and unique_ratio < 0.35:
        return True

    return False


def truncate_text(text: str, max_len: int = 1200) -> str:
    """
    Keep text useful but not too long for vector storage / prompts.
    """
    if not text:
        return ""

    text = text.strip()
    if len(text) <= max_len:
        return text

    truncated = text[:max_len]
    last_period = truncated.rfind(".")
    if last_period > max_len * 0.6:
        return truncated[: last_period + 1].strip()

    return truncated.strip()


def build_best_summary(title: str, description: str, content: str) -> str:
    """
    Prefer a real description; otherwise derive a summary from content.
    """
    if description and not looks_like_placeholder(description):
        return truncate_text(description, 400)

    if content and not looks_like_placeholder(content):
        return truncate_text(content, 400)

    return truncate_text(title, 200)


def build_best_content(title: str, description: str, content: str) -> str:
    """
    Build the strongest possible content block from available fields.
    """
    content = clean_text(content)
    description = clean_text(description)
    title = clean_text(title)

    if content and not looks_like_placeholder(content):
        return truncate_text(content, 1500)

    if description and not looks_like_placeholder(description):
        return truncate_text(f"{description}", 1000)

    return truncate_text(title, 300)


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
    """
    Smarter relevance filter:
    - accepts geopolitical + supply chain overlap
    - accepts strong oil/logistics disruption articles
    - avoids very weak placeholder content as the only evidence
    """
    title = clean_text(article.get("title"))
    description = clean_text(article.get("description") or article.get("summary"))
    content = clean_text(article.get("content"))

    text = f"{title} {description} {content}".lower()

    geo_matches = sum(1 for keyword in GEOPOLITICAL_KEYWORDS if keyword in text)
    supply_matches = sum(1 for keyword in SUPPLY_CHAIN_KEYWORDS if keyword in text)
    high_risk_matches = sum(1 for keyword in HIGH_RISK_KEYWORDS if keyword in text)
    medium_risk_matches = sum(1 for keyword in MEDIUM_RISK_KEYWORDS if keyword in text)

    usable_text_present = any(
        not looks_like_placeholder(part)
        for part in [title, description, content]
    )

    if not usable_text_present:
        return False

    # Strongest signal: geopolitical + supply chain overlap
    if geo_matches >= 1 and supply_matches >= 1:
        return True

    # Strong logistics / energy disruption signal
    if supply_matches >= 2 and (high_risk_matches >= 1 or medium_risk_matches >= 1):
        return True

    # Strong geopolitical conflict signal
    if geo_matches >= 2 and (high_risk_matches >= 1 or medium_risk_matches >= 1):
        return True

    # Narrow but useful fallback
    if geo_matches >= 1 and high_risk_matches >= 2:
        return True

    return False


def extract_source_name(article: dict) -> str:
    source = article.get("source")

    if isinstance(source, dict):
        return clean_text(source.get("name")) or "Unknown"

    if isinstance(source, str):
        return clean_text(source) or "Unknown"

    return "Unknown"


def build_fingerprint(source: str, title: str, url: str) -> str:
    raw = f"{source}|{title}|{url}".strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_published_at(article: dict) -> str:
    published_at = article.get("publishedAt") or article.get("published_at")

    if published_at:
        return str(published_at)

    return datetime.utcnow().isoformat()


def normalize_article(article: dict, topic: str | None = None) -> dict:
    title = clean_text(article.get("title")) or "Untitled"

    raw_description = clean_text(article.get("description") or article.get("summary"))
    raw_content = clean_text(article.get("content"))
    url = clean_text(article.get("url")) or ""
    source_name = extract_source_name(article)
    published_at = normalize_published_at(article)

    summary = build_best_summary(title, raw_description, raw_content)
    content = build_best_content(title, raw_description, raw_content)

    combined_text = f"{title} {summary} {content}"
    fingerprint = build_fingerprint(source_name, title, url)

    return {
        "fingerprint": fingerprint,
        "source": source_name,
        "title": title,
        "url": url,
        "published_at": published_at,
        "summary": summary,
        "content": content,
        "topic": topic,
        "risk_score": compute_risk_score(combined_text),
    }