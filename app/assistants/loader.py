import json
import logging
from pathlib import Path
from typing import Any

from app.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)

ASSISTANT_REGISTRY_PATH = Path(__file__).with_name("registry.json")
DEFAULT_ASSISTANT_ID = "risk_analyst"

ALLOWED_ASSISTANT_STATUSES = {"draft", "testing", "approved", "deprecated"}

REQUIRED_ASSISTANT_FIELDS = {
    "assistant_id",
    "name",
    "persona",
    "purpose",
    "use_case",
    "status",
    "owner",
    "prompt_ids",
    "output_style",
    "expected_sections",
    "version",
    "last_updated",
}


class AssistantRegistryError(Exception):
    """Raised when assistant registry loading or validation fails."""


class AssistantRegistry:
    def __init__(
        self,
        registry_path: str | Path | None = None,
        prompt_loader: PromptLoader | None = None,
    ):
        self.registry_path = Path(registry_path) if registry_path else ASSISTANT_REGISTRY_PATH
        self.prompt_loader = prompt_loader or PromptLoader()

    def load_all(
        self,
        persona: str | None = None,
        use_case: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        assistants = self._read_registry()
        self.validate_assistants(assistants)

        if persona:
            assistants = [assistant for assistant in assistants if assistant.get("persona") == persona]
        if use_case:
            normalized_use_case = use_case.lower()
            assistants = [
                assistant
                for assistant in assistants
                if normalized_use_case in str(assistant.get("use_case", "")).lower()
            ]
        if status:
            assistants = [assistant for assistant in assistants if assistant.get("status") == status]

        return assistants

    def load_by_id(self, assistant_id: str) -> dict[str, Any] | None:
        safe_assistant_id = str(assistant_id or "").strip()
        if not safe_assistant_id:
            logger.warning("Assistant lookup requested with an empty assistant_id")
            return None

        for assistant in self.load_all():
            if assistant.get("assistant_id") == safe_assistant_id:
                return assistant

        logger.warning("Assistant not found: %s", safe_assistant_id)
        return None

    def require_by_id(self, assistant_id: str) -> dict[str, Any]:
        assistant = self.load_by_id(assistant_id)
        if not assistant:
            raise AssistantRegistryError(f"Assistant not found: {assistant_id}")
        return assistant

    def get_default(self) -> dict[str, Any]:
        return self.require_by_id(DEFAULT_ASSISTANT_ID)

    def validate_assistants(self, assistants: list[dict[str, Any]]) -> None:
        prompt_ids = {prompt["prompt_id"] for prompt in self.prompt_loader.load_all()}
        seen_ids = set()

        for assistant in assistants:
            self.validate_assistant(assistant, prompt_ids)
            assistant_id = assistant["assistant_id"]
            if assistant_id in seen_ids:
                raise AssistantRegistryError(f"Duplicate assistant_id found: {assistant_id}")
            seen_ids.add(assistant_id)

    def validate_assistant(self, assistant: dict[str, Any], prompt_ids: set[str] | None = None) -> None:
        missing_fields = sorted(REQUIRED_ASSISTANT_FIELDS - set(assistant))
        if missing_fields:
            raise AssistantRegistryError(
                f"Assistant is missing required metadata fields: {', '.join(missing_fields)}"
            )

        status = assistant.get("status")
        if status not in ALLOWED_ASSISTANT_STATUSES:
            raise AssistantRegistryError(
                f"Assistant '{assistant.get('assistant_id')}' has invalid status: {status}"
            )

        assistant_prompt_ids = assistant.get("prompt_ids")
        if not isinstance(assistant_prompt_ids, list) or not all(isinstance(item, str) for item in assistant_prompt_ids):
            raise AssistantRegistryError(
                f"Assistant '{assistant.get('assistant_id')}' prompt_ids must be a list of strings"
            )

        expected_sections = assistant.get("expected_sections")
        if not isinstance(expected_sections, list) or not all(isinstance(item, str) for item in expected_sections):
            raise AssistantRegistryError(
                f"Assistant '{assistant.get('assistant_id')}' expected_sections must be a list of strings"
            )

        if prompt_ids is not None:
            missing_prompt_ids = sorted(set(assistant_prompt_ids) - prompt_ids)
            if missing_prompt_ids:
                raise AssistantRegistryError(
                    f"Assistant '{assistant.get('assistant_id')}' references missing prompt_ids: "
                    f"{', '.join(missing_prompt_ids)}"
                )

    def _read_registry(self) -> list[dict[str, Any]]:
        try:
            with self.registry_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except FileNotFoundError as exc:
            logger.exception("Assistant registry file not found: %s", self.registry_path)
            raise AssistantRegistryError(f"Assistant registry file not found: {self.registry_path}") from exc
        except json.JSONDecodeError as exc:
            logger.exception("Assistant registry JSON is invalid: %s", exc)
            raise AssistantRegistryError("Assistant registry JSON is invalid") from exc

        assistants = payload.get("assistants") if isinstance(payload, dict) else None
        if not isinstance(assistants, list):
            raise AssistantRegistryError("Assistant registry must contain an 'assistants' list")

        return assistants


def load_assistants(
    persona: str | None = None,
    use_case: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    return AssistantRegistry().load_all(persona=persona, use_case=use_case, status=status)


def load_assistant(assistant_id: str) -> dict[str, Any] | None:
    return AssistantRegistry().load_by_id(assistant_id)


def get_default_assistant() -> dict[str, Any]:
    return AssistantRegistry().get_default()
