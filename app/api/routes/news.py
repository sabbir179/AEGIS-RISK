from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from app.api.schemas.news import RefreshResponse, LatestNewsResponse, ArticleOut
from app.core.database import get_db, SessionLocal
from app.ingestion.scheduler import refresh_news_job
from app.services.article_service import get_latest_articles
from app.models.article import Article
from app.rag.vectordb import search_articles
from app.rag.llm_answer import generate_ai_answer

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


@router.get("/summary")
def get_news_summary():
    db = SessionLocal()
    try:
        articles = db.query(Article).all()

        if not articles:
            return {
                "total": 0,
                "avg_risk": 0,
                "top_risks": [],
            }

        total = len(articles)
        avg_risk = sum((a.risk_score or 0) for a in articles) / total

        sorted_articles = sorted(
            articles,
            key=lambda x: x.risk_score or 0,
            reverse=True,
        )

        top = sorted_articles[:3]

        return {
            "total": total,
            "avg_risk": round(avg_risk, 2),
            "top_risks": [
                {
                    "title": a.title,
                    "risk_score": a.risk_score or 0,
                    "url": a.url,
                }
                for a in top
            ],
        }
    finally:
        db.close()


@router.post("/ask")
def ask_news(query: str = Body(..., embed=True)):
    results = search_articles(query=query, n_results=5)

    formatted = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    for doc_id, doc, meta in zip(ids, docs, metas):
        formatted.append(
            {
                "id": doc_id,
                "document": doc,
                "metadata": meta,
            }
        )

    ai_answer = generate_ai_answer(query, docs)

    return {
        "query": query,
        "answer": ai_answer,
        "results": formatted,
    }