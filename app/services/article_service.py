from sqlalchemy.orm import Session
from app.models.article import Article
from app.rag.vectordb import add_article_to_vectordb


def save_articles(db: Session, articles):
    inserted = 0
    duplicates = 0

    for item in articles:
        existing = db.query(Article).filter(Article.url == item["url"]).first()
        if existing:
            duplicates += 1
            continue

        article = Article(
            title=item["title"],
            source=item["source"],
            url=item["url"],
            published_at=item["published_at"],
            summary=item.get("summary"),
            content=item.get("content"),
            risk_score=item.get("risk_score", 0),
        )

        db.add(article)
        inserted += 1

    db.commit()

    # Fetch recently inserted articles
    saved_articles = (
        db.query(Article)
        .order_by(Article.id.desc())
        .limit(inserted)
        .all()
    )

    # Store in vector DB
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