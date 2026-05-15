import json

import pytest

from app.assistants.loader import (
    ALLOWED_ASSISTANT_STATUSES,
    DEFAULT_ASSISTANT_ID,
    AssistantRegistry,
    AssistantRegistryError,
    get_default_assistant,
    load_assistant,
    load_assistants,
)
from app.prompts import load_prompts


INITIAL_ASSISTANT_IDS = {
    "risk_analyst",
    "executive_briefing",
    "compliance_review",
    "market_intelligence",
}


def test_assistant_registry_loads_successfully():
    assistants = load_assistants()

    assert len(assistants) >= 4
    assert all(assistant["status"] in ALLOWED_ASSISTANT_STATUSES for assistant in assistants)


def test_all_initial_assistant_definitions_exist():
    assistant_ids = {assistant["assistant_id"] for assistant in load_assistants()}

    assert INITIAL_ASSISTANT_IDS.issubset(assistant_ids)


def test_get_assistant_by_valid_id():
    assistant = load_assistant("executive_briefing")

    assert assistant is not None
    assert assistant["assistant_id"] == "executive_briefing"
    assert assistant["persona"] == "Senior Management / Executive"


def test_missing_assistant_id_returns_none():
    assert load_assistant("missing_assistant") is None
    assert load_assistant("") is None


def test_default_assistant_is_risk_analyst():
    assistant = get_default_assistant()

    assert DEFAULT_ASSISTANT_ID == "risk_analyst"
    assert assistant["assistant_id"] == "risk_analyst"


def test_assistant_prompt_ids_exist_in_prompt_library():
    prompt_ids = {prompt["prompt_id"] for prompt in load_prompts()}

    for assistant in load_assistants():
        assert set(assistant["prompt_ids"]).issubset(prompt_ids)


def test_assistant_filters_by_persona_and_status():
    assistants = load_assistants(
        persona="Risk Analyst",
        status="approved",
    )

    assert len(assistants) == 1
    assert assistants[0]["assistant_id"] == "risk_analyst"


def test_required_metadata_validation(tmp_path):
    bad_registry = tmp_path / "bad_registry.json"
    bad_registry.write_text(
        json.dumps({"assistants": [{"assistant_id": "incomplete"}]}),
        encoding="utf-8",
    )

    with pytest.raises(AssistantRegistryError, match="missing required metadata"):
        AssistantRegistry(bad_registry).load_all()


def test_allowed_status_validation(tmp_path):
    bad_assistant = {
        "assistant_id": "bad_status",
        "name": "Bad Status Assistant",
        "persona": "Tester",
        "purpose": "Validate bad status handling.",
        "use_case": "Testing",
        "status": "live",
        "owner": "RiskLens AI",
        "prompt_ids": ["critic_review"],
        "output_style": "test",
        "expected_sections": ["Summary"],
        "version": "1.0.0",
        "last_updated": "2026-05-15",
    }
    bad_registry = tmp_path / "bad_status_registry.json"
    bad_registry.write_text(json.dumps({"assistants": [bad_assistant]}), encoding="utf-8")

    with pytest.raises(AssistantRegistryError, match="invalid status"):
        AssistantRegistry(bad_registry).load_all()


def test_missing_prompt_reference_fails_validation(tmp_path):
    bad_assistant = {
        "assistant_id": "missing_prompt_ref",
        "name": "Missing Prompt Reference",
        "persona": "Tester",
        "purpose": "Validate missing prompt handling.",
        "use_case": "Testing",
        "status": "testing",
        "owner": "RiskLens AI",
        "prompt_ids": ["does_not_exist"],
        "output_style": "test",
        "expected_sections": ["Summary"],
        "version": "1.0.0",
        "last_updated": "2026-05-15",
    }
    bad_registry = tmp_path / "bad_prompt_registry.json"
    bad_registry.write_text(json.dumps({"assistants": [bad_assistant]}), encoding="utf-8")

    with pytest.raises(AssistantRegistryError, match="references missing prompt_ids"):
        AssistantRegistry(bad_registry).load_all()
