# Aegis-Risk Technical Documentation

## 1. Project Summary

**Aegis-Risk** is an AI-powered geopolitical risk monitoring system focused on oil transit routes, maritime chokepoints, shipping lanes, and global energy supply chain disruption signals.

The system ingests open-source news, filters for geopolitical and supply-chain relevance, stores normalized article evidence, retrieves relevant context through a vector database, and generates evidence-backed risk assessments using a multi-agent LLM workflow.

The project is designed as a practical decision-support application rather than a generic news summarizer. Its main output is a verified risk report with source-backed claims, a numeric risk score, and historical risk index storage.

## 2. Core Capabilities

- Collects news from NewsAPI, RSS feeds, and targeted web parsing.
- Cleans, normalizes, and deduplicates article records.
- Stores raw and normalized data using a Medallion-style architecture.
- Promotes transit-relevant articles into ChromaDB for semantic retrieval.
- Uses retrieval-augmented generation to answer risk questions from evidence.
- Runs a two-agent LLM workflow:
  - Lead Analyst: generates the geopolitical risk assessment.
  - Verification Critic: checks whether claims are supported by retrieved sources.
- Persists final risk scores and reports into the Gold risk index.
- Provides a FastAPI backend and Streamlit dashboard for interaction.

## 3. High-Level Architecture

```text
News Sources
  ├── NewsAPI
  ├── BBC RSS
  ├── Al Jazeera web parsing
  ├── Jerusalem Post RSS
  └── Tehran Times RSS
        ↓
Ingestion Pipeline
  ├── fetch articles
  ├── clean article text
  ├── reject placeholder content
  ├── apply relevance rules
  └── normalize fields
        ↓
Medallion Data Layer
  ├── Bronze: raw article JSON
  ├── Silver: normalized SQLite articles
  ├── Vector Memory: ChromaDB evidence index
  └── Gold: verified risk reports and risk scores
        ↓
RAG + Multi-Agent Reasoning
  ├── retrieve relevant evidence from ChromaDB
  ├── generate analyst report with GPT-4o
  ├── verify claims with Claude
  └── save consensus output to Gold layer
        ↓
Application Layer
  ├── FastAPI backend
  └── Streamlit dashboard
```

Architecture visual:

![Aegis-Risk Architecture](../diagrams/aegis-risk-medallion-architecture.svg)

## 4. Repository Structure

```text
app/
  api/
    main.py                 FastAPI application startup and router registration
    routes/news.py          News refresh, latest articles, RAG ask, risk index endpoints
    schemas/news.py         Pydantic response schemas for article and refresh APIs
    schemas/rag.py          RAG-related schema definitions

  core/
    config.py               Environment variable and application settings
    database.py             SQLAlchemy engine/session setup

  ingestion/
    news_fetcher.py         NewsAPI, RSS, and web source collection
    parser.py               Cleaning, relevance filtering, normalization, risk scoring
    dedupe.py               Article fingerprint helper
    scheduler.py            Scheduled refresh job

  models/
    article.py              SQLAlchemy Article model

  rag/
    vectordb.py             ChromaDB persistence and semantic retrieval
    llm_answer.py           Multi-agent analyst and critic workflow

  services/
    article_service.py      Article query, save, dedupe handling, vector promotion

  ui/
    streamlit_app.py        Streamlit dashboard

diagrams/
  aegis-risk-medallion-architecture.svg
  aegis-risk-medallion-architecture.png

screenshots/
  dashboard.png
  ai_answers.png
  sources.png
```

## 5. Runtime Components

### 5.1 Streamlit UI

File: `app/ui/streamlit_app.py`

The Streamlit dashboard acts as the operator-facing control center. It communicates with the FastAPI backend at:

```python
API_BASE = "http://127.0.0.1:8000/api"
```

Main dashboard responsibilities:

- Trigger or consume ingestion refresh workflows.
- Display latest evidence articles.
- Run user queries against the RAG and multi-agent workflow.
- Display analyst and critic outputs.
- Show Gold-layer risk trend data.
- Provide source visibility for retrieved evidence.

### 5.2 FastAPI Backend

Files:

- `app/api/main.py`
- `app/api/routes/news.py`

The backend exposes operational endpoints for ingestion, article retrieval, RAG questioning, and Gold-layer risk chart data.

