# User Playbook

## What AEGIS-RISK Does

AEGIS-RISK / RiskLens AI monitors geopolitical and supply-chain risk signals from open-source news. It focuses on critical infrastructure topics such as oil transit routes, maritime chokepoints, tanker movement, shipping disruption, and energy supply-chain exposure.

The system ingests news, filters for operational relevance, retrieves evidence, and produces a final risk assessment through an analyst -> critic -> revision workflow.

## Who Should Use It

RiskLens AI is intended for:

- risk analysts monitoring geopolitical disruption
- supply-chain and energy analysts tracking maritime exposure
- business stakeholders needing concise evidence-backed briefings
- technical reviewers assessing RAG and LLM workflow quality
- governance stakeholders reviewing auditability and uncertainty handling

It is a decision-support tool, not an autonomous decision-maker.

## How To Run A Risk Query

1. Start the FastAPI backend.
2. Start the Streamlit dashboard.
3. In the sidebar, choose a focus topic such as `oil`, `iran`, `red sea`, or `suez`.
4. Refresh ingestion if you need the latest available source pull.
5. Load Silver evidence for the selected topic.
6. Enter a strategic question in the Consensus Workspace.
7. Run the multi-model consensus workflow.
8. Review the Final Risk Assessment, evidence notes, uncertainty notes, and human review points.

## Pipeline Controls

### Refresh Bronze Pipeline

This fetches raw source material from configured news sources and stores raw records for auditability.

Use this when:

- starting a new demo or analysis session
- the current evidence looks stale
- you want to test ingestion behavior

### Load Silver Evidence

This loads cleaned and normalized articles that match the selected topic.

Use this before asking a question so the RAG workflow has source context.

### Sync Gold Timeline

This loads persisted Gold-layer risk index records for charting historical risk scores.

Use this when:

- comparing current risk against previous assessments
- demoing trend behavior
- validating whether new Gold outputs are being persisted

## How To Interpret Risk Scores

Risk scores use a `1-5` scale:

- `1`: low observed disruption signal
- `2`: guarded or early-warning signal
- `3`: elevated risk with meaningful uncertainty
- `4`: high risk with stronger evidence of disruption
- `5`: severe risk or major disruption signal

Risk scores should be interpreted with the retrieved evidence and uncertainty notes. A score is not a forecast guarantee.

## Reading Evidence And Uncertainty

The final assessment should include:

- `Final Risk Score`
- `Concise Summary`
- `Key Evidence`
- `Uncertainty Notes`
- `Recommended Human Review Points`

Evidence citations such as `[Source 1]` indicate which retrieved source supports a claim. Uncertainty notes identify evidence gaps, ambiguity, weak source coverage, or areas requiring additional validation.

## When To Escalate To Human Review

Escalate when:

- the assessment has weak or missing citations
- uncertainty notes mention missing market, vessel, insurance, or operational data
- the recommendation would affect commercial, safety, legal, or reputational decisions
- sources conflict with each other
- the risk score is high but evidence coverage is narrow
- the output includes caveats about unsupported claims or incomplete verification

## Known Limitations

- Open-source news can be incomplete, delayed, duplicated, or biased.
- Retrieval quality depends on the ingested article set and vector store contents.
- The LLM may still phrase uncertain information too confidently.
- Risk scores are qualitative and should be reviewed before operational use.
- The system does not currently include real-time vessel tracking, market pricing calibration, or formal human approval workflow.
