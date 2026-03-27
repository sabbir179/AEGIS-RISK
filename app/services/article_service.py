from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.article import Article
from app.ingestion.dedupe import article_fingerprint


def save_articles(db: Session, normalized_articles: list[dict]) -> dict:
    inserted = 0
    duplicates = 0

    for item in normalized_articles:
        fingerprint = article_fingerprint(item["title"], item["url"])
        existing = db.query(Article).filter(Article.fingerprint == fingerprint).first()

        if existing:
            duplicates += 1
            continue

        article = Article(
            fingerprint=fingerprint,
            source=item.get("source"),
            title=item.get("title"),
            url=item.get("url"),
            published_at=item.get("published_at"),
            summary=item.get("summary"),
            content=item.get("content"),
            topic=item.get("topic"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(article)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "duplicates": duplicates}


def get_latest_articles(db: Session, topic: str | None = None, limit: int = 10) -> list[Article]:
    query = db.query(Article)

    if topic:
        query = query.filter(Article.title.ilike(f"%{topic}%"))

    return query.order_by(desc(Article.id)).limit(limit).all()
