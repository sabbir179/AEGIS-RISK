from sqlalchemy import Column, Integer, String, Text, DateTime
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
    risk_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