On startup, FastAPI:

- Creates SQLAlchemy tables through `Base.metadata.create_all`.
- Ensures the `gold_risk_index` table exists.
- Starts the APScheduler background refresh job.

### 5.3 Ingestion Pipeline

Files:

- `app/ingestion/news_fetcher.py`
- `app/ingestion/parser.py`
- `app/ingestion/scheduler.py`

The ingestion pipeline pulls articles from configured sources, cleans them, applies relevance filtering, normalizes fields, and saves them to SQLite.

Primary sources:

- NewsAPI
- BBC RSS
- Al Jazeera news page parsing
- Jerusalem Post RSS
- Tehran Times RSS

The scheduled refresh job currently uses NewsAPI, BBC RSS, and Al Jazeera directly. `NewsFetcher.fetch_all_sources` also includes Jerusalem Post and Tehran Times.

### 5.4 SQLite Data Store

Files:

- `app/core/database.py`
- `app/models/article.py`

SQLite is used for local persistence. The main normalized article table is `articles`.

The Gold risk index is managed through direct SQLite statements in `app/api/main.py` and `app/rag/llm_answer.py`.

### 5.5 ChromaDB Vector Store

File: `app/rag/vectordb.py`

ChromaDB stores transit-relevant article evidence for semantic search. The persistent storage path is:

```text
./chroma_db
```

Collection name:

```text
aegis_risk_silver_context
```

The vector store supports:

- Upserting article text and metadata.
- Semantic search against stored evidence.
- Local re-ranking using semantic similarity, keyword overlap, and recency scoring.
- Deduplication of retrieved results.

### 5.6 Multi-Agent LLM Layer

File: `app/rag/llm_answer.py`

The multi-agent workflow has two primary roles:

- **Lead Analyst**: uses GPT-4o to generate the initial geopolitical risk report.
- **Verification Critic**: uses Claude to validate the analyst report against retrieved evidence.

The workflow requires the models to use only retrieved context and include source citations such as `[Source 1]`.

The final output is saved into the Gold layer with:

- normalized topic
- extracted risk score
- full report
- consensus status
- timestamp

## 6. Medallion Data Architecture

### 6.1 Bronze Layer

Implemented in: `NewsFetcher.save_to_bronze`

Bronze stores raw article payloads as JSON for auditability.

Table:

```text
bronze_news
```

Fields:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
raw_json TEXT
source_name TEXT
ingested_at TIMESTAMP
```

Purpose:

- Preserve source payloads.
- Support debugging and traceability.
- Keep a raw record before normalization changes are applied.

### 6.2 Silver Layer

Implemented through:

- `parser.normalize_article`
- `ArticleService.save_articles`
- `Article` SQLAlchemy model

Silver stores cleaned and normalized articles.

Table:

```text
articles
```

Fields:

```text
id INTEGER PRIMARY KEY
fingerprint STRING UNIQUE
source STRING
title STRING
url STRING
published_at STRING
summary TEXT
content TEXT
topic STRING
risk_score INTEGER
created_at DATETIME
```

Purpose:

- Provide normalized evidence for the API and UI.
- Prevent duplicate article insertion using `fingerprint`.
- Store basic rule-based article risk scores.
- Feed relevant content into ChromaDB.

### 6.3 Vector Memory

Implemented in: `app/rag/vectordb.py`

Transit-relevant Silver articles are promoted into ChromaDB.

Stored metadata:

```text
source
title
url
published_at
topic
```

Stored document text:

```text
title + summary + content
```

Purpose:

- Provide evidence retrieval for RAG.
- Reduce prompt noise by indexing only operationally relevant articles.
- Preserve source metadata for citation and UI display.

### 6.4 Gold Layer

Implemented in:

- `app/api/main.py`
- `AegisAgenticSystem.save_to_gold_layer`

Gold stores final verified risk reports and risk scores.

Table:

```text
gold_risk_index
```

Fields:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
timestamp TEXT
topic TEXT
risk_score INTEGER
full_report TEXT
consensus_reached BOOLEAN
```

Purpose:

- Store final AI-generated consensus reports.
- Enable historical risk timeline visualization.
- Track risk scores by normalized topic.

## 7. Data Flow

### 7.1 News Refresh Flow

