import requests
import feedparser
import sqlite3
import json
from datetime import datetime
from bs4 import BeautifulSoup
from app.core.config import settings
from mcp.server.fastmcp import FastMCP

# Initialize MCP Server - This makes your code "Agent-Ready" for the job requirement
mcp = FastMCP("AegisRiskIngestion")

class NewsFetcher:
    def __init__(self):
        self.newsapi_key = settings.newsapi_key
        # Extracts the raw path from your .env DATABASE_URL
        self.db_path = settings.database_url.replace("sqlite:///", "")

    def save_to_bronze(self, articles: list, source_name: str):
        """
        MEDALLION ARCHITECTURE: BRONZE LAYER
        Saves raw data exactly as received for 'Verifiable AI' audits.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bronze_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_json TEXT,
                source_name TEXT,
                ingested_at TIMESTAMP
            )
        ''')

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
        AGENTIC TOOL: Allows an AI Agent to trigger a global news refresh.
        """
        search_query = query or settings.default_query
        
        results = {
            "NewsAPI": self.fetch_newsapi(search_query),
            "BBC": self.fetch_bbc_rss(),
            "AlJazeera": self.fetch_aljazeera_page(),
            "JerusalemPost": self.fetch_jpost_rss(),
            "TehranTimes": self.fetch_tehran_times_rss()
        }

        for name, articles in results.items():
            if articles:
                self.save_to_bronze(articles, name)

        total_count = sum(len(v) for v in results.values())
        return f"Refreshed Bronze Layer: {total_count} articles ingested from 5 sources."

    def fetch_newsapi(self, query: str, page_size: int = 20) -> list[dict]:
        if not self.newsapi_key: return []
        url = "https://newsapi.org/v2/everything"
        params = {"q": query, "language": "en", "sortBy": "publishedAt", "pageSize": page_size, "apiKey": self.newsapi_key}
        try:
            r = requests.get(url, params=params, timeout=20)
            return r.json().get("articles", [])
        except: return []

    def fetch_bbc_rss(self) -> list[dict]:
        url = "https://feeds.bbci.co.uk/news/world/rss.xml"
        return self._parse_rss(url, "BBC News")

    def fetch_jpost_rss(self) -> list[dict]:
        # Specific 2026 feed for Middle East tensions
        url = "https://www.jpost.com/rss/rssfeedsfrontpage.aspx"
        return self._parse_rss(url, "Jerusalem Post")

    def fetch_tehran_times_rss(self) -> list[dict]:
        # Direct Iranian state-aligned perspective
        url = "https://www.tehrantimes.com/rss"
        return self._parse_rss(url, "Tehran Times")

    def _parse_rss(self, url: str, name: str) -> list[dict]:
        try:
            feed = feedparser.parse(url)
            return [{
                "source": {"name": name},
                "title": e.get("title"),
                "url": e.get("link"),
                "publishedAt": e.get("published"),
                "description": e.get("summary"),
                "content": e.get("summary")
            } for e in feed.entries[:15]]
        except: return []

    def fetch_aljazeera_page(self) -> list[dict]:
        url = "https://www.aljazeera.com/news/"
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "lxml")
            articles = []
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if "/news/" in href and len(title) > 25:
                    articles.append({
                        "source": {"name": "Al Jazeera"},
                        "title": title,
                        "url": f"https://www.aljazeera.com{href}" if href.startswith("/") else href,
                        "publishedAt": datetime.now().isoformat(),
                        "description": title, "content": title
                    })
                if len(articles) >= 15: break
            return articles
        except: return []