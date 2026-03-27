import requests
import feedparser
from bs4 import BeautifulSoup
from app.core.config import settings


class NewsFetcher:
    def __init__(self):
        self.newsapi_key = settings.newsapi_key

    def fetch_newsapi(self, query: str, page_size: int = 20) -> list[dict]:
        if not self.newsapi_key:
            print("NEWSAPI_KEY missing")
            return []

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": self.newsapi_key,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                print("NewsAPI error:", data)
                return []

            return data.get("articles", [])
        except Exception as exc:
            print("NewsAPI fetch failed:", str(exc))
            return []

    def fetch_bbc_rss(self) -> list[dict]:
        # Verified from BBC Developer feed pages
        rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"

        try:
            feed = feedparser.parse(rss_url)

            print("DEBUG BBC feed entries:", len(feed.entries))
            
            articles = []

            for entry in feed.entries[:20]:
                articles.append(
                    {
                        "source": {"name": "BBC News"},
                        "title": entry.get("title"),
                        "url": entry.get("link"),
                        "publishedAt": entry.get("published"),
                        "description": entry.get("summary"),
                        "content": entry.get("summary"),
                    }
                )

            return articles
        except Exception as exc:
            print("BBC RSS fetch failed:", str(exc))
            return []

    def fetch_aljazeera_page(self) -> list[dict]:
        # Verified accessible public page
        url = "https://www.aljazeera.com/news/"

        try:
            response = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            articles = []
            seen_links = set()

            for a in soup.select("a[href]"):
                href = a.get("href", "").strip()
                title = a.get_text(" ", strip=True)

                if not href or not title:
                    continue

                if href.startswith("/"):
                    full_url = f"https://www.aljazeera.com{href}"
                elif href.startswith("http"):
                    full_url = href
                else:
                    continue

                if "/news/" not in full_url and "/middle-east/" not in full_url and "/economy/" not in full_url:
                    continue

                if full_url in seen_links:
                    continue
                seen_links.add(full_url)

                if len(title) < 25:
                    continue

                articles.append(
                    {
                        "source": {"name": "Al Jazeera"},
                        "title": title,
                        "url": full_url,
                        "publishedAt": None,
                        "description": title,
                        "content": title,
                    }
                )

                if len(articles) >= 20:
                    break

            return articles
        except Exception as exc:
            print("Al Jazeera page fetch failed:", str(exc))
            return []