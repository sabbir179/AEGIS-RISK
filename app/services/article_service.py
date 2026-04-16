from typing import Dict, List

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.article import Article
from app.rag.vectordb import add_article_to_vectordb


TRANSIT_KEYWORDS = [
    "oil transit",
    "transit route",
    "shipping lane",
    "sea lane",
    "maritime route",
    "maritime security",
    "oil tanker",
    "tanker",
    "shipping",
    "shipment",
    "cargo vessel",
    "port",
    "strait of hormuz",
    "hormuz",
    "red sea",
    "suez",
    "blockade",
    "navy",
    "naval",
    "vessel",
    "freight",
]

OIL_KEYWORDS = [
    "oil",
    "crude",
    "petroleum",
    "fuel",
    "energy",
    "lng",
]

REGION_KEYWORDS = [
    "iran",
    "israel",
    "middle east",
    "gulf",
    "yemen",
    "houthi",
    "red sea",
    "strait of hormuz",
    "hormuz",
]

TOPIC_RULES = {
    "oil": {
        "must_any": TRANSIT_KEYWORDS + OIL_KEYWORDS,
        "prefer_any": REGION_KEYWORDS,
    },
    "oil transit": {
        "must_any": TRANSIT_KEYWORDS + OIL_KEYWORDS,
        "prefer_any": REGION_KEYWORDS,
    },
    "iran": {
        "must_any": ["iran"] + REGION_KEYWORDS,
        "prefer_any": TRANSIT_KEYWORDS + OIL_KEYWORDS,
    },
    "iran transit": {
        "must_any": ["iran"] + TRANSIT_KEYWORDS,
        "prefer_any": OIL_KEYWORDS,
    },
}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).lower().split()).strip()


def _article_text(article_data: Dict) -> str:
    title = _normalize_text(article_data.get("title"))
    summary = _normalize_text(article_data.get("summary"))
    content = _normalize_text(article_data.get("content"))
    topic = _normalize_text(article_data.get("topic"))
    source = _normalize_text(article_data.get("source"))
    return f"{title} {summary} {content} {topic} {source}".strip()


