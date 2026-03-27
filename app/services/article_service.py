import hashlib
from sqlalchemy.orm import Session
from app.models.article import Article
from app.rag.vectordb import add_article_to_vectordb


def generate_fingerprint(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def save_articles(db: Session, articles):
    inserted = 0
    duplicates = 0

    for item in articles:
        # 🚨 CRITICAL FIX: skip invalid URLs
        if not item.get("url"):
            print("Skipping article with missing URL:", item.get("title"))
            continue

        fingerprint = generate_fingerprint(item["url"])

        existing = db.query(Article).filter(Article.fingerprint == fingerprint).first()
        if existing:
            duplicates += 1
            continue

        article = Article(
            fingerprint=fingerprint,
            title=item.get("title", "Untitled"),
            source=item.get("source"),
            url=item.get("url"),
            published_at=item.get("published_at"),
            summary=item.get("summary"),
            content=item.get("content"),
            risk_score=item.get("risk_score", 0),
            topic=item.get("topic"),
        )

        db.add(article)
        inserted += 1

    db.commit()

    # Store in vector DB
    saved_articles = (
        db.query(Article)
        .order_by(Article.id.desc())
        .limit(inserted)
        .all()
    )

    for article in saved_articles:
        combined_text = f"{article.title} {article.summary or ''} {article.content or ''}"

        add_article_to_vectordb(
            article_id=str(article.id),
            text=combined_text,
            metadata={
                "title": article.title or "",
                "source": article.source or "",
                "published_at": article.published_at or "",
                "risk_score": article.risk_score or 0,
                "url": article.url or "",
            },
        )

    return {"inserted": inserted, "duplicates": duplicates}


def get_latest_articles(db: Session, topic: str | None = None, limit: int = 10):
    query = db.query(Article)

    if topic:
        query = query.filter(Article.title.ilike(f"%{topic}%"))

    return query.order_by(Article.published_at.desc()).limit(limit).all()