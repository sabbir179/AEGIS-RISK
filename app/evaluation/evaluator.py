import logging
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


EXPECTED_SECTIONS = [
    "Final Risk Score",
    "Concise Summary",
    "Key Evidence",
    "Uncertainty Notes",
    "Recommended Human Review Points",
]


@dataclass
class EvaluationResult:
    status: str
    score: float
    checks: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RiskAssessmentEvaluator:
    """
    Lightweight evaluator for final RAG/LLM risk assessments.

    The evaluator is intentionally deterministic and makes no external calls.
    It checks output structure, citations, risk-score validity, critic/revision
    signals, and basic groundedness against retrieved evidence metadata.
    """

    risk_score_pattern = re.compile(
        r"final\s+risk\s+score[^0-9]{0,20}([0-9]+)",
        flags=re.IGNORECASE,
    )
    citation_pattern = re.compile(r"\[Source\s+(\d+)\]", flags=re.IGNORECASE)

    def evaluate(
        self,
        final_output: str | None,
        retrieved_evidence: list[dict[str, Any]] | None = None,
        audit: dict[str, Any] | None = None,
        stage_latencies: dict[str, float] | None = None,
    ) -> EvaluationResult:
        started_at = time.perf_counter()
        final_text = (final_output or "").strip()
        evidence = retrieved_evidence or []
        audit_data = audit or {}

        risk_score = self._extract_risk_score(final_text)
        citation_ids = self._extract_citation_ids(final_text)
        expected_section_checks = {
            self._section_key(section): self._contains_section(final_text, section)
            for section in EXPECTED_SECTIONS
        }

        has_uncertainty_notes = expected_section_checks["has_uncertainty_notes"]
        has_human_review_points = expected_section_checks["has_recommended_human_review_points"]
        has_critic_feedback = self._has_critic_feedback(audit_data)
        has_revised_output = bool(
            final_text
            and final_text != str(audit_data.get("initial_analyst_assessment", "")).strip()
        )
        groundedness_score = self._groundedness_score(final_text, evidence)

        checks = {
            "has_final_answer": bool(final_text),
            "has_valid_risk_score": risk_score is not None,
            "risk_score_in_range": risk_score is not None and 1 <= risk_score <= 5,
            "has_citations": bool(citation_ids),
            "citation_count": len(citation_ids),
            "retrieved_evidence_count": len(evidence),
            "citation_coverage_ratio": self._citation_coverage_ratio(citation_ids, len(evidence)),
            "groundedness_score": groundedness_score,
            "has_uncertainty_notes": has_uncertainty_notes,
            "has_human_review_points": has_human_review_points,
            "has_critic_feedback": has_critic_feedback,
            "has_revised_output": has_revised_output,
            **expected_section_checks,
        }

        warnings, failures = self._build_findings(checks)
        status = self._status_from_findings(warnings, failures)
        score = self._score_checks(checks)

        metadata = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "retrieved_evidence_count": len(evidence),
            "risk_score": risk_score,
            "citation_ids": citation_ids,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
        }
        if stage_latencies:
            metadata["stage_latencies_ms"] = {
                str(key): round(float(value), 3)
                for key, value in stage_latencies.items()
            }

        result = EvaluationResult(
            status=status,
            score=score,
            checks=checks,
            warnings=warnings,
            failures=failures,
            metadata=metadata,
        )
        logger.debug("Risk assessment evaluation result: %s", result.to_dict())
        return result

    def _extract_risk_score(self, text: str) -> int | None:
        match = self.risk_score_pattern.search(text)
        if not match:
            return None

        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _extract_citation_ids(self, text: str) -> list[int]:
        ids = {
            int(match)
            for match in self.citation_pattern.findall(text)
            if match.isdigit()
        }
        return sorted(ids)

    def _contains_section(self, text: str, section: str) -> bool:
        return bool(re.search(rf"(^|\n)#+\s*{re.escape(section)}\b|{re.escape(section)}\s*:", text, re.IGNORECASE))

    def _section_key(self, section: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", section.lower()).strip("_")
        return f"has_{normalized}"

    def _citation_coverage_ratio(self, citation_ids: list[int], evidence_count: int) -> float:
        if evidence_count <= 0:
            return 0.0
        valid_citations = [citation_id for citation_id in citation_ids if 1 <= citation_id <= evidence_count]
        return round(len(valid_citations) / evidence_count, 3)

    def _groundedness_score(self, text: str, evidence: list[dict[str, Any]]) -> float:
        if not text or not evidence:
            return 0.0

        lowered_text = text.lower()
        matches = 0

        for item in evidence:
            title = str(item.get("title", "")).strip().lower()
            source = str(item.get("source", "")).strip().lower()
            if title and title in lowered_text:
                matches += 1
                continue
            if source and source in lowered_text:
                matches += 1

        if matches:
            return round(matches / len(evidence), 3)

        citation_count = len(self._extract_citation_ids(text))
        return round(min(citation_count, len(evidence)) / len(evidence), 3)

    def _has_critic_feedback(self, audit: dict[str, Any]) -> bool:
        feedback = audit.get("critic_feedback")
        if isinstance(feedback, dict):
            return any(bool(value) for value in feedback.values())
        return bool(feedback)

    def _build_findings(self, checks: dict[str, Any]) -> tuple[list[str], list[str]]:
        warnings = []
        failures = []

        if not checks["has_final_answer"]:
            failures.append("Final answer is missing.")
        if not checks["has_valid_risk_score"]:
            failures.append("Final risk score is missing or not numeric.")
        elif not checks["risk_score_in_range"]:
            failures.append("Final risk score is outside the expected 1-5 range.")

        for section in EXPECTED_SECTIONS:
            key = self._section_key(section)
            if not checks[key]:
                warnings.append(f"Expected section missing: {section}.")

        if not checks["has_citations"]:
            warnings.append("No source citations were found.")
        if checks["groundedness_score"] == 0:
            warnings.append("Final answer has no obvious evidence grounding signal.")
        if not checks["has_uncertainty_notes"]:
            warnings.append("Uncertainty notes are missing.")
        if not checks["has_human_review_points"]:
            warnings.append("Recommended human review points are missing.")
        if not checks["has_critic_feedback"]:
            warnings.append("Critic feedback was not available for evaluation.")
        if not checks["has_revised_output"]:
            warnings.append("Revised output signal was not detected.")

        return warnings, failures

    def _status_from_findings(self, warnings: list[str], failures: list[str]) -> str:
        if failures:
            return "fail"
        if warnings:
            return "warning"
        return "pass"

    def _score_checks(self, checks: dict[str, Any]) -> float:
        weighted_checks = [
            ("has_final_answer", 0.16),
            ("has_valid_risk_score", 0.16),
            ("risk_score_in_range", 0.12),
            ("has_final_risk_score", 0.08),
            ("has_concise_summary", 0.08),
            ("has_key_evidence", 0.08),
            ("has_uncertainty_notes", 0.08),
            ("has_recommended_human_review_points", 0.08),
            ("has_citations", 0.08),
            ("has_critic_feedback", 0.04),
            ("has_revised_output", 0.04),
        ]
        score = sum(weight for key, weight in weighted_checks if checks.get(key))
        return round(min(score, 1.0), 3)


def evaluate_risk_assessment(
    final_output: str | None,
    retrieved_evidence: list[dict[str, Any]] | None = None,
    audit: dict[str, Any] | None = None,
    stage_latencies: dict[str, float] | None = None,
) -> dict[str, Any]:
    return RiskAssessmentEvaluator().evaluate(
        final_output=final_output,
        retrieved_evidence=retrieved_evidence,
        audit=audit,
        stage_latencies=stage_latencies,
    ).to_dict()
