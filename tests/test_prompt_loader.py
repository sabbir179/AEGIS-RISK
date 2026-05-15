import json

import pytest

from app.prompts.loader import (
    ALLOWED_PROMPT_STATUSES,
    PromptLibraryError,
    PromptLoader,
    load_prompt,
    load_prompts,
)


INITIAL_PROMPT_IDS = {
    "risk_analyst_initial_assessment",
    "critic_review",
    "analyst_revision",
    "executive_briefing_summary",
    "compliance_review_summary",
}


def test_load_prompt_library_successfully():
    prompts = load_prompts()

    assert len(prompts) >= 5
    assert all(prompt["status"] in ALLOWED_PROMPT_STATUSES for prompt in prompts)


def test_load_prompt_by_valid_id():
    prompt = load_prompt("critic_review")

    assert prompt is not None
    assert prompt["prompt_id"] == "critic_review"
    assert prompt["persona"] == "verification_critic"
    assert "unsupported_claims" in prompt["expected_output"]


def test_missing_prompt_id_returns_none():
    assert load_prompt("missing_prompt") is None
    assert load_prompt("") is None


def test_five_initial_prompt_entries_exist():
    prompt_ids = {prompt["prompt_id"] for prompt in load_prompts()}

    assert INITIAL_PROMPT_IDS.issubset(prompt_ids)


def test_prompt_filters_by_persona_and_status():
    approved_analyst_prompts = load_prompts(
        persona="lead_geopolitical_risk_analyst",
        status="approved",
    )

    assert approved_analyst_prompts
    assert all(prompt["persona"] == "lead_geopolitical_risk_analyst" for prompt in approved_analyst_prompts)
    assert all(prompt["status"] == "approved" for prompt in approved_analyst_prompts)


def test_required_metadata_validation(tmp_path):
    bad_library = tmp_path / "bad_library.json"
    bad_library.write_text(
        json.dumps({"prompts": [{"prompt_id": "incomplete"}]}),
        encoding="utf-8",
    )

    with pytest.raises(PromptLibraryError, match="missing required metadata"):
        PromptLoader(bad_library).load_all()


def test_allowed_status_validation(tmp_path):
    bad_prompt = {
        "prompt_id": "bad_status",
        "name": "Bad Status",
        "version": "1.0.0",
        "persona": "tester",
        "use_case": "Validate bad status handling.",
        "status": "live",
        "owner": "RiskLens AI",
        "last_updated": "2026-05-15",
        "required_inputs": ["input"],
        "expected_output": "Output",
        "template": "Template {{input}}",
    }
    bad_library = tmp_path / "bad_status_library.json"
    bad_library.write_text(json.dumps({"prompts": [bad_prompt]}), encoding="utf-8")

    with pytest.raises(PromptLibraryError, match="invalid status"):
        PromptLoader(bad_library).load_all()
