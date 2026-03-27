import requests
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

        print("DEBUG query:", query)
        print("DEBUG api key prefix:", settings.newsapi_key[:6] + "...")
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        print("DEBUG status code:", response.status_code)
        print("DEBUG response text:", response.text[:1000])

        response.raise_for_status()
        data = response.json()

        print("DEBUG totalResults:", data.get("totalResults"))
        print("DEBUG articles count:", len(data.get("articles", [])))

        return data.get("articles", [])