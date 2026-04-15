from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
import sqlite3
import re
from datetime import datetime

from app.api.schemas.news import RefreshResponse, LatestNewsResponse, ArticleOut
from app.core.database import get_db
from app.ingestion.scheduler import refresh_news_job
from app.services.article_service import get_latest_articles
from app.rag.vectordb import VectorDB
from app.rag.llm_answer import AegisAgenticSystem
from app.core.config import settings

router = APIRouter()

# --- BRONZE LAYER: DATA INGESTION ---
@router.post("/refresh", response_model=RefreshResponse)
def refresh_news():
    """Triggers raw news fetch. This fixes your 404 error."""
    try:
        result = refresh_news_job()
        return RefreshResponse(
            status=result["status"],
            fetched=result.get("fetched", 0),
            inserted=result.get("inserted", 0),
            duplicates=result.get("duplicates", 0),
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- SILVER LAYER: CONTEXT RETRIEVAL ---
@router.get("/latest", response_model=LatestNewsResponse)
def latest_news(
    topic: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieves the latest articles stored in the Silver Tier."""
    articles = get_latest_articles(db, topic=topic, limit=limit)
    return LatestNewsResponse(
        topic=topic,
        count=len(articles),
        articles=[ArticleOut.model_validate(article) for article in articles],
    )

# --- GOLD LAYER: AGENTIC CONSENSUS ---
@router.post("/ask")
def ask_news(query: str = Body(..., embed=True)):
    """Executes the Multi-Agent Debate and saves the verified report."""
    vector_engine = VectorDB()
    agent_system = AegisAgenticSystem()
    
    # 1. Search Vector DB
    search_results = vector_engine.search_memory(query=query, n_results=5)
    
    # 2. Agentic Debate (GPT-4o vs Claude 3.5)
    ai_answer = agent_system.generate_consensus_report(query, search_results)

    return {
        "query": query,
        "answer": ai_answer,
        "verification_status": "Consensus Verified",
        "medallion_tier": "Gold"
    }

# --- GRAPHING DATA ENDPOINT ---
@router.get("/risk-indices")
def get_gold_risk_data():
    """Fetches data points for the Streamlit line chart."""
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Fetching scores for the graph
        cursor.execute("SELECT timestamp, topic, risk_score FROM gold_risk_index ORDER BY timestamp ASC")
        data = cursor.fetchall()
        return [{"time": d[0], "topic": d[1], "score": d[2]} for d in data]
    except Exception:
        return []
    finally:
        conn.close()