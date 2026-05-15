import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROMPT_LIBRARY_PATH = Path(__file__).with_name("library.json")

ALLOWED_PROMPT_STATUSES = {"draft", "testing", "approved", "deprecated"}

REQUIRED_PROMPT_FIELDS = {
    "prompt_id",
    "name",
    "version",
    "persona",
    "use_case",
    "status",
    "owner",
    "last_updated",
    "required_inputs",
    "expected_output",
    "template",
}


class PromptLibraryError(Exception):
    """Raised when prompt library loading or validation fails."""


class PromptLoader:
    def __init__(self, library_path: str | Path | None = None):
        self.library_path = Path(library_path) if library_path else PROMPT_LIBRARY_PATH

    def load_all(
        self,
        persona: str | None = None,
        use_case: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        prompts = self._read_library()
        self.validate_prompts(prompts)

        if persona:
            prompts = [prompt for prompt in prompts if prompt.get("persona") == persona]
        if use_case:
            normalized_use_case = use_case.lower()
            prompts = [
                prompt
                for prompt in prompts
                if normalized_use_case in str(prompt.get("use_case", "")).lower()
            ]
        if status:
            prompts = [prompt for prompt in prompts if prompt.get("status") == status]

        return prompts

    def load_by_id(self, prompt_id: str) -> dict[str, Any] | None:
        safe_prompt_id = str(prompt_id or "").strip()
        if not safe_prompt_id:
            logger.warning("Prompt lookup requested with an empty prompt_id")
            return None

        for prompt in self.load_all():
            if prompt.get("prompt_id") == safe_prompt_id:
                return prompt

        logger.warning("Prompt not found: %s", safe_prompt_id)
        return None

    def require_by_id(self, prompt_id: str) -> dict[str, Any]:
        prompt = self.load_by_id(prompt_id)
        if not prompt:
            raise PromptLibraryError(f"Prompt not found: {prompt_id}")
        return prompt

    def validate_prompts(self, prompts: list[dict[str, Any]]) -> None:
        seen_ids = set()
        for prompt in prompts:
            self.validate_prompt(prompt)
            prompt_id = prompt["prompt_id"]
            if prompt_id in seen_ids:
                raise PromptLibraryError(f"Duplicate prompt_id found: {prompt_id}")
            seen_ids.add(prompt_id)

    def validate_prompt(self, prompt: dict[str, Any]) -> None:
        missing_fields = sorted(REQUIRED_PROMPT_FIELDS - set(prompt))
        if missing_fields:
            raise PromptLibraryError(
                f"Prompt is missing required metadata fields: {', '.join(missing_fields)}"
            )

        status = prompt.get("status")
        if status not in ALLOWED_PROMPT_STATUSES:
            raise PromptLibraryError(
                f"Prompt '{prompt.get('prompt_id')}' has invalid status: {status}"
            )

        required_inputs = prompt.get("required_inputs")
        if not isinstance(required_inputs, list) or not all(isinstance(item, str) for item in required_inputs):
            raise PromptLibraryError(
                f"Prompt '{prompt.get('prompt_id')}' required_inputs must be a list of strings"
            )

    def _read_library(self) -> list[dict[str, Any]]:
        try:
            with self.library_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except FileNotFoundError as exc:
            logger.exception("Prompt library file not found: %s", self.library_path)
            raise PromptLibraryError(f"Prompt library file not found: {self.library_path}") from exc
        except json.JSONDecodeError as exc:
            logger.exception("Prompt library JSON is invalid: %s", exc)
            raise PromptLibraryError("Prompt library JSON is invalid") from exc

        prompts = payload.get("prompts") if isinstance(payload, dict) else None
        if not isinstance(prompts, list):
            raise PromptLibraryError("Prompt library must contain a 'prompts' list")

        return prompts


def load_prompts(
    persona: str | None = None,
    use_case: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    return PromptLoader().load_all(persona=persona, use_case=use_case, status=status)


def load_prompt(prompt_id: str) -> dict[str, Any] | None:
    return PromptLoader().load_by_id(prompt_id)
