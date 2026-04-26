# Aegis-Risk: Agentic Geopolitical Risk Monitor

Aegis-Risk is an LLM-powered multi-agent system for real-time geopolitical risk analysis across critical infrastructure domains such as oil transit routes, maritime chokepoints, and global energy supply chains.

The project combines a Medallion-style data pipeline, retrieval-augmented generation, and adversarial multi-model verification to produce evidence-backed risk assessments with source visibility.

## Key Features

- Multi-agent reasoning workflow
  - Lead Analyst: GPT-4o
  - Verification Critic: Claude 4.6
  - Optional Refiner: Groq / Llama-3
- Medallion architecture
  - Bronze: raw ingestion and audit trail
  - Silver: cleaned and structured articles
  - Gold: risk scoring and historical trend tracking
- Geopolitical retrieval focused on oil transit, chokepoints, shipping lanes, and disruption signals
- Evidence-backed outputs tied to source articles
- Streamlit control-center dashboard for operators and demos

## System Overview

Aegis-Risk integrates data engineering, retrieval, and LLM reasoning in one pipeline:

```text
News Sources (NewsAPI, RSS, scraping)
            ↓
        Bronze Layer (raw ingestion)
            ↓
   Cleaning and normalization pipeline
            ↓
        Silver Layer (SQLite)
            ↓
   Relevance filtering (vector gate)
            ↓
        Vector DB (Chroma)
            ↓
   Retrieval-Augmented Generation
            ↓
   Multi-Agent Reasoning Workflow
            ↓
        Gold Layer (risk index)
            ↓
        Streamlit Dashboard
```

## System Architecture

![Aegis-Risk Architecture](diagrams/architechture.png)

## Dashboard Preview

![Aegis-Risk Dashboard](screenshots/dashboard.png)
![Aegis-Risk AI Answers](screenshots/ai_answers.png)
![Aegis-Risk Sources](screenshots/sources.png)

## Run Locally

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root with the required keys:

```env
NEWSAPI_KEY=your_newsapi_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
DATABASE_URL=sqlite:///./aegis_risk.db
REFRESH_MINUTES=60
DEFAULT_QUERY=Israel Iran Red Sea Suez oil shipping fuel supply chain
```

Environment variables are loaded from `app/core/config.py`.

### 4. Start the FastAPI backend

```bash
uvicorn app.api.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

### 5. Start the Streamlit dashboard

Open a second terminal, activate the same environment, then run:

```bash
streamlit run app/ui/streamlit_app.py
```

The dashboard usually opens at:

- `http://localhost:8501`

## Workflow

1. Refresh the Bronze pipeline to ingest and promote news data.
2. Load Silver evidence for a topic such as `oil`, `iran`, or `red sea`.
3. Sync the Gold timeline to visualize historical risk scores.
4. Run a consensus query so the analyst and critic debate the currently loaded evidence.

Core endpoints:

```text
POST /api/news/refresh
GET  /api/news/latest
POST /api/news/ask
GET  /api/news/risk-indices
```

## Dashboard Experience

The Streamlit UI is designed as a dashboard-style control center with:

- a command sidebar for ingestion, evidence loading, and timeline sync
- summary KPI cards for focus topic, timeline risk, consensus grade, and source diversity
- a historical Gold-layer risk chart
- a consensus workspace for analyst and critic outputs
- an evidence feed with source cards and direct links to underlying articles

## Medallion Architecture

### Bronze Layer

- Raw, unmodified article ingestion
- Auditability and reproducibility of upstream data
- News sources including NewsAPI, RSS feeds, and targeted scraping

### Silver Layer

- Cleaned and normalized articles stored in SQLite
- Enriched article metadata such as title, summary, source, timestamp, and content

### Gold Layer

- LLM-generated geopolitical risk assessments
- Time-series risk scoring
- Multi-model consensus output

## Vector Relevance Filtering

Before indexing into ChromaDB, the system uses semantic gating to keep only transit-relevant reporting:

```python
VECTOR_KEYWORDS = [
    "oil tanker", "shipping lane", "oil transit",
    "maritime route", "strait", "chokepoint",
    "blockade", "navy", "pipeline"
]
```

This helps reduce:

- noise pollution
- political-only articles with weak operational relevance
- irrelevant macroeconomic coverage

## Multi-Agent AI System

### Lead Analyst

- Generates the main geopolitical risk report
- Surfaces risk factors, mitigation ideas, recommendations, and a risk score

### Verification Critic

- Validates whether claims are supported by retrieved evidence
- Flags unsupported or weakly grounded reasoning

### Refiner

- Optional cleanup stage for clarity and structure

## Example Output

- Risk score: 3-4 out of 5
- Typical focus areas:
  - Strait of Hormuz disruption risk
  - naval blockades
  - tanker movement constraints

## Project Structure

```text
app/
  api/         FastAPI routes and schemas
  core/        configuration and database setup
  ingestion/   news fetch, parsing, dedupe, scheduler
  models/      SQLAlchemy models
  rag/         vector search and LLM consensus logic
  services/    article retrieval services
  ui/          Streamlit dashboard
```

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Streamlit
- ChromaDB
- OpenAI
- Anthropic
- Groq
- BeautifulSoup
- RSS parsing

## Future Work

- chokepoint-specific scoring for Hormuz, Suez, and Bab el-Mandeb
- real-time streaming ingestion
- graph-based geopolitical entity linking
- quantitative risk calibration using market data

## Author

Sabbir Ahmed  
Research-oriented Data Scientist focused on applied AI, ML systems, and decision-support technologies
