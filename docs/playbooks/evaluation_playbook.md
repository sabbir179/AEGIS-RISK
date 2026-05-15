# Evaluation Playbook

## What The Evaluation Module Measures

The evaluation module in `app/evaluation/` provides lightweight local checks for final RAG/LLM risk assessments. It does not call OpenAI, Anthropic, NewsAPI, RSS, embeddings, or ChromaDB.

It is designed for pre-launch testing, regression checks, demo readiness, and future production monitoring.

## Metrics

### Groundedness

Checks whether the final answer shows evidence grounding signals. The current implementation looks for source references, cited evidence, and overlap with retrieved evidence metadata.

### Citation / Evidence Coverage

Checks whether the final output includes references such as `[Source 1]` and counts how many distinct sources are cited. It also compares citations against the number of retrieved evidence items.

### Structured Output Validity

Checks whether expected sections are present:

- Final Risk Score
- Concise Summary
- Key Evidence
- Uncertainty Notes
- Recommended Human Review Points

### Risk Score Validity

Checks whether:

- a final risk score is present
- the score is numeric
- the score falls within `1-5`

### Critic / Revision Quality Signals

Checks whether:

- critic feedback exists in the audit payload
- revised final output exists
- uncertainty notes exist
- recommended human review points exist

### Warnings And Failures

The evaluator produces:

- `pass`: required fields and citations are present
- `warning`: output is usable but has gaps such as missing citations or missing uncertainty notes
- `fail`: final answer or valid risk score is missing, or the score is outside the expected range

## Running Evaluation Tests

Run:

```bash
pytest tests/test_evaluator.py
```

Run the full suite:

```bash
pytest
```

## Interpreting Results

### Pass

A pass means the output has required sections, a valid risk score, citation signals, and useful governance signals.

### Warning

A warning means the output may still be useful, but should be reviewed. Common warning causes include:

- missing citations
- weak evidence grounding
- missing uncertainty notes
- missing human review points
- missing critic feedback

### Fail

A fail means the output should not be used as-is. Common failure causes include:

- no final answer
- missing risk score
- non-numeric risk score
- risk score outside `1-5`

## Low-Confidence Output

Low-confidence output should trigger human review. It may indicate incomplete evidence, weak retrieval results, prompt drift, or model formatting failure.

## Pre-Launch And Post-Launch Monitoring

Before launch, evaluation helps compare prompt versions, assistant outputs, and regression behavior.

After launch, evaluation can support:

- quality monitoring
- prompt release gates
- assistant lifecycle reviews
- incident analysis
- governance reporting

The current evaluator is intentionally lightweight. Future improvements could include curated benchmark datasets, human labels, retrieval recall metrics, and scheduled evaluation runs.
