# AI Enablement Playbooks

This folder contains practical operating guidance for AEGIS-RISK / RiskLens AI. The playbooks are written for business users, technical reviewers, and AI governance stakeholders who need to understand how to use, evaluate, maintain, and scale the system responsibly.

## Playbook Index

- [User Playbook](user_playbook.md): how analysts and operators use the dashboard, evidence workflow, risk scores, uncertainty notes, and human review points.
- [Assistant Playbook](assistant_playbook.md): available persona-based assistants, when to use each assistant, expected output styles, and assistant lifecycle statuses.
- [Prompt Governance Playbook](prompt_governance_playbook.md): prompt metadata, versioning, lifecycle management, review process, and auditability practices.
- [Evaluation Playbook](evaluation_playbook.md): evaluation metrics, pass/warning/fail interpretation, and how evaluation supports pre-launch and post-launch monitoring.
- [Production Readiness Playbook](production_readiness_playbook.md): current hardening controls, known production gaps, and recommended next improvements.

## Purpose

These playbooks help position RiskLens AI as an enterprise AI enablement platform rather than a one-off demo. They document how the implemented FastAPI, Streamlit, RAG, prompt library, assistant registry, evaluation module, and analyst-critic-revision workflow should be operated and governed.

The project is production-oriented, but not presented as fully production-ready. The playbooks call out implemented controls and remaining gaps clearly.
