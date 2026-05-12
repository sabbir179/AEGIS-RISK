# Roadmap

This roadmap tracks the production-hardening path for Aegis-Risk / RiskLens AI.

## Phase 0: Repository governance

- Add project license.
- Add roadmap and changelog.
- Clarify repository documentation baseline.

## Phase 1: Logging and error handling

- Introduce consistent structured logging.
- Improve exception handling around ingestion, retrieval, and model calls.
- Add clear operational error messages without exposing sensitive details.

## Phase 2: Tests

- Add focused unit tests for core data processing and retrieval behavior.
- Add integration tests for API workflows.
- Establish a repeatable test command for local and CI use.

## Phase 3: Actor-critic revision loop

- Formalize the analyst, critic, and revision flow.
- Add traceable intermediate outputs.
- Improve unsupported-claim handling and answer revision quality.

## Phase 4: Evaluation framework

- Define evaluation datasets and expected-answer rubrics.
- Measure retrieval relevance, claim support, and risk-score consistency.
- Track evaluation results across prompt and model changes.

## Phase 5: Deployment polish

- Harden configuration and secret handling.
- Add deployment documentation.
- Improve production readiness for the FastAPI and Streamlit services.
