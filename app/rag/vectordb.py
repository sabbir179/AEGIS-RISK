import chromadb
from chromadb.config import Settings
from app.core.config import settings
from mcp.server.fastmcp import FastMCP

# Initialize MCP Server for the Vector Memory Module
# This satisfies the "Agentic AI" requirement for the Digital Catapult role.
mcp = FastMCP("AegisRiskMemory")

class VectorDB:
    def __init__(self):
        # Persistent storage path for the Silver Layer
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # MEDALLION SILVER LAYER: Cleaned, embedded context
        # HNSW with Cosine similarity is the research standard for NLP/Geopolitical context.
        self.collection = self.client.get_or_create_collection(
            name="aegis_risk_silver_context",
            metadata={"hnsw:space": "cosine"} 
        )

    @mcp.tool()
    def upsert_silver_article(self, article_id: str, text: str, metadata: dict):
        """
        SILVER LAYER TOOL: Stores cleaned news for RAG.
        """
        self.collection.upsert(
            ids=[article_id],
            documents=[text],
            metadatas=[metadata],
        )
        return f"Article {article_id} successfully promoted to Silver Layer."

    @mcp.tool()
    def search_memory(self, query: str, n_results: int = 5) -> str:
        """
        AGENTIC TOOL: Used by Analyst/Critic agents to verify facts against the Silver Layer.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                formatted_results.append(f"SOURCE: {meta.get('source')}\nCONTENT: {doc}\n---")
        
        return "\n".join(formatted_results) if formatted_results else "No relevant history found."

# --- COMPATIBILITY WRAPPERS (Fixes the ImportError) ---

def add_article_to_vectordb(article_id: str, text: str, metadata: dict):
    """
    Standard function wrapper so article_service.py can find it.
    """
    db = VectorDB()
    return db.upsert_silver_article(article_id, text, metadata)

def search_articles(query: str, n_results: int = 5):
    """
    Standard function wrapper for the API search routes.
    """
    db = VectorDB()
    # Returns raw results for the API to process
    return db.collection.query(query_texts=[query], n_results=n_results)