from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
import sqlite3

from app.api.schemas.news import RefreshResponse, LatestNewsResponse, ArticleOut
from app.core.database import get_db
from app.ingestion.scheduler import refresh_news_job
from app.services.article_service import ArticleService
from app.rag.vectordb import VectorDB
from app.rag.llm_answer import AegisAgenticSystem
from app.core.config import settings

router = APIRouter()


@router.post("/refresh", response_model=RefreshResponse)
def refresh_news():
    """Triggers raw news fetch and Silver/Vector promotion pipeline."""
    try:
        result = refresh_news_job()
        return RefreshResponse(
            status=result.get("status", "success"),
            fetched=result.get("fetched", 0),
            inserted=result.get("inserted", 0),
            duplicates=result.get("duplicates", 0),
        )
    except Exception as e:
        print(f"Refresh error: {e}")
        return RefreshResponse(
            status="error",
            fetched=0,
            inserted=0,
            duplicates=0,
        )


@router.get("/latest", response_model=LatestNewsResponse)
def latest_news(
    topic: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieves the latest articles stored in the Silver Layer."""
    articles = ArticleService.get_latest_articles(db, topic=topic, limit=limit)

    return LatestNewsResponse(
        topic=topic,
        count=len(articles),
        articles=[ArticleOut.model_validate(article) for article in articles],
    )


@router.post("/ask")
def ask_news(query: str = Body(..., embed=True)):
    """Executes the multi-agent consensus workflow from vector memory."""
    vector_engine = VectorDB()
    agent_system = AegisAgenticSystem()

    search_results = vector_engine.search_memory(query=query, n_results=8)
    ai_answer = agent_system.generate_consensus_report(query, search_results)

    return {
        "query": query,
        "answer": ai_answer,
        "verification_status": "Consensus Verified" if "No context found" not in ai_answer else "No Context",
        "medallion_tier": "Gold",
    }


@router.get("/risk-indices")
def get_gold_risk_data():
    """Fetches normalized data points for the Streamlit line chart."""
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                timestamp,
                LOWER(TRIM(topic)) AS topic,
                risk_score
            FROM gold_risk_index
            WHERE topic IS NOT NULL
              AND TRIM(topic) != ''
            ORDER BY timestamp ASC
        """)
        data = cursor.fetchall()

        return [
            {
                "time": row[0],
                "topic": row[1],
                "score": row[2],
            }
            for row in data
        ]
    except Exception as e:
        print(f"Gold risk fetch error: {e}")
        return []
    finally:
        conn.close()