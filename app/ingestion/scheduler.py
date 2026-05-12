import logging

from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import SessionLocal
from app.ingestion.news_fetcher import NewsFetcher
from app.ingestion.parser import normalize_article, is_relevant_article
from app.services.article_service import ArticleService

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def refresh_news_job() -> dict:
    db = SessionLocal()
    try:
        fetcher = NewsFetcher()

        newsapi_articles = fetcher.fetch_newsapi(settings.default_query, page_size=20)
        bbc_articles = fetcher.fetch_bbc_rss()
        aljazeera_articles = fetcher.fetch_aljazeera_page()

        raw_articles = newsapi_articles + bbc_articles + aljazeera_articles

        logger.debug("newsapi_articles: %s", len(newsapi_articles))
        logger.debug("bbc_articles: %s", len(bbc_articles))
        logger.debug("aljazeera_articles: %s", len(aljazeera_articles))
        logger.debug("raw_articles_total: %s", len(raw_articles))

        filtered_articles = [
            article for article in raw_articles
            if is_relevant_article(article)
        ]
        logger.debug("filtered_articles: %s", len(filtered_articles))

        normalized_articles = [
            normalize_article(article, topic="middle-east-risk")
            for article in filtered_articles
        ]
        logger.debug("normalized_articles: %s", len(normalized_articles))

        result = ArticleService.save_articles(db, normalized_articles)
        logger.debug("save result: %s", result)

        return {
            "status": "success",
            "fetched": len(raw_articles),
            "inserted": result["inserted"],
            "duplicates": result["duplicates"],
        }

    except Exception as exc:
        logger.exception("News refresh job failed: %s", exc)
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
