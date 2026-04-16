import sqlite3
from fastapi import FastAPI
from app.core.database import Base, engine
from app.api.routes.news import router as news_router
from app.ingestion.scheduler import start_scheduler
from app.core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aegis-Risk API",
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
        print("✅ Gold Risk Table verified/created.")
    except Exception as e:
        print(f"❌ Error creating Gold table: {e}")

    start_scheduler()


@app.get("/")
def root():
    return {
        "message": "Aegis-Risk API is online",
        "docs": "/docs",
        "status": "ready"
    }


app.include_router(news_router, prefix="/api/news", tags=["news"])