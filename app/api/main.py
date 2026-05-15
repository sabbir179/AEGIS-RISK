import sqlite3
from fastapi import FastAPI
from app.core.logging_config import configure_logging
from app.core.database import Base, engine
from app.api.routes.metrics import router as metrics_router
from app.api.routes.news import router as news_router
from app.ingestion.scheduler import start_scheduler
from app.core.config import settings
import logging

configure_logging()
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RiskLens AI API",
    version="1.0.0",
    description="Agentic Geopolitical Risk Monitoring System"
)


@app.on_event("startup")
def on_startup():
    try:
        db_path = settings.database_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gold_risk_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                topic TEXT,
                risk_score INTEGER,
                full_report TEXT,
                consensus_reached BOOLEAN
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Gold Risk Table verified/created.")
    except Exception as e:
        logger.exception("Error creating Gold table: %s", e)

    start_scheduler()


@app.get("/")
def root():
    return {
        "message": "RiskLens AI API is online",
        "docs": "/docs",
        "status": "ready"
    }


app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["metrics"])