```text
POST /api/news/refresh
        ↓
refresh_news_job()
        ↓
NewsFetcher pulls source articles
        ↓
parser.is_relevant_article filters weak or irrelevant articles
        ↓
parser.normalize_article standardizes fields
        ↓
ArticleService.save_articles writes to SQLite
        ↓
ArticleService promotes transit-relevant records to ChromaDB
        ↓
API returns fetched / inserted / duplicate counts
```

### 7.2 Question Answering Flow

```text
POST /api/news/ask
        ↓
VectorDB.search_memory(query, n_results=8)
        ↓
ChromaDB returns candidate article evidence
        ↓
Local re-ranking by similarity, keyword overlap, and recency
        ↓
AegisAgenticSystem.generate_consensus_report()
        ↓
GPT-4o Lead Analyst writes risk assessment
        ↓
Claude Verification Critic checks evidence support
        ↓
Final report saved to gold_risk_index
        ↓
API returns consensus answer
```

### 7.3 Dashboard Risk Timeline Flow

```text
GET /api/news/risk-indices
        ↓
Read gold_risk_index from SQLite
        ↓
Return timestamp, topic, and risk_score
        ↓
Streamlit renders historical risk chart
```

## 8. API Documentation

Base URL:

```text
http://127.0.0.1:8000
```

API prefix:

