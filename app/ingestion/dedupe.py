import hashlib


def article_fingerprint(title: str, url: str) -> str:
    clean_title = (title or "").strip().lower()
    clean_url = (url or "").strip().lower()
    raw = f"{clean_title}|{clean_url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
