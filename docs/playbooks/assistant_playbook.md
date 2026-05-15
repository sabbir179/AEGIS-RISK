# Assistant Playbook

## Purpose

RiskLens AI includes a persona-based assistant registry in `app/assistants/registry.json`. Assistants define role-specific guidance, expected output style, lifecycle status, and recommended prompt IDs from the prompt library.

The registry supports enterprise AI enablement by making assistant behavior cataloged, reviewable, and reusable.

## Available Assistants

### Risk Analyst Assistant

- `assistant_id`: `risk_analyst`
- Persona: Risk Analyst
- Purpose: detailed evidence-based risk assessment
- Output style: structured, analytical, evidence-heavy
- Use when: a user needs a full risk assessment with citations, uncertainty, and review points.

Example questions:

- "Assess current risk to oil transit through the Strait of Hormuz."
- "What are the main shipping disruption signals in the Red Sea?"
- "How exposed are tanker routes to current Middle East tensions?"

### Executive Briefing Assistant

- `assistant_id`: `executive_briefing`
- Persona: Senior Management / Executive
- Purpose: short decision-focused summary for senior stakeholders
- Output style: concise, commercial impact, decision points
- Use when: the audience needs business impact and next actions rather than detailed source analysis.

Example questions:

- "Summarize the commercial implications of current oil transit risk."
- "What should senior leadership know about Red Sea shipping disruption?"
- "What decisions may be needed this week?"

### Compliance Review Assistant

- `assistant_id`: `compliance_review`
- Persona: Compliance / Risk Control
- Purpose: auditability, uncertainty, unsupported claims, escalation points
- Output style: cautious, evidence-focused, governance-oriented
- Use when: the user needs to review traceability, evidence coverage, and escalation risk.

Example questions:

- "Review the assessment for unsupported claims and evidence gaps."
- "What should be escalated for human approval?"
- "Is the current assessment audit-ready?"

### Market Intelligence Assistant

- `assistant_id`: `market_intelligence`
- Persona: Market Intelligence Analyst
- Purpose: trends, commercial implications, monitoring signals
- Output style: trend-focused, signal-oriented, business impact
- Use when: the user needs monitoring signals and commercial trend interpretation.

Example questions:

- "What market signals should we monitor for oil transit disruption?"
- "Which trends suggest rising risk in maritime logistics?"
- "What commercial indicators could confirm or weaken this assessment?"

## How Assistants Connect To Prompts

Each assistant references prompt IDs from `app/prompts/library.json`. For example, the Risk Analyst Assistant references:

- `risk_analyst_initial_assessment`
- `critic_review`
- `analyst_revision`

The assistant loader validates that every referenced prompt ID exists. This keeps persona definitions aligned with governed prompt assets.

## Lifecycle Statuses

Assistant statuses are:

- `draft`: early concept, not ready for workflow use
- `testing`: under evaluation with representative examples
- `approved`: reviewed and suitable for the current workflow
- `deprecated`: retained for audit history but no longer recommended

## Expected Output Styles

- Risk Analyst Assistant: detailed, cited, structured, evidence-heavy
- Executive Briefing Assistant: short, decision-focused, commercially relevant
- Compliance Review Assistant: cautious, traceable, governance-oriented
- Market Intelligence Assistant: trend-focused, signal-oriented, business impact focused

## Governance Notes

Assistant changes should be reviewed with:

- linked prompt versions
- expected output sections
- evaluation results
- known limitations
- owner approval

Changing an assistant should not silently change production behavior without review.