```text
/api/news
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

### 8.1 Health Check

```http
GET /
```

Response:

```json
{
  "message": "Aegis-Risk API is online",
  "docs": "/docs",
  "status": "ready"
}
```

### 8.2 Refresh News

```http
POST /api/news/refresh
```

Description:

Triggers the news ingestion and Silver/vector promotion pipeline.

Response:

```json
{
  "status": "success",
  "fetched": 18,
  "inserted": 12,
  "duplicates": 6
}
```

Error-style response:

```json
{
  "status": "error",
  "fetched": 0,
  "inserted": 0,
  "duplicates": 0
}
```

### 8.3 Latest News

```http
GET /api/news/latest?topic=oil&limit=10
```

Query parameters:

```text
topic optional string
limit optional integer, min 1, max 50, default 10
```

Response:

```json
{
  "topic": "oil",
  "count": 2,
  "articles": [
    {
      "id": 1,
      "source": "BBC News",
      "title": "Example article title",
      "url": "https://example.com/article",
      "published_at": "2026-04-27T10:00:00Z",
      "summary": "Short article summary",
      "topic": "middle-east-risk",
      "risk_score": 3
    }
  ]
}
```

### 8.4 Ask Risk Question

```http
POST /api/news/ask
```

Request body:

```json
{
  "query": "What is the current risk to oil transit through the Strait of Hormuz?"
}
```

Response:

```json
{
  "query": "What is the current risk to oil transit through the Strait of Hormuz?",
  "answer": "## AGENTIC CONSENSUS REPORT...",
  "verification_status": "Consensus Verified",
  "medallion_tier": "Gold"
}
```

### 8.5 Gold Risk Index

```http
GET /api/news/risk-indices
```

Response:

```json
[
  {
    "time": "2026-04-27T12:34:56.000000",
    "topic": "oil transit",
    "score": 4
  }
]
```

## 9. Relevance Filtering and Scoring

### 9.1 Article-Level Relevance

Implemented in: `parser.is_relevant_article`

The parser uses keyword groups:

- geopolitical keywords: Iran, Israel, Red Sea, Suez, Gaza, Houthis, Strait of Hormuz
- supply-chain keywords: oil, fuel, shipping, tanker, logistics, crude, energy, port
- high-risk keywords: war, conflict, attack, blockade, missile, strike, sanctions
- medium-risk keywords: disruption, delay, shortage, rerouting, volatility, tension

An article is accepted when it has enough geopolitical, supply-chain, or disruption overlap and contains usable text.

### 9.2 Placeholder Rejection

Implemented in: `parser.looks_like_placeholder`

The system rejects weak evidence such as:

- empty or very short text
- `read more`, `subscribe`, `click here`
- repeated low-diversity text
- generic placeholders such as `N/A`, `none`, or `untitled`

### 9.3 Rule-Based Article Risk Score

Implemented in: `parser.compute_risk_score`

The system assigns a simple 0-5 score based on high-risk and medium-risk keyword matches.

This article-level score is separate from the final Gold-layer risk score produced by the LLM consensus workflow.

## 10. RAG Retrieval Design

Implemented in: `VectorDB.search_memory`

Retrieval steps:

1. Query ChromaDB with the user question.
2. Fetch a wider candidate pool than the final requested result count.
3. Format returned documents, metadata, ids, and distances.
4. Calculate keyword overlap between query and article fields.
5. Calculate recency score from `published_at`.
6. Convert Chroma distance into similarity score.
7. Combine scores into a final local ranking.
8. Deduplicate by URL, title, or document id.
9. Return top-ranked evidence objects.

Returned evidence shape:

```json
{
  "id": "article-fingerprint",
  "source": "BBC News",
  "title": "Article title",
  "url": "https://example.com/article",
  "published_at": "2026-04-27T10:00:00Z",
  "topic": "middle-east-risk",
  "summary": "Short text preview",
  "content": "Full indexed content"
}
```

## 11. Multi-Agent Reasoning Design

### 11.1 Lead Analyst

Model:

```text
GPT-4o
```

Responsibilities:

- Use only retrieved context.
- Avoid outside knowledge.
- Produce a concise geopolitical risk assessment.
- Cite claims using `[Source X]`.
- Include current risk factors, mitigating factors, conclusion, recommendations, and numeric risk score.

### 11.2 Verification Critic

Model:

```text
Claude Sonnet 4.6
```

Responsibilities:

- Verify analyst claims against retrieved context.
- Identify supported claims.
- Identify unsupported claims.
- Identify missing evidence.
- Return a final reliability verdict.
- Return a final numeric risk score.

### 11.3 Gold Persistence

After the critic responds, the system:

- combines analyst and critic output
- extracts a final risk score
- normalizes the query into a topic label
- writes the final report to `gold_risk_index`

Topic normalization examples:

```text
"suez disruption"      -> "suez canal"
"hormuz oil transit"  -> "strait of hormuz"
"oil shipping risk"   -> "oil transit"
"iran tanker risk"    -> "iran transit"
```

## 12. Configuration

Environment variables are loaded by `app/core/config.py` from `.env`.

Required or supported variables:

```env
NEWSAPI_KEY=your_newsapi_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
DATABASE_URL=sqlite:///./aegis_risk.db
REFRESH_MINUTES=60
DEFAULT_QUERY=Israel Iran Red Sea Suez oil shipping fuel supply chain
```

Notes:

- `NEWSAPI_KEY` is required for NewsAPI ingestion.
- `OPENAI_API_KEY` is required for the Lead Analyst.
- `ANTHROPIC_API_KEY` is required for the Verification Critic.
- `GROQ_API_KEY` is configured but not part of the main active route in the current implementation.
- `DATABASE_URL` defaults to local SQLite.

## 13. Local Setup

### 13.1 Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 13.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 13.3 Create `.env`

Create a `.env` file in the project root and add the required keys listed in the configuration section.

### 13.4 Start FastAPI

```bash
uvicorn app.api.main:app --reload
```

Backend URLs:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

### 13.5 Start Streamlit

In a second terminal:

```bash
source .venv/bin/activate
streamlit run app/ui/streamlit_app.py
```

Dashboard URL:

```text
http://localhost:8501
```

## 14. Operational Workflow

Typical demo or operator flow:

1. Start FastAPI.
2. Start Streamlit.
3. Trigger news refresh.
4. Load latest evidence for a topic such as `oil`, `iran`, or `red sea`.
5. Ask a risk question.
6. Review the Lead Analyst report.
7. Review the Verification Critic report.
8. Check cited sources.
9. View the Gold-layer risk timeline.

## 15. Failure Modes and Troubleshooting

### 15.1 No Articles Returned

Possible causes:

- Missing `NEWSAPI_KEY`.
- NewsAPI quota exhausted.
- Source RSS endpoint unavailable.
- Relevance filter is too strict for current news.
- Network or SSL request failure.

Recommended checks:

- Confirm `.env` is loaded.
- Check backend logs for `DEBUG NewsAPI status`.
- Try a broader `DEFAULT_QUERY`.
- Inspect raw source fetch counts.

### 15.2 RAG Returns No Context

Possible causes:

- No articles have been promoted to ChromaDB.
- Ingestion has not been run.
- Articles were saved to SQLite but failed vector relevance filtering.
- Query does not match indexed evidence.

Recommended checks:

- Run `POST /api/news/refresh`.
- Check `chroma_db` exists.
- Confirm `ArticleService` logs show `VectorDB upserted`.
- Try a query closer to indexed topics, such as `oil transit`, `hormuz`, or `red sea shipping`.

### 15.3 LLM Agent Fails

Possible causes:

- Missing OpenAI or Anthropic API key.
- Model API error.
- Rate limit or billing issue.
- Empty retrieved context.

Recommended checks:

- Confirm `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.
- Check backend response for `Analyst Agent failed` or `Critic Agent failed`.
- Verify vector retrieval returns evidence before calling the agents.

