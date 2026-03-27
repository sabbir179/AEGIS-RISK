from typing import List, Optional
from pydantic import BaseModel


class ArticleOut(BaseModel):
    id: int
    source: Optional[str] = None
    title: str
    url: str
    published_at: Optional[str] = None
    summary: Optional[str] = None
    topic: Optional[str] = None
    risk_score: Optional[int] = None

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