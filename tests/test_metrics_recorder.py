import json

from app.metrics import UsageMetricsRecorder, load_usage_events, record_usage_event, summarize_usage_events


def test_record_and_load_usage_event(tmp_path):
    metrics_path = tmp_path / "usage_metrics.jsonl"
    event = {
        "status": "success",
        "assistant_id": "risk_analyst",
        "focus_topic": "oil transit",
        "evidence_count": 12,
        "final_risk_score": 4,
        "verification_state": "Consensus Verified",
        "evaluation_status": "pass",
        "citation_count": 3,
        "uncertainty_note_count": 1,
        "human_review_point_count": 2,
        "has_critic_warning": False,
        "has_revision_signal": True,
        "latency_ms": 3200,
    }

    assert record_usage_event(event, metrics_path=metrics_path) is True
    events = load_usage_events(metrics_path=metrics_path)

    assert len(events) == 1
    assert events[0]["assistant_id"] == "risk_analyst"
    assert events[0]["final_risk_score"] == 4


def test_missing_metrics_file_returns_empty_list(tmp_path):
    metrics_path = tmp_path / "missing.jsonl"

    assert load_usage_events(metrics_path=metrics_path) == []
    assert summarize_usage_events(metrics_path=metrics_path)["total_runs"] == 0


def test_malformed_metrics_rows_are_skipped(tmp_path):
    metrics_path = tmp_path / "usage_metrics.jsonl"
    metrics_path.write_text(
        "\n".join([
            json.dumps({"status": "success", "assistant_id": "risk_analyst"}),
            "{bad json",
            json.dumps(["not", "an", "object"]),
        ]),
        encoding="utf-8",
    )

    events = load_usage_events(metrics_path=metrics_path)

    assert len(events) == 1
    assert events[0]["assistant_id"] == "risk_analyst"


def test_summary_metrics_calculate_averages_and_counts(tmp_path):
    metrics_path = tmp_path / "usage_metrics.jsonl"
    recorder = UsageMetricsRecorder(metrics_path=metrics_path)
    recorder.record_event({
        "status": "success",
        "assistant_id": "risk_analyst",
        "focus_topic": "oil",
        "evidence_count": 10,
        "final_risk_score": 4,
        "evaluation_status": "pass",
        "latency_ms": 3000,
    })
    recorder.record_event({
        "status": "success",
        "assistant_id": "risk_analyst",
        "focus_topic": "oil",
        "evidence_count": 20,
        "final_risk_score": 5,
        "evaluation_status": "warning",
        "latency_ms": 5000,
    })
    recorder.record_event({
        "status": "failed",
        "assistant_id": "executive_briefing",
        "focus_topic": "suez",
        "evaluation_status": "fail",
    })

    summary = summarize_usage_events(metrics_path=metrics_path)

    assert summary["total_runs"] == 3
    assert summary["successful_runs"] == 2
    assert summary["failed_runs"] == 1
    assert summary["most_used_assistant"] == "risk_analyst"
    assert summary["most_common_topic"] == "oil"
    assert summary["average_risk_score"] == 4.5
    assert summary["average_evidence_count"] == 15
    assert summary["average_latency_ms"] == 4000
    assert summary["evaluation_status_counts"] == {
        "pass": 1,
        "warning": 1,
        "fail": 1,
    }


def test_no_personal_data_fields_are_stored(tmp_path):
    metrics_path = tmp_path / "usage_metrics.jsonl"
    record_usage_event(
        {
            "status": "success",
            "assistant_id": "risk_analyst",
            "query": "full user query should not be stored",
            "user_email": "person@example.com",
            "api_key": "secret",
            "prompt": "full prompt should not be stored",
        },
        metrics_path=metrics_path,
    )

    event = load_usage_events(metrics_path=metrics_path)[0]

    assert "query" not in event
    assert "user_email" not in event
    assert "api_key" not in event
    assert "prompt" not in event
