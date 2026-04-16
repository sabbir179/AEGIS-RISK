import json
import sqlite3
from datetime import datetime

import certifi
import feedparser
import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.ingestion.parser import is_relevant_article
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AegisRiskIngestion")


class NewsFetcher:
    def __init__(self):
        self.newsapi_key = settings.newsapi_key
        self.db_path = settings.database_url.replace("sqlite:///", "")
        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            )
        }

    def save_to_bronze(self, articles: list, source_name: str):
        """
        MEDALLION ARCHITECTURE: BRONZE LAYER
        Saves raw data exactly as received for verifiable audit trails.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bronze_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_json TEXT,
                source_name TEXT,
                ingested_at TIMESTAMP
            )
        """)

        for art in articles:
            cursor.execute(
                "INSERT INTO bronze_news (raw_json, source_name, ingested_at) VALUES (?, ?, ?)",
                (json.dumps(art), source_name, datetime.now().isoformat())
            )

        conn.commit()
        conn.close()

    @mcp.tool()
    def fetch_all_sources(self, query: str = None) -> str:
        """
        AGENTIC TOOL: Allows an AI agent to trigger a global news refresh.
        """
        search_query = query or settings.default_query

        results = {
            "NewsAPI": self.fetch_newsapi(search_query, page_size=50),
            "BBC": self.fetch_bbc_rss(),
            "AlJazeera": self.fetch_aljazeera_page(),
            "JerusalemPost": self.fetch_jpost_rss(),
            "TehranTimes": self.fetch_tehran_times_rss(),
        }

        for name, articles in results.items():
            print(f"DEBUG {name} fetched: {len(articles)}")
            if articles:
                self.save_to_bronze(articles, name)

        total_count = sum(len(v) for v in results.values())
        return f"Refreshed Bronze Layer: {total_count} articles ingested from 5 sources."

    def _build_newsapi_query(self, query: str | None) -> str:
        """
        NewsAPI works better with concise boolean-style queries.
        """
        if query and query.strip():
            return query.strip()

        return (
            '("Strait of Hormuz" OR "oil tanker" OR "shipping lane" OR "oil transit" '
            'OR "maritime security" OR "crude shipments" OR "energy supply route") '
            'AND '
            '(Iran OR "Red Sea" OR Yemen OR Houthi OR Gulf OR tanker OR blockade '
            'OR navy OR sanctions OR shipping)'
        )

    def _clean_text(self, value: str | None) -> str:
        if not value:
            return ""

        value = str(value)
        value = value.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        return " ".join(value.split()).strip()

    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract useful paragraph text from article HTML.
        """
        if not html:
            return ""

        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "noscript", "header", "footer", "svg", "form"]):
            tag.decompose()

        paragraphs = []
        for p in soup.find_all("p"):
            text = self._clean_text(p.get_text(" ", strip=True))
            if len(text) >= 40:
                paragraphs.append(text)

        content = " ".join(paragraphs)
        return self._clean_text(content)[:6000]

    def _fetch_full_article_text(self, url: str) -> str:
        """
        Try to fetch fuller article body from source URL.
        Falls back to empty string on failure.
        """
        if not url:
            return ""

        try:
            response = requests.get(
                url,
                headers=self.default_headers,
                timeout=12,
                verify=certifi.where(),
            )

            if response.status_code != 200:
                return ""

            return self._extract_text_from_html(response.text)

        except Exception as e:
            print(f"DEBUG full article fetch failed for {url}: {e}")
            return ""

    def _looks_like_placeholder(self, title: str, description: str, content: str) -> bool:
        """
        Reject obviously weak or repeated placeholder content.
        """
        title_clean = self._clean_text(title).lower()
        description_clean = self._clean_text(description).lower()
        content_clean = self._clean_text(content).lower()

        if not title_clean:
            return True

        if not description_clean and not content_clean:
            return True

        if content_clean and content_clean == title_clean:
            return True

        if description_clean == title_clean and content_clean == title_clean:
            return True

        if len(content_clean) < 60 and len(description_clean) < 60:
            return True

        return False

    def _is_relevant_normalized_article(self, article: dict) -> bool:
        """
        Final relevance gate before article is accepted.
        Uses parser.py rules plus a stricter oil-transit bias.
        """
        if not article:
            return False

        if not is_relevant_article(article):
            return False

        title = self._clean_text(article.get("title", "")).lower()
        description = self._clean_text(article.get("description", "")).lower()
        content = self._clean_text(article.get("content", "")).lower()

        text = f"{title} {description} {content}"

        oil_transit_terms = [
            "oil",
            "crude",
            "tanker",
            "shipping",
            "ship",
            "maritime",
            "strait of hormuz",
            "red sea",
            "cargo",
            "freight",
            "port",
            "blockade",
            "supply chain",
            "energy",
            "transit",
            "shipping lane",
            "naval",
        ]

        strong_geo_terms = [
            "iran",
            "israel",
            "middle east",
            "houthi",
            "yemen",
            "gaza",
            "gulf",
            "strait of hormuz",
            "red sea",
        ]

        oil_hits = sum(1 for term in oil_transit_terms if term in text)
        geo_hits = sum(1 for term in strong_geo_terms if term in text)

        if oil_hits >= 2 and geo_hits >= 1:
            return True

        if "strait of hormuz" in text and ("oil" in text or "tanker" in text or "shipping" in text):
            return True

        return False

    def _normalize_article_payload(
        self,
        source_name: str,
        title: str,
        url: str,
        published_at: str | None = None,
        description: str | None = None,
        content: str | None = None,
        allow_fetch_full_text: bool = True,
    ) -> dict | None:
        """
        Standardize article structure and skip very weak entries.
        """
        source_name = self._clean_text(source_name) or "Unknown"
        title = self._clean_text(title)
        url = self._clean_text(url)
        description = self._clean_text(description)
        content = self._clean_text(content)

        if not title or not url:
            return None

        weak_initial_content = (
            not content
            or content.lower() == title.lower()
            or len(content) < 120
        )

        if allow_fetch_full_text and weak_initial_content:
            fetched_content = self._fetch_full_article_text(url)
            if fetched_content:
                content = fetched_content

        if not content and description:
            content = description

        if not description and content:
            description = content[:600]

        if self._looks_like_placeholder(title, description, content):
            return None

        normalized = {
            "source": {"name": source_name},
            "title": title,
            "url": url,
            "publishedAt": published_at or datetime.now().isoformat(),
            "description": description,
            "content": content,
        }

        if not self._is_relevant_normalized_article(normalized):
            return None

        return normalized

    def fetch_newsapi(self, query: str | None, page_size: int = 50) -> list[dict]:
        if not self.newsapi_key:
            print("DEBUG NewsAPI: missing API key")
            return []

        url = "https://newsapi.org/v2/everything"
        clean_query = self._build_newsapi_query(query)

        params = {
            "q": clean_query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": self.newsapi_key,
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.default_headers,
                timeout=20,
                verify=certifi.where(),
            )
            print("DEBUG NewsAPI status:", response.status_code)

            data = response.json()
            print("DEBUG NewsAPI response status:", data.get("status"))
            print("DEBUG NewsAPI totalResults:", data.get("totalResults"))

            if response.status_code != 200:
                print("DEBUG NewsAPI error body:", data)
                return []

            articles = data.get("articles", [])
            cleaned = []

            for art in articles:
                normalized = self._normalize_article_payload(
                    source_name=(art.get("source") or {}).get("name", "NewsAPI"),
                    title=art.get("title"),
                    url=art.get("url"),
                    published_at=art.get("publishedAt"),
                    description=art.get("description"),
                    content=art.get("content") or art.get("description"),
                    allow_fetch_full_text=True,
                )
                if normalized:
                    cleaned.append(normalized)

            return cleaned

        except Exception as e:
            print(f"DEBUG NewsAPI exception: {e}")
            return []

    def fetch_bbc_rss(self) -> list[dict]:
        return self._parse_rss_via_requests(
            url="https://feeds.bbci.co.uk/news/world/rss.xml",
            name="BBC News",
        )

    def fetch_jpost_rss(self) -> list[dict]:
        return self._parse_rss_via_requests(
            url="https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
            name="Jerusalem Post",
        )

    def fetch_tehran_times_rss(self) -> list[dict]:
        return self._parse_rss_via_requests(
            url="https://www.tehrantimes.com/rss",
            name="Tehran Times",
        )

    def _parse_rss_via_requests(self, url: str, name: str) -> list[dict]:
        """
        Fetch RSS with requests first, then parse XML with feedparser.
        More reliable than feedparser.parse(url) when SSL/header issues appear.
        """
        try:
            response = requests.get(
                url,
                headers=self.default_headers,
                timeout=20,
                verify=certifi.where(),
            )
            print(f"DEBUG RSS HTTP status for {name}:", response.status_code)

            if response.status_code != 200:
                return []

            feed = feedparser.parse(response.text)

            if getattr(feed, "bozo", 0):
                print(f"DEBUG RSS parse warning for {name}: {getattr(feed, 'bozo_exception', 'unknown')}")

            entries = []
            seen_links = set()

            for e in feed.entries[:25]:
                title = e.get("title")
                link = e.get("link")

                if not title or not link:
                    continue

                if link in seen_links:
                    continue
                seen_links.add(link)

                summary = e.get("summary") or e.get("description") or ""
                published = e.get("published") or e.get("updated") or datetime.now().isoformat()

                normalized = self._normalize_article_payload(
                    source_name=name,
                    title=title,
                    url=link,
                    published_at=published,
                    description=summary,
                    content=summary,
                    allow_fetch_full_text=True,
                )
                if normalized:
                    entries.append(normalized)

            print(f"DEBUG RSS {name} entries:", len(entries))
            return entries

        except Exception as e:
            print(f"DEBUG RSS exception for {name}: {e}")
            return []

    def fetch_aljazeera_page(self) -> list[dict]:
        url = "https://www.aljazeera.com/news/"

        try:
            response = requests.get(
                url,
                timeout=20,
                headers=self.default_headers,
                verify=certifi.where(),
            )
            print("DEBUG Al Jazeera status:", response.status_code)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "lxml")
            articles = []
            seen_urls = set()

            for a in soup.select("a[href]"):
                href = self._clean_text(a.get("href"))
                title = self._clean_text(a.get_text(" ", strip=True))

                if not href or not title:
                    continue

                if "/news/" not in href:
                    continue

                if len(title) < 25:
                    continue

                full_url = f"https://www.aljazeera.com{href}" if href.startswith("/") else href

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                normalized = self._normalize_article_payload(
                    source_name="Al Jazeera",
                    title=title,
                    url=full_url,
                    published_at=datetime.now().isoformat(),
                    description=title,
                    content="",
                    allow_fetch_full_text=True,
                )

                if normalized:
                    articles.append(normalized)

                if len(articles) >= 20:
                    break

            print("DEBUG Al Jazeera parsed:", len(articles))
            return articles

        except Exception as e:
            print(f"DEBUG Al Jazeera exception: {e}")
            return []