def _count_matches(text: str, keywords: List[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _is_transit_focused(text: str) -> bool:
    transit_hits = _count_matches(text, TRANSIT_KEYWORDS)
    oil_hits = _count_matches(text, OIL_KEYWORDS)
    region_hits = _count_matches(text, REGION_KEYWORDS)

    # Strong signal: actual transit/shipping + oil/energy
    if transit_hits >= 1 and oil_hits >= 1:
        return True

    # Strong regional maritime signal
    if transit_hits >= 1 and region_hits >= 1:
        return True

    # Very strong explicit transit coverage
    if transit_hits >= 2:
        return True

    return False


def is_vector_relevant(article_data: Dict) -> bool:
    """
    Promote only articles that are truly useful for oil / maritime transit RAG.
    This keeps Chroma cleaner and reduces noisy analyst outputs.
    """
    text = _article_text(article_data)

    if not text:
        return False

    return _is_transit_focused(text)


class ArticleService:
    @staticmethod
    def get_latest_articles(db: Session, topic: str = None, limit: int = 20):
        """
        Retrieves articles for the Silver Layer.

        Behavior:
        - If topic is blank: return latest articles
        - If topic is oil/oil transit: require oil + transit style matching
        - If topic is iran/iran transit: require iran + prefer transit/oil context
        """
        query = db.query(Article)

        if topic and topic.strip():
            normalized_topic = topic.strip().lower()

            if normalized_topic in ("oil", "oil transit"):
                query = query.filter(
                    and_(
                        or_(
                            Article.title.ilike("%oil%"),
                            Article.summary.ilike("%oil%"),
                            Article.content.ilike("%oil%"),
                            Article.title.ilike("%crude%"),
                            Article.summary.ilike("%crude%"),
                            Article.content.ilike("%crude%"),
                            Article.title.ilike("%fuel%"),
                            Article.summary.ilike("%fuel%"),
                            Article.content.ilike("%fuel%"),
                            Article.title.ilike("%lng%"),
                            Article.summary.ilike("%lng%"),
                            Article.content.ilike("%lng%"),
                        ),
                        or_(
                            Article.title.ilike("%transit%"),
                            Article.summary.ilike("%transit%"),
                            Article.content.ilike("%transit%"),
                            Article.title.ilike("%tanker%"),
                            Article.summary.ilike("%tanker%"),
                            Article.content.ilike("%tanker%"),
                            Article.title.ilike("%shipping%"),
                            Article.summary.ilike("%shipping%"),
                            Article.content.ilike("%shipping%"),
                            Article.title.ilike("%maritime%"),
                            Article.summary.ilike("%maritime%"),
                            Article.content.ilike("%maritime%"),
                            Article.title.ilike("%strait of hormuz%"),
                            Article.summary.ilike("%strait of hormuz%"),
                            Article.content.ilike("%strait of hormuz%"),
                            Article.title.ilike("%hormuz%"),
                            Article.summary.ilike("%hormuz%"),
                            Article.content.ilike("%hormuz%"),
                            Article.title.ilike("%port%"),
                            Article.summary.ilike("%port%"),
                            Article.content.ilike("%port%"),
                            Article.title.ilike("%blockade%"),
                            Article.summary.ilike("%blockade%"),
                            Article.content.ilike("%blockade%"),
                            Article.title.ilike("%navy%"),
                            Article.summary.ilike("%navy%"),
                            Article.content.ilike("%navy%"),
                        ),
                    )
                )

            elif normalized_topic in ("iran", "iran transit"):
                query = query.filter(
                    and_(
                        or_(
                            Article.title.ilike("%iran%"),
                            Article.summary.ilike("%iran%"),
                            Article.content.ilike("%iran%"),
                        ),
                        or_(
                            Article.title.ilike("%transit%"),
                            Article.summary.ilike("%transit%"),
                            Article.content.ilike("%transit%"),
                            Article.title.ilike("%oil%"),
                            Article.summary.ilike("%oil%"),
                            Article.content.ilike("%oil%"),
                            Article.title.ilike("%tanker%"),
                            Article.summary.ilike("%tanker%"),
                            Article.content.ilike("%tanker%"),
                            Article.title.ilike("%shipping%"),
                            Article.summary.ilike("%shipping%"),
                            Article.content.ilike("%shipping%"),
                            Article.title.ilike("%maritime%"),
                            Article.summary.ilike("%maritime%"),
                            Article.content.ilike("%maritime%"),
                            Article.title.ilike("%strait of hormuz%"),
                            Article.summary.ilike("%strait of hormuz%"),
                            Article.content.ilike("%strait of hormuz%"),
                            Article.title.ilike("%hormuz%"),
                            Article.summary.ilike("%hormuz%"),
                            Article.content.ilike("%hormuz%"),
                            Article.title.ilike("%blockade%"),
                            Article.summary.ilike("%blockade%"),
                            Article.content.ilike("%blockade%"),
                            Article.title.ilike("%navy%"),
                            Article.summary.ilike("%navy%"),
                            Article.content.ilike("%navy%"),
                        ),
                    )
                )

            else:
                search_filter = f"%{topic.strip()}%"
                query = query.filter(
                    or_(
                        Article.title.ilike(search_filter),
                        Article.summary.ilike(search_filter),
                        Article.content.ilike(search_filter),
                        Article.source.ilike(search_filter),
                        Article.topic.ilike(search_filter),
                    )
                )

        return query.order_by(Article.published_at.desc()).limit(limit).all()

    @staticmethod
    def create_article(db: Session, article_data: Dict):
        """
        Saves a single article to SQLite.
        Promotes to Chroma only if it is transit-relevant.
        """
        db_article = Article(**article_data)
        db.add(db_article)
        db.commit()
        db.refresh(db_article)

        if not is_vector_relevant(article_data):
            print(f"Skipped VectorDB (not transit-relevant): {db_article.title}")
            return db_article

        try:
            vector_text = " ".join(
                filter(
                    None,
                    [
                        db_article.title,
                        db_article.summary,
                        db_article.content,
                    ],
                )
            ).strip()

            if vector_text:
                add_article_to_vectordb(
                    article_id=db_article.fingerprint,
                    text=vector_text,
                    metadata={
                        "source": db_article.source,
                        "title": db_article.title,
                        "url": db_article.url,
                        "published_at": str(db_article.published_at),
                        "topic": db_article.topic or "",
                    },
                )
                print(f"VectorDB upserted: {db_article.title}")
            else:
                print(f"Skipped VectorDB (empty text): {db_article.title}")

        except Exception as e:
            print(f"VectorDB single upsert failed for '{db_article.title}': {e}")

        return db_article

    @staticmethod
    def save_articles(db: Session, articles: List[Dict]):
        """
        Bulk save articles with duplicate protection.
        Only transit-relevant articles are promoted into Chroma Silver Layer.
        """
        inserted = 0
        duplicates = 0

        for article_data in articles:
            if not article_data.get("fingerprint"):
                print(f"SKIPPING missing fingerprint: {article_data.get('title', 'Untitled')}")
                continue

            try:
                db_article = Article(**article_data)
                db.add(db_article)
                db.commit()
                db.refresh(db_article)
                inserted += 1

                if not is_vector_relevant(article_data):
                    print(f"Skipped VectorDB (not transit-relevant): {db_article.title}")
                    continue

                try:
                    vector_text = " ".join(
                        filter(
                            None,
                            [
                                db_article.title,
                                db_article.summary,
                                db_article.content,
                            ],
                        )
                    ).strip()

                    if not vector_text:
                        print(f"Skipped VectorDB (empty text): {db_article.title}")
                        continue

                    add_article_to_vectordb(
                        article_id=db_article.fingerprint,
                        text=vector_text,
                        metadata={
                            "source": db_article.source,
                            "title": db_article.title,
                            "url": db_article.url,
                            "published_at": str(db_article.published_at),
                            "topic": db_article.topic or "",
                        },
                    )
                    print(f"VectorDB upserted: {db_article.title}")

                except Exception as e:
                    print(f"VectorDB upsert failed for '{db_article.title}': {e}")

            except IntegrityError:
                db.rollback()
                duplicates += 1
                print(f"Duplicate skipped: {article_data.get('title', 'Untitled')}")

            except Exception as e:
                db.rollback()
                print(f"Failed to save article '{article_data.get('title', 'Untitled')}': {e}")

        return {
            "inserted": inserted,
            "duplicates": duplicates,
        }