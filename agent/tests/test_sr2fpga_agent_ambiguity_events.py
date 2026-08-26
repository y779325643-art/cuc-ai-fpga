import pytest

from sr2fpga_agent.ambiguity_events import (
    AmbiguityAuditEventInterceptor,
    DownstreamEventIntercepted,
    validate_ambiguity_audit_events,
)


def _interceptor():
    return AmbiguityAuditEventInterceptor(
        audit_run_id="audit-001",
        manifest_sha256="a" * 64,
    )


def test_interceptor_records_attempt_without_invoking_callback() -> None:
    interceptor = _interceptor()
    calls = []
    interceptor.phase_a_started("case-001")
    interceptor.phase_a_completed(
        "case-001",
        execution_status="completed",
        predicted_disposition="needs_clarification",
        counters={
            "model_calls": 0,
            "tool_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "wall_time_ms": 1.0,
        },
        infrastructure_status="available",
    )

    with pytest.raises(DownstreamEventIntercepted, match="project_generator_call"):
        interceptor.attempt_downstream(
            "case-001",
            "project_generator_call",
            lambda: calls.append("called"),
        )

    artifact = interceptor.build_artifact(phase_a_audit_sha256="b" * 64)
    validate_ambiguity_audit_events(artifact)
    assert calls == []
    assert artifact["events"][-1]["enforcement_status"] == "intercepted"


def test_event_validator_rejects_non_contiguous_sequence() -> None:
    interceptor = _interceptor()
    interceptor.phase_a_started("case-001")
    artifact = interceptor.build_artifact(phase_a_audit_sha256="b" * 64)
    artifact["events"][0]["sequence"] = 3
    with pytest.raises(ValueError, match="contiguous and ordered"):
        validate_ambiguity_audit_events(artifact)
