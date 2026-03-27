from pathlib import Path

PROJECT_FILES = {
    "app/__init__.py": "",
    "app/api/__init__.py": "",
    "app/api/main.py": '''from fastapi import FastAPI
from app.api.routes.news import router as news_router
from app.core.database import Base, engine
from app.ingestion.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aegis-Risk API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def root():
    return {"message": "Aegis-Risk API is running"}


app.include_router(news_router, prefix="/api/news", tags=["news"])
''',

    "app/api/routes/__init__.py": "",
    "app/api/routes/news.py": '''from fastapi import APIRouter, Depends, Query
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
''',

    "app/api/schemas/__init__.py": "",
    "app/api/schemas/news.py": '''from typing import List, Optional
from pydantic import BaseModel


class ArticleOut(BaseModel):
    id: int
    source: Optional[str] = None
    title: str
    url: str
    published_at: Optional[str] = None
    summary: Optional[str] = None
    topic: Optional[str] = None

    class Config:
        from_attributes = True


class RefreshResponse(BaseModel):
    status: str
    fetched: int
    inserted: int
    duplicates: int


class LatestNewsResponse(BaseModel):
    topic: Optional[str] = None
    count: int
    articles: List[ArticleOut]
''',

    "app/core/__init__.py": "",
    "app/core/config.py": '''from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    newsapi_key: str | None = None
    database_url: str = "sqlite:///./aegis_risk.db"
    refresh_minutes: int = 60
    default_query: str = "Israel Iran oil shipping Red Sea Suez UK supply chain"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
''',

    "app/core/database.py": '''from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',

    "app/ingestion/__init__.py": "",
    "app/ingestion/dedupe.py": '''import hashlib


def article_fingerprint(title: str, url: str) -> str:
    clean_title = (title or "").strip().lower()
    clean_url = (url or "").strip().lower()
    raw = f"{clean_title}|{clean_url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
''',

    "app/ingestion/news_fetcher.py": '''import requests
from app.core.config import settings


class NewsFetcher:
    BASE_URL = "https://newsapi.org/v2/everything"

    def fetch_newsapi(self, query: str, page_size: int = 20) -> list[dict]:
        if not settings.newsapi_key:
            raise ValueError("NEWSAPI_KEY is missing in .env")

        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": settings.newsapi_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
''',

    "app/ingestion/parser.py": '''def normalize_article(article: dict, topic: str | None = None) -> dict:
    return {
        "source": (article.get("source") or {}).get("name"),
        "title": article.get("title") or "Untitled",
        "url": article.get("url") or "",
        "published_at": article.get("publishedAt"),
        "summary": article.get("description"),
        "content": article.get("content"),
        "topic": topic,
    }
''',

    "app/ingestion/scheduler.py": '''from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import SessionLocal
from app.ingestion.news_fetcher import NewsFetcher
from app.ingestion.parser import normalize_article
from app.services.article_service import save_articles

scheduler = BackgroundScheduler()


def refresh_news_job() -> dict:
    db = SessionLocal()
    try:
        fetcher = NewsFetcher()
        raw_articles = fetcher.fetch_newsapi(settings.default_query, page_size=20)
        normalized_articles = [
            normalize_article(article, topic="middle-east-risk")
            for article in raw_articles
        ]
        result = save_articles(db, normalized_articles)

        return {
            "status": "success",
            "fetched": len(raw_articles),
            "inserted": result["inserted"],
            "duplicates": result["duplicates"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "fetched": 0,
            "inserted": 0,
            "duplicates": 0,
            "error": str(exc),
        }
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            refresh_news_job,
            trigger="interval",
            minutes=settings.refresh_minutes,
            id="news_refresh_job",
            replace_existing=True,
        )
        scheduler.start()
''',

    "app/models/__init__.py": "",
    "app/models/article.py": '''from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    source = Column(String(255), nullable=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    published_at = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    topic = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True)
''',

    "app/services/__init__.py": "",
    "app/services/article_service.py": '''from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.article import Article
from app.ingestion.dedupe import article_fingerprint


def save_articles(db: Session, normalized_articles: list[dict]) -> dict:
    inserted = 0
    duplicates = 0

    for item in normalized_articles:
        fingerprint = article_fingerprint(item["title"], item["url"])
        existing = db.query(Article).filter(Article.fingerprint == fingerprint).first()

        if existing:
            duplicates += 1
            continue

        article = Article(
            fingerprint=fingerprint,
            source=item.get("source"),
            title=item.get("title"),
            url=item.get("url"),
            published_at=item.get("published_at"),
            summary=item.get("summary"),
            content=item.get("content"),
            topic=item.get("topic"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(article)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "duplicates": duplicates}


def get_latest_articles(db: Session, topic: str | None = None, limit: int = 10) -> list[Article]:
    query = db.query(Article)

    if topic:
        query = query.filter(Article.title.ilike(f"%{topic}%"))

    return query.order_by(desc(Article.id)).limit(limit).all()
''',

    "app/ui/__init__.py": "",
    "app/ui/streamlit_app.py": '''import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Aegis-Risk Live News Monitor", layout="wide")
st.title("Aegis-Risk Live News Monitor")

topic = st.text_input("Topic filter", value="")
limit = st.slider("Number of articles", min_value=1, max_value=20, value=10)

col1, col2 = st.columns(2)

with col1:
    if st.button("Refresh News Now"):
        try:
            response = requests.post(f"{API_BASE}/news/refresh", timeout=60)
            response.raise_for_status()
            data = response.json()
            st.success(
                f"Fetched: {data['fetched']} | Inserted: {data['inserted']} | Duplicates: {data['duplicates']}"
            )
        except Exception as exc:
            st.error(f"Refresh failed: {exc}")

with col2:
    if st.button("Load Latest News"):
        try:
            response = requests.get(
                f"{API_BASE}/news/latest",
                params={"topic": topic or None, "limit": limit},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            st.subheader("Latest Articles")
            if not data["articles"]:
                st.info("No articles found.")
            else:
                for article in data["articles"]:
                    st.markdown(f"### [{article['title']}]({article['url']})")
                    st.write(f"**Source:** {article.get('source', 'Unknown')}")
                    st.write(f"**Published:** {article.get('published_at', 'Unknown')}")
                    st.write(article.get("summary", "No summary available."))
                    st.divider()
        except Exception as exc:
            st.error(f"Could not load news: {exc}")
''',

    ".env.example": '''NEWSAPI_KEY=your_newsapi_key_here
DATABASE_URL=sqlite:///./aegis_risk.db
REFRESH_MINUTES=60
DEFAULT_QUERY=Israel Iran oil shipping Red Sea Suez UK supply chain
''',

    "requirements.txt": '''fastapi
uvicorn
streamlit
requests
apscheduler
sqlalchemy
pydantic
pydantic-settings
python-dotenv
''',

    "README.md": '''# Aegis-Risk

Aegis-Risk is a live news monitoring starter project for geopolitical and supply-chain risk analysis.

## Run
1. Create and activate a virtual environment
2. Install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and add your NEWSAPI_KEY
4. Run backend:
   uvicorn app.api.main:app --reload
5. Run frontend:
   streamlit run app/ui/streamlit_app.py
''',
}


def create_project():
    for file_path, content in PROJECT_FILES.items():
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"Created: {file_path}")
        else:
            print(f"Skipped (already exists): {file_path}")


if __name__ == "__main__":
    create_project()
    print("\\nProject scaffold created successfully.")