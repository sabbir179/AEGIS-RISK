from app.evaluation import RiskAssessmentEvaluator, evaluate_risk_assessment


VALID_REPORT = """
## Final Risk Assessment

Final Risk Score: 3

### Concise Summary
Oil transit risk is elevated based on tanker disruption reporting from Source A. [Source 1]

### Key Evidence
- Source A reports tanker disruption affecting maritime transit. [Source 1]
- Source B reports rerouting pressure in the region. [Source 2]

### Uncertainty Notes
- Market pricing impact is not quantified in the retrieved evidence.

### Recommended Human Review Points
- Validate current vessel movement and insurance data before operational action.
"""


EVIDENCE = [
    {"title": "Tanker disruption affecting maritime transit", "source": "Source A"},
    {"title": "Rerouting pressure in the region", "source": "Source B"},
]


AUDIT = {
    "initial_analyst_assessment": "Initial draft with Risk Score: 4",
    "critic_feedback": {
        "unsupported_claims": [],
        "missing_evidence": ["No market pricing evidence"],
        "uncertainty_areas": ["Limited source coverage"],
        "risk_score_concerns": ["Moderate score is better supported"],
        "suggested_improvements": ["Add uncertainty notes"],
    },
}


def test_evaluator_passes_valid_final_assessment():
    result = RiskAssessmentEvaluator().evaluate(
        final_output=VALID_REPORT,
        retrieved_evidence=EVIDENCE,
        audit=AUDIT,
        stage_latencies={"retrieval": 12.2, "revision": 30.8},
    )

    assert result.status == "pass"
    assert result.checks["has_valid_risk_score"] is True
    assert result.checks["risk_score_in_range"] is True
    assert result.checks["citation_count"] == 2
    assert result.checks["has_critic_feedback"] is True
    assert result.metadata["retrieved_evidence_count"] == 2
    assert result.metadata["stage_latencies_ms"]["retrieval"] == 12.2


def test_evaluator_warns_when_citations_and_audit_are_missing():
    report = VALID_REPORT.replace("[Source 1]", "").replace("[Source 2]", "")

    result = RiskAssessmentEvaluator().evaluate(
        final_output=report,
        retrieved_evidence=EVIDENCE,
        audit={},
    )

    assert result.status == "warning"
    assert result.checks["has_citations"] is False
    assert "No source citations were found." in result.warnings
    assert "Critic feedback was not available for evaluation." in result.warnings


def test_evaluator_fails_when_final_answer_is_missing():
    result = RiskAssessmentEvaluator().evaluate(
        final_output="",
        retrieved_evidence=EVIDENCE,
        audit=AUDIT,
    )

    assert result.status == "fail"
    assert "Final answer is missing." in result.failures
    assert "Final risk score is missing or not numeric." in result.failures


def test_evaluator_fails_when_risk_score_is_out_of_range():
    report = VALID_REPORT.replace("Final Risk Score: 3", "Final Risk Score: 8")

    result = RiskAssessmentEvaluator().evaluate(
        final_output=report,
        retrieved_evidence=EVIDENCE,
        audit=AUDIT,
    )

    assert result.status == "fail"
    assert result.checks["risk_score_in_range"] is False
    assert "Final risk score is outside the expected 1-5 range." in result.failures


def test_evaluate_risk_assessment_returns_dict_shape():
    result = evaluate_risk_assessment(
        final_output=VALID_REPORT,
        retrieved_evidence=EVIDENCE,
        audit=AUDIT,
    )

    assert result["status"] == "pass"
    assert "checks" in result
    assert "metadata" in result
