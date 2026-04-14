from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.api.schemas.news import RefreshResponse, LatestNewsResponse, ArticleOut
from app.core.database import get_db, SessionLocal
from app.ingestion.scheduler import refresh_news_job
from app.rag.vectordb import VectorDB
from app.rag.llm_answer import AegisAgenticSystem

router = APIRouter()
vector_engine = VectorDB()
agent_system = AegisAgenticSystem()

@router.post("/ask")
def ask_news(query: str = Body(..., embed=True)):
    """
    IEEE Paper Workflow: Semantic Retrieval -> Multi-Agent Consensus -> Gold Storage.
    """
    # 1. Retrieve context from SILVER LAYER (ChromaDB)
    # Using the 'search_memory' logic we built in vectordb.py
    search_results = vector_engine.search_memory(query=query, n_results=5)
    
    # 2. Generate Verified Answer via GOLD LAYER (Agentic Consensus)
    # This triggers the OpenAI Analyst + Anthropic Critic debate
    ai_answer = agent_system.generate_consensus_report(query, [search_results])

    return {
        "query": query,
        "answer": ai_answer,
        "verification_status": "Consensus Verified",
        "medallion_tier": "Gold"
    }

@router.get("/risk-indices")
def get_gold_risk_data():
    """
    Tool for your IEEE Paper: Returns the structured data for graphing.
    """
    import sqlite3
    from app.core.config import settings
    db_path = settings.database_url.replace("sqlite:///", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, topic, risk_score FROM gold_risk_index ORDER BY timestamp DESC LIMIT 20")
    data = cursor.fetchall()
    conn.close()
    
    return [{"time": d[0], "topic": d[1], "score": d[2]} for d in data]