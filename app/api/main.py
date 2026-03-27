from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.article import Article
from app.api.routes.news import router as news_router
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