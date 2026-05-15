# Production Readiness Playbook

## Purpose

This playbook summarizes the current production-hardening controls in AEGIS-RISK / RiskLens AI and identifies remaining gaps before a real production deployment.

## Implemented Controls

### Logging

The project uses Python logging instead of print statements. Logs are intended to help diagnose ingestion, vector store, API, and LLM workflow failures.

### Error Handling

The project includes error handling for:

- NewsAPI and RSS failures
- malformed article payloads
- duplicate articles
- database read/write errors
- vector store failures
- LLM generation and revision failures
- FastAPI endpoint errors
- Streamlit user-facing errors

### Tests

Pytest tests cover parsing, dedupe, vector response handling, LLM workflow behavior, API paths, prompt loading, assistant loading, and evaluation logic.

### Evaluation

The evaluation module checks groundedness signals, citation coverage, output structure, risk-score validity, critic/revision signals, warnings, and failures.

### Adoption And Usage Metrics

The metrics module records lightweight operational metadata in `data/usage_metrics.jsonl` by default, or another path set with `USAGE_METRICS_PATH`. It is designed for privacy-conscious monitoring and does not store personal data, API keys, full prompts, full LLM responses, full conversations, or raw article bodies.

Tracked fields include run status, assistant ID, focus topic, evidence count, final risk score, evaluation status, citation count, uncertainty note count, human review point count, latency, and error category. Local metrics files are ignored by git and can be reset by deleting the JSONL file.

### Prompt Library

Prompts are stored outside core business logic in `app/prompts/library.json` with metadata, versions, lifecycle status, owners, required inputs, expected outputs, and templates.

### Assistant Registry

Persona-based assistants are stored in `app/assistants/registry.json`. Assistant definitions reference prompt IDs and include lifecycle metadata.

### RAG Grounding

The system retrieves evidence from vector memory and instructs LLMs to cite retrieved sources. The evaluator checks for citation and evidence coverage signals.

### Actor-Critic-Revision Workflow

The workflow generates an analyst draft, runs critic review, and revises once before producing the final user-facing assessment.

### Human Review Controls

Final outputs include uncertainty notes and recommended human review points. These are intended to prevent over-reliance on automated assessments.

## Known Production Gaps

The project is production-oriented but not fully production-ready. Remaining gaps include:

- no formal authentication or authorization
- no deployment pipeline or infrastructure-as-code
- no centralized observability stack
- no human approval workflow
- no formal incident response process
- no scheduled evaluation jobs
- no labeled benchmark dataset
- no real-time vessel, market, or insurance data calibration
- no secrets manager integration
- no role-based access control
- limited load and resilience testing

## Recommended Future Improvements

### Operational Hardening

- add CI/CD with automated test and evaluation gates
- add structured JSON logs for production deployment
- add monitoring dashboards and alerting
- add retry/backoff policies where appropriate
- add environment-specific configuration

### Governance

- add prompt and assistant approval records
- add human review workflow for high-risk outputs
- add release notes for prompt and assistant changes
- store evaluation results for audit history

### RAG Quality

- create curated benchmark queries
- measure retrieval precision and recall
- add source freshness checks
- add deduplication quality reports

### Security

- add authentication
- protect API keys with a secrets manager
- restrict admin operations
- review data retention and source licensing

## Production Readiness Positioning

RiskLens AI demonstrates the architecture and governance patterns expected in enterprise AI enablement. It should be described as a hardened prototype or production-oriented reference implementation until the remaining operational, security, and governance controls are completed.