### 15.4 Gold Timeline Is Empty

Possible causes:

- No successful `/api/news/ask` call has completed.
- Agent workflow failed before saving to Gold.
- SQLite path mismatch.

Recommended checks:

- Ask a question after ingestion.
- Confirm `gold_risk_index` exists in `aegis_risk.db`.
- Call `GET /api/news/risk-indices`.

## 16. Current Limitations

- Risk scoring is partly rule-based and partly LLM-generated; it is not calibrated against external market or incident datasets.
- Source quality depends on available news provider responses.
- Some source pages may block scraping or return partial content.
- The scheduler runs locally and is not yet designed for distributed deployment.
- SQLite is suitable for local demos but should be replaced with PostgreSQL for production.
- ChromaDB persistence is local and should be externalized for multi-user deployment.
- There is no authentication or role-based access control.
- There is no formal evaluation harness for hallucination, citation accuracy, or risk-score stability.
- The LLM workflow depends on third-party model APIs and their availability.

## 17. Production Hardening Recommendations

For a production-grade version, add:

- PostgreSQL for normalized and Gold-layer data.
- Managed vector database or hosted Chroma service.
- Background worker queue such as Celery, RQ, or Dramatiq.
- Centralized logging and monitoring.
- API authentication and dashboard access control.
- Source reliability scoring.
- Incident taxonomy and chokepoint-specific risk models.
- Automated tests for ingestion, parsing, API responses, and RAG output shape.
- Evaluation dataset for claim support and citation grounding.
- Deployment configuration using Docker and environment-specific settings.

## 18. Testing Strategy

Recommended test coverage:

- Unit tests for `clean_text`, `looks_like_placeholder`, `is_relevant_article`, and `normalize_article`.
- Unit tests for `compute_risk_score`.
- Unit tests for article fingerprint and duplicate handling.
- API tests for `/refresh`, `/latest`, `/ask`, and `/risk-indices`.
- Integration test for article save and ChromaDB promotion.
- Mocked LLM tests for the analyst/critic workflow.
- Streamlit smoke test for dashboard rendering.

## 19. Security and Compliance Considerations

- Never commit `.env` or API keys.
- Avoid storing sensitive proprietary data in local SQLite or ChromaDB.
- Treat LLM output as decision support, not an authoritative intelligence product.
- Preserve source URLs and citations for auditability.
- Add authentication before exposing the API beyond local development.
- Add rate limiting before public deployment.

## 20. Future Roadmap

Potential next improvements:

- Chokepoint-specific risk indices for Hormuz, Suez, Bab el-Mandeb, and Red Sea routes.
- Entity extraction for countries, ports, vessels, militant groups, and shipping companies.
- Graph-based relationship mapping between geopolitical actors and infrastructure assets.
- Market data integration for oil prices, shipping rates, and insurance premiums.
- Human analyst feedback loop for correcting model outputs.
- Scheduled report generation.
- Email or Slack alerting for high-risk score changes.
- Dockerized deployment with persistent database and vector volumes.

## 21. Glossary

**Bronze Layer**: raw source data stored before cleaning or transformation.

**Silver Layer**: cleaned, normalized article data used by the application.

**Gold Layer**: final verified risk intelligence outputs and historical risk scores.

**RAG**: retrieval-augmented generation, where the LLM answers using retrieved evidence.

**Vector DB**: database that stores embeddings for semantic search.

**ChromaDB**: local vector database used for evidence retrieval.

**Lead Analyst**: LLM agent that generates the initial risk assessment.

**Verification Critic**: LLM agent that checks whether the analyst's claims are supported by evidence.

**Risk Index**: time-series record of topic-level risk scores generated from final consensus reports.
