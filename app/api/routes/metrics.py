import logging

from fastapi import APIRouter

from app.metrics import summarize_usage_events

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
def metrics_summary():
    """Returns lightweight adoption and usage metrics summary."""
    try:
        return summarize_usage_events()
    except Exception as exc:
        logger.exception("Usage metrics summary failed: %s", exc)
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "most_used_assistant": None,
            "most_common_topic": None,
            "average_risk_score": None,
            "evaluation_status_counts": {},
            "average_evidence_count": None,
            "average_latency_ms": None,
        }
