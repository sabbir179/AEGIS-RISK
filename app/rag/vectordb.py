import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="aegis_risk_articles"
)


def add_article_to_vectordb(article_id: str, text: str, metadata: dict):
    collection.upsert(
        ids=[article_id],
        documents=[text],
        metadatas=[metadata],
    )


def search_articles(query: str, n_results: int = 5):
    return collection.query(
        query_texts=[query],
        n_results=n_results,
    )