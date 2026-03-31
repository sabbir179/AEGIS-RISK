# AEGIS-RISK: LLM-Powered Risk Intelligence & Monitoring System

## Overview

AEGIS-RISK is an end-to-end applied AI system that transforms real-time geopolitical and supply-chain news into structured, decision-ready risk intelligence using Large Language Models (LLMs).

The system ingests live news, processes and deduplicates content, applies prompt-engineered LLM reasoning, and produces structured outputs including risk scores, drivers, summaries, and monitoring signals—surfaced through an interactive dashboard.

This project is positioned as a **research-oriented prototype for AI-assisted decision support**, exploring how LLMs can be used beyond text generation for structured reasoning and operational intelligence.

---

## Problem Statement

Modern risk assessment systems face key limitations:

- Heavy reliance on structured datasets and static rules
- Limited ability to process unstructured, real-time information
- High dependence on manual expert interpretation
- Poor scalability in rapidly evolving geopolitical contexts

### Goal

To investigate whether LLMs can:

- Interpret unstructured news data
- Extract meaningful risk signals
- Generate consistent and structured risk assessments
- Support decision-making in dynamic environments

---

## System Capabilities

AEGIS-RISK provides a full pipeline for real-time risk intelligence:

- Ingests live geopolitical and supply-chain news
- Deduplicates and preprocesses incoming articles
- Applies LLM-based reasoning to assess risk
- Generates structured outputs:
  - Risk level (Low / Medium / High)
  - Risk score (numeric)
  - Key risk drivers
  - Strategic implications
  - Recommended watchpoints
- Aggregates multiple articles into system-level insights
- Provides an interactive dashboard for monitoring and analysis

---

## Architecture Overview

### Pipeline

News Sources → Ingestion → Deduplication → Parsing → Prompt Engineering → LLM Inference → Output Structuring → Risk Scoring → Dashboard & Analytics

---

## Architecture Diagram

```mermaid
flowchart LR

A[News Sources] --> B[Ingestion Layer]
B --> B1[News Fetcher]
B --> B2[Deduplication]
B --> B3[Parser]

B --> C[Preprocessing]

C --> D[Prompt Engineering]

D --> E[LLM Inference Engine]

E --> F[Output Structuring]

F --> G[Risk Scoring Engine]

G --> H[Database Storage]

H --> I[Analytics & Aggregation]

I --> J[Dashboard UI (Streamlit)]

H --> K[Vector DB (Chroma)]
K --> E

style E fill:#f9f,stroke:#333,stroke-width:2px
style J fill:#bbf,stroke:#333,stroke-width:2px
style K fill:#bfb,stroke:#333,stroke-width:2px
```

---

## System Components

### 1. Ingestion Layer (`ingestion/`)

- `news_fetcher.py` – Fetches live news data
- `dedupe.py` – Removes duplicate articles
- `parser.py` – Extracts and structures content
- `scheduler.py` – Automates periodic ingestion

### 2. Core Infrastructure (`core/`)

- `config.py` – Configuration management
- `database.py` – Storage and persistence layer

### 3. LLM & Retrieval (`rag/`)

- `llm_answer.py` – LLM interaction and reasoning logic
- `vectordb.py` – Vector storage for retrieval (RAG-ready)

### 4. API Layer (`api/`)

- `routes/` – API endpoints
- `schemas/` – Data validation and structure
- `main.py` – API entry point

### 5. Services (`services/`)

- `article_service.py` – Business logic for processing articles

### 6. Data Models (`models/`)

- `article.py` – Article schema and structure

### 7. User Interface (`ui/`)

- `streamlit_app.py` – Interactive dashboard for monitoring risk insights

### 8. Storage

- `aegis_risk.db` – SQLite database
- `chroma_db/` – Vector database for embeddings

---

## Key Features

### LLM-Based Risk Reasoning

- Converts unstructured news into structured intelligence
- Uses prompt engineering to guide consistent outputs

### Structured Outputs

- Risk classification (Low / Medium / High)
- Risk scoring
- Key drivers and explanations

### Real-Time Monitoring

- Live news ingestion
- Refreshable dashboard

### Analytical Dashboard

- Risk distribution (High / Medium / Low)
- Average risk score
- Top risk articles
- Trend visualisation

### Modular Architecture

- Clean separation of ingestion, processing, and inference
- Easily extensible for future features (RAG, agents)

---

## Example Outputs

The system produces:

- Overall risk assessment summaries
- Article-level risk scores
- Key risk drivers (geopolitical, economic, operational)
- Recommended watchpoints

Additionally:

- Aggregated metrics (average risk score)
- Risk distribution across articles
- Visual dashboards for monitoring trends

---

## Engineering Design Principles

### Modularity

- Clear separation between ingestion, inference, and UI

### Reproducibility

- Structured pipelines and deterministic workflows where possible

### Scalability (Conceptual)

- Designed to integrate with streaming data and APIs

### Maintainability

- Clean project structure with isolated components

---

## Research Perspective

This project explores:

- LLMs for structured reasoning tasks
- Reliability and consistency of AI-generated assessments
- Converting unstructured text into decision-ready intelligence

It represents early-stage work in:

- Generative AI applications
- AI-assisted decision support systems
- Agent-like reasoning workflows over streaming data

---

## Limitations

- LLM outputs may vary across runs
- Limited quantitative evaluation framework
- Not production-ready (research prototype)

---

## Future Work

- Retrieval-Augmented Generation (RAG) integration
- Agentic workflows with iterative reasoning
- Feedback loops for self-improving predictions
- Benchmark-based evaluation metrics
- Domain-specific fine-tuning

---

## Tech Stack

- Python
- FastAPI
- Streamlit
- SQLite
- ChromaDB (vector database)
- LLM APIs (e.g., OpenAI)
- Pandas / NumPy

---

## Installation & Setup

```bash
# Clone repository
git clone https://github.com/your-username/AEGIS-RISK.git
cd AEGIS-RISK

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

---

## Running the System

### Start API

```bash
python app/api/main.py
```

### Run Dashboard

```bash
streamlit run app/ui/streamlit_app.py
```

---

## Repository Structure

```
app/
 ├── api/
 ├── core/
 ├── ingestion/
 ├── models/
 ├── rag/
 ├── services/
 ├── ui/

chroma_db/
aegis_risk.db
README.md
requirements.txt
```

---

## Positioning

AEGIS-RISK is an **applied AI system** that demonstrates:

- End-to-end LLM pipeline design
- Real-time data ingestion and processing
- Structured reasoning using generative AI
- Decision-support system development

This project reflects early-stage capabilities in:

- Generative AI
- Applied machine learning systems
- AI-driven risk intelligence

---

## Author

Sabbir Ahmed  
Research-oriented Data Scientist focused on applied AI, ML systems, and decision-support technologies
