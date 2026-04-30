import re
import chromadb
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RiskLensMemory")


class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")

        self.collection = self.client.get_or_create_collection(
            name="aegis_risk_silver_context",
            metadata={"hnsw:space": "cosine"}
        )

    def _safe_text(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_text(self, text: str) -> str:
        text = self._safe_text(text).lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _tokenize(self, text: str) -> set[str]:
        cleaned = self._normalize_text(text)
        return set(re.findall(r"[a-zA-Z0-9_]+", cleaned))

    def _parse_date(self, value: str):
        value = self._safe_text(value)
        if not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            pass

        for fmt in [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue

        return None

    def _keyword_overlap_score(self, query: str, title: str, source: str, topic: str, content: str) -> float:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return 0.0

        title_tokens = self._tokenize(title)
        source_tokens = self._tokenize(source)
        topic_tokens = self._tokenize(topic)
        content_tokens = self._tokenize(content)

        score = 0.0

        title_overlap = len(query_tokens & title_tokens)
        topic_overlap = len(query_tokens & topic_tokens)
        source_overlap = len(query_tokens & source_tokens)
        content_overlap = len(query_tokens & content_tokens)

        score += title_overlap * 3.0
        score += topic_overlap * 2.5
        score += source_overlap * 1.0
        score += content_overlap * 1.5

        return score

    def _recency_score(self, published_at: str) -> float:
        parsed = self._parse_date(published_at)
        if not parsed:
            return 0.0

        now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
        age_hours = (now - parsed).total_seconds() / 3600

        if age_hours < 0:
            return 0.0
        if age_hours <= 12:
            return 2.0
        if age_hours <= 24:
            return 1.5
        if age_hours <= 48:
            return 1.0
        if age_hours <= 96:
            return 0.5
        return 0.0

    def _dedupe_results(self, items: list[dict]) -> list[dict]:
        seen = set()
        unique_items = []

        for item in items:
            title = self._normalize_text(item.get("title", ""))
            url = self._normalize_text(item.get("url", ""))
            doc_id = self._normalize_text(item.get("id", ""))

            key = url or title or doc_id
            if not key:
                key = str(item)

            if key in seen:
                continue

            seen.add(key)
            unique_items.append(item)

        return unique_items

    @mcp.tool()
    def upsert_silver_article(self, article_id: str, text: str, metadata: dict):
        """
        SILVER LAYER TOOL: Stores cleaned news for RAG.
        """
        safe_metadata = {
            "source": self._safe_text(metadata.get("source", "Unknown")),
            "title": self._safe_text(metadata.get("title", "")),
            "url": self._safe_text(metadata.get("url", "")),
            "published_at": self._safe_text(metadata.get("published_at", "")),
            "topic": self._safe_text(metadata.get("topic", "")),
        }

        clean_text = self._safe_text(text)

        self.collection.upsert(
            ids=[self._safe_text(article_id)],
            documents=[clean_text],
            metadatas=[safe_metadata],
        )

        return f"Article {article_id} successfully promoted to Silver Layer."

    @mcp.tool()
    def search_memory(self, query: str, n_results: int = 5):
        """
        Returns structured and re-ranked search results for the analyst/critic.
        """
        safe_query = self._safe_text(query)
        if not safe_query:
            return []

        # Fetch a wider pool first, then re-rank locally.
        initial_fetch = max(n_results * 3, 12)

        results = self.collection.query(
            query_texts=[safe_query],
            n_results=initial_fetch,
        )

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])
        distances = results.get("distances", [])

        formatted_results = []

        if documents and len(documents) > 0:
            docs_row = documents[0]
            metas_row = metadatas[0] if metadatas and len(metadatas) > 0 else [{}] * len(docs_row)
            ids_row = ids[0] if ids and len(ids) > 0 else [""] * len(docs_row)
            dist_row = distances[0] if distances and len(distances) > 0 else [None] * len(docs_row)

            for i, doc in enumerate(docs_row):
                meta = metas_row[i] if i < len(metas_row) else {}
                doc_id = ids_row[i] if i < len(ids_row) else ""
                distance = dist_row[i] if i < len(dist_row) else None

                source = self._safe_text(meta.get("source", "Unknown"))
                title = self._safe_text(meta.get("title", ""))
                url = self._safe_text(meta.get("url", ""))
                published_at = self._safe_text(meta.get("published_at", ""))
                topic = self._safe_text(meta.get("topic", ""))
                content = self._safe_text(doc)

                keyword_score = self._keyword_overlap_score(
                    query=safe_query,
                    title=title,
                    source=source,
                    topic=topic,
                    content=content,
                )

                recency_score = self._recency_score(published_at)

                similarity_score = 0.0
                if isinstance(distance, (int, float)):
                    similarity_score = 1.0 / (1.0 + float(distance))

                final_rank_score = (similarity_score * 5.0) + keyword_score + recency_score

                formatted_results.append({
                    "id": self._safe_text(doc_id),
                    "source": source,
                    "title": title,
                    "url": url,
                    "published_at": published_at,
                    "topic": topic,
                    "summary": content[:1200],
                    "content": content,
                    "_rank_score": final_rank_score,
                })

        deduped = self._dedupe_results(formatted_results)
        ranked = sorted(deduped, key=lambda x: x["_rank_score"], reverse=True)

        final_results = []
        for item in ranked[:n_results]:
            clean_item = dict(item)
            clean_item.pop("_rank_score", None)
            final_results.append(clean_item)

        return final_results


# --- COMPATIBILITY WRAPPERS ---

def add_article_to_vectordb(article_id: str, text: str, metadata: dict):
    db = VectorDB()
    return db.upsert_silver_article(article_id, text, metadata)


def search_articles(query: str, n_results: int = 5):
    db = VectorDB()
    return db.search_memory(query=query, n_results=n_results)
