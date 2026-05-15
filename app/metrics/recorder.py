import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_METRICS_PATH = Path("data/usage_metrics.jsonl")
METRICS_PATH_ENV = "USAGE_METRICS_PATH"

ALLOWED_EVENT_FIELDS = {
    "timestamp",
    "status",
    "assistant_id",
    "focus_topic",
    "evidence_count",
    "final_risk_score",
    "verification_state",
    "evaluation_status",
    "citation_count",
    "uncertainty_note_count",
    "human_review_point_count",
    "has_critic_warning",
    "has_revision_signal",
    "latency_ms",
    "error_type",
}

STRING_FIELD_LIMITS = {
    "assistant_id": 80,
    "focus_topic": 120,
    "verification_state": 80,
    "evaluation_status": 40,
    "error_type": 80,
}

ALLOWED_STATUSES = {"success", "failed"}


class UsageMetricsRecorder:
    def __init__(self, metrics_path: str | Path | None = None):
        configured_path = metrics_path or os.getenv(METRICS_PATH_ENV)
        self.metrics_path = Path(configured_path) if configured_path else DEFAULT_METRICS_PATH

    def record_event(self, event: dict[str, Any]) -> bool:
        safe_event = self._sanitize_event(event)

        try:
            self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with self.metrics_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(safe_event, sort_keys=True) + "\n")
            logger.info("Recorded usage metrics event: %s", safe_event.get("status"))
            return True
        except Exception as exc:
            logger.exception("Failed to record usage metrics event: %s", exc)
            return False

    def load_events(self) -> list[dict[str, Any]]:
        if not self.metrics_path.exists():
            logger.debug("Usage metrics file does not exist yet: %s", self.metrics_path)
            return []

        events = []
        try:
            with self.metrics_path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        event = json.loads(stripped)
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed usage metrics row %s", line_number)
                        continue
                    if isinstance(event, dict):
                        events.append(self._sanitize_event(event))
                    else:
                        logger.warning("Skipping non-object usage metrics row %s", line_number)
        except Exception as exc:
            logger.exception("Failed to load usage metrics events: %s", exc)
            return []

        return events

    def summarize(self) -> dict[str, Any]:
        return summarize_events(self.load_events())

    def _sanitize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        safe_event = {
            key: value
            for key, value in (event or {}).items()
            if key in ALLOWED_EVENT_FIELDS
        }
        safe_event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        safe_event.setdefault("status", "success")
        if safe_event["status"] not in ALLOWED_STATUSES:
            safe_event["status"] = "failed"

        for string_key, limit in STRING_FIELD_LIMITS.items():
            if string_key in safe_event and safe_event[string_key] is not None:
                safe_event[string_key] = str(safe_event[string_key]).strip()[:limit]

        for numeric_key in [
            "evidence_count",
            "final_risk_score",
            "citation_count",
            "uncertainty_note_count",
            "human_review_point_count",
            "latency_ms",
        ]:
            if numeric_key in safe_event and safe_event[numeric_key] is not None:
                safe_event[numeric_key] = _coerce_number(safe_event[numeric_key])

        for bool_key in ["has_critic_warning", "has_revision_signal"]:
            if bool_key in safe_event:
                safe_event[bool_key] = bool(safe_event[bool_key])

        return safe_event


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(events)
    successful_runs = sum(1 for event in events if event.get("status") == "success")
    failed_runs = sum(1 for event in events if event.get("status") == "failed")

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "most_used_assistant": _most_common(events, "assistant_id"),
        "most_common_topic": _most_common(events, "focus_topic"),
        "average_risk_score": _average(events, "final_risk_score"),
        "evaluation_status_counts": dict(Counter(
            event.get("evaluation_status", "unknown")
            for event in events
            if event.get("evaluation_status")
        )),
        "average_evidence_count": _average(events, "evidence_count"),
        "average_latency_ms": _average(events, "latency_ms"),
    }


def record_usage_event(event: dict[str, Any], metrics_path: str | Path | None = None) -> bool:
    return UsageMetricsRecorder(metrics_path=metrics_path).record_event(event)


def load_usage_events(metrics_path: str | Path | None = None) -> list[dict[str, Any]]:
    return UsageMetricsRecorder(metrics_path=metrics_path).load_events()


def summarize_usage_events(metrics_path: str | Path | None = None) -> dict[str, Any]:
    return UsageMetricsRecorder(metrics_path=metrics_path).summarize()


def _coerce_number(value: Any) -> int | float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return int(number) if number.is_integer() else number


def _average(events: list[dict[str, Any]], key: str) -> float | None:
    values = [
        float(event[key])
        for event in events
        if isinstance(event.get(key), (int, float))
    ]
    if not values:
        return None
    return round(mean(values), 3)


def _most_common(events: list[dict[str, Any]], key: str) -> str | None:
    values = [
        str(event[key])
        for event in events
        if event.get(key)
    ]
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]
