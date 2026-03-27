from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.schemas.news import RefreshResponse, LatestNewsResponse, ArticleOut
from app.core.database import get_db
from app.ingestion.scheduler import refresh_news_job
from app.services.article_service import get_latest_articles

router = APIRouter()


@router.post("/refresh", response_model=RefreshResponse)
def refresh_news():
    result = refresh_news_job()
    return RefreshResponse(
        status=result["status"],
        fetched=result["fetched"],
        inserted=result["inserted"],
        duplicates=result["duplicates"],
    )


@router.get("/latest", response_model=LatestNewsResponse)
def latest_news(
    topic: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    articles = get_latest_articles(db, topic=topic, limit=limit)
    return LatestNewsResponse(
        topic=topic,
        count=len(articles),
        articles=[ArticleOut.model_validate(article) for article in articles],
    )
