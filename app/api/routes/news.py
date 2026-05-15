from fastapi import APIRouter, Depends, Query, Body, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import re
import sqlite3
import time

from app.api.schemas.news import RefreshResponse, LatestNewsResponse, ArticleOut
from app.core.database import get_db
from app.evaluation import evaluate_risk_assessment
from app.ingestion.scheduler import refresh_news_job
from app.metrics import record_usage_event
from app.services.article_service import ArticleService
from app.rag.vectordb import VectorDB, VectorStoreError
from app.rag.llm_answer import AegisAgenticSystem
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _topic_label(query: str) -> str:
    clean_query = (query or "").strip().lower()
    if "suez" in clean_query:
        return "suez canal"
    if "hormuz" in clean_query:
        return "strait of hormuz"
    if "oil" in clean_query:
        return "oil transit"
    if "iran" in clean_query:
        return "iran transit"
    if "shipping" in clean_query:
        return "shipping transit"
    return "general risk"


def _count_section_items(text: str, section: str) -> int:
    pattern = rf"###\s*{re.escape(section)}\s*(.*?)(?:\n###\s+|\Z)"
    match = re.search(pattern, text or "", flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return 0
    section_text = match.group(1)
    return len(re.findall(r"^\s*[-*]\s+", section_text, flags=re.MULTILINE))


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
        logger.exception("Refresh error: %s", e)
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
    try:
        articles = ArticleService.get_latest_articles(db, topic=topic, limit=limit)
    except Exception as e:
        logger.exception("Latest news fetch failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Unable to load latest articles right now.",
            },
        ) from e

    return LatestNewsResponse(
        topic=topic,
        count=len(articles),
        articles=[ArticleOut.model_validate(article) for article in articles],
    )


@router.post("/ask")
def ask_news(query: str = Body(..., embed=True)):
    """Executes the multi-agent consensus workflow from vector memory."""
    started_at = time.perf_counter()
    if not query or not query.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Please provide a question to analyze.",
            },
        )

    try:
        vector_engine = VectorDB()
        agent_system = AegisAgenticSystem()
        search_results = vector_engine.search_memory(query=query, n_results=8)
        ai_answer = agent_system.generate_consensus_report(query, search_results)
    except VectorStoreError as e:
        logger.exception("Vector store error during ask flow: %s", e)
        record_usage_event({
            "status": "failed",
            "assistant_id": "risk_analyst",
            "focus_topic": _topic_label(query),
            "verification_state": "Error",
            "evaluation_status": "fail",
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
            "error_type": "vector_store_error",
        })
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Evidence search is temporarily unavailable.",
                "answer": "Evidence search is temporarily unavailable. Please try again shortly.",
                "verification_status": "Error",
                "medallion_tier": "Gold",
            },
        )
    except Exception as e:
        logger.exception("Ask flow failed: %s", e)
        record_usage_event({
            "status": "failed",
            "assistant_id": "risk_analyst",
            "focus_topic": _topic_label(query),
            "verification_state": "Error",
            "evaluation_status": "fail",
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
            "error_type": "ask_flow_error",
        })
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Unable to generate an answer right now.",
                "answer": "Unable to generate an answer right now. Please try again shortly.",
                "verification_status": "Error",
                "medallion_tier": "Gold",
            },
        )

    audit = getattr(agent_system, "last_audit", {})
    evaluation = evaluate_risk_assessment(
        final_output=ai_answer,
        retrieved_evidence=search_results,
        audit=audit,
    )
    verification_status = "Consensus Verified" if "No context found" not in ai_answer else "No Context"
    record_usage_event({
        "status": "success",
        "assistant_id": "risk_analyst",
        "focus_topic": _topic_label(query),
        "evidence_count": len(search_results),
        "final_risk_score": evaluation.get("metadata", {}).get("risk_score"),
        "verification_state": verification_status,
        "evaluation_status": evaluation.get("status"),
        "citation_count": evaluation.get("checks", {}).get("citation_count"),
        "uncertainty_note_count": _count_section_items(ai_answer, "Uncertainty Notes"),
        "human_review_point_count": _count_section_items(ai_answer, "Recommended Human Review Points"),
        "has_critic_warning": bool(audit.get("critic_warning")) if isinstance(audit, dict) else False,
        "has_revision_signal": bool(evaluation.get("checks", {}).get("has_revised_output")),
        "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
    })

    return {
        "status": "success",
        "query": query,
        "answer": ai_answer,
        "audit": audit,
        "evaluation": evaluation,
        "verification_status": verification_status,
        "medallion_tier": "Gold",
    }


@router.get("/risk-indices")
def get_gold_risk_data():
    """Fetches normalized data points for the Streamlit line chart."""
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
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
        logger.exception("Gold risk fetch error: %s", e)
        return []
    finally:
        if conn:
            conn.close()
