import chromadb
from chromadb.config import Settings
from app.core.config import settings
from mcp.server.fastmcp import FastMCP

# Initialize MCP Server for the Vector Memory Module
mcp = FastMCP("AegisRiskMemory")

class VectorDB:
    def __init__(self):
        # Using the path from your .env or default
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # MEDALLION SILVER LAYER: Cleaned, embedded context
        self.collection = self.client.get_or_create_collection(
            name="aegis_risk_silver_context",
            metadata={"hnsw:space": "cosine"} # Best for similarity matching
        )

    @mcp.tool()
    def upsert_silver_article(self, article_id: str, text: str, metadata: dict):
        """
        SILVER LAYER TOOL: Stores cleaned, high-quality news for RAG.
        Used by the Refiner Agent after cleaning Bronze data.
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
        AGENTIC TOOL: Allows Analyst/Critic agents to search for historical context.
        Essential for 'Verifiable AI' and reducing hallucinations.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        
        # Formatting for the LLM to read easily
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                formatted_results.append(f"SOURCE: {meta.get('source')}\nCONTENT: {doc}\n---")
        
        return "\n".join(formatted_results) if formatted_results else "No relevant history found."

    def delete_old_entries(self):
        """Cleanup tool for maintaining system performance."""
        # Optional: Logic to remove data older than 30 days for IEEE paper scope
        pass