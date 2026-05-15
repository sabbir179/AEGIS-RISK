# Prompt Governance Playbook

## What The Prompt Library Is

The prompt library is a JSON-based catalog of reusable prompt definitions stored in `app/prompts/library.json`. Prompt metadata and template text are separated from core application logic so prompt changes are easy to review, version, test, and audit.

## Required Prompt Metadata

Each prompt should include:

- `prompt_id`
- `name`
- `version`
- `persona`
- `use_case`
- `status`
- `owner`
- `last_updated`
- `required_inputs`
- `expected_output`
- `template`
- optional `evaluation_notes`

The prompt loader validates required fields and allowed lifecycle statuses.

## Versioning

Use semantic-style versions such as `1.0.0`, `1.1.0`, or `2.0.0`.

Recommended practice:

- patch version for wording fixes that do not change behavior
- minor version for output structure or instruction improvements
- major version for material behavior changes or new workflow assumptions

## Lifecycle

### Draft

Use `draft` for early prompt ideas. Draft prompts should not be used in production workflows.

### Testing

Use `testing` when a prompt is being evaluated against representative examples. Testing prompts should have documented expected outputs and known risks.

### Approved

Use `approved` when a prompt has been reviewed and has acceptable evaluation results for its intended use case.

### Deprecated

Use `deprecated` when a prompt is retained for audit history but should no longer be selected for new workflows.

## Review Process For Prompt Changes

Prompt changes should be reviewed like code changes:

1. Update the prompt version.
2. Document the reason for the change.
3. Confirm required metadata is complete.
4. Run prompt loader tests.
5. Run relevant RAG/LLM evaluation tests or offline examples.
6. Review output quality, citations, uncertainty, and risk-score behavior.
7. Promote from `testing` to `approved` only when results are acceptable.

## Evaluation Support For Approval

Evaluation results should support prompt approval by checking:

- groundedness
- citation coverage
- structured output validity
- valid risk score
- uncertainty notes
- human review points
- critic/revision quality signals

Low-confidence or warning-heavy results should keep a prompt in `testing`.

## Safely Deprecating Prompts

To deprecate a prompt:

1. Change status to `deprecated`.
2. Keep the prompt definition in the library for audit history.
3. Add or reference a replacement prompt where appropriate.
4. Confirm assistants no longer depend on the deprecated prompt unless intentionally retained for legacy behavior.

## Auditability

Prompt governance supports auditability by making prompt behavior explicit and reviewable. A reviewer should be able to answer:

- what prompt was used
- what version was used
- who owns it
- what inputs it expects
- what output it is expected to produce
- whether it is draft, testing, approved, or deprecated
