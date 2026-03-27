from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import SessionLocal
from app.ingestion.news_fetcher import NewsFetcher
from app.ingestion.parser import normalize_article, is_relevant_article
from app.services.article_service import save_articles

scheduler = BackgroundScheduler()


def refresh_news_job() -> dict:
    db = SessionLocal()
    try:
        fetcher = NewsFetcher()
        raw_articles = fetcher.fetch_newsapi(settings.default_query, page_size=20)
        print("DEBUG raw_articles:", len(raw_articles))

        filtered_articles = [article for article in raw_articles if is_relevant_article(article)]
        print("DEBUG filtered_articles:", len(filtered_articles))

        normalized_articles = [
            normalize_article(article, topic="middle-east-risk")
            for article in filtered_articles
        ]
        print("DEBUG normalized_articles:", len(normalized_articles))

        result = save_articles(db, normalized_articles)
        print("DEBUG save result:", result)

        return {
            "status": "success",
            "fetched": len(raw_articles),
            "inserted": result["inserted"],
            "duplicates": result["duplicates"],
        }

    except Exception as exc:
        print("ERROR:", str(exc))
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