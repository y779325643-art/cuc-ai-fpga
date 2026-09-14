import json
import hashlib

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.model_gateway_provenance import write_model_gateway_provenance
from sr2fpga_agent.runner import PlannedSample, RunnerConfig, _generation_event_sink
from sr2fpga_agent.model_gateway_provenance import read_verified_model_gateway_provenance
from sr2fpga_agent.provider_seed_capability import (
    ProviderSeedProbeObservation,
    write_development_provider_seed_capability,
)


@pytest.mark.parametrize("mismatch", [None, "provider_model", "gateway_base_url_sha256",
    "provider_adapter", "provider_system_fingerprint", "seed_forwarding_status"])
def test_call_capability_binding_rejects_identity_drift(tmp_path, mismatch):
    store = ArtifactStore(tmp_path / "store")
    capability = write_development_provider_seed_capability(
        store, provider_adapter="openai_compatible", provider_model="fake-model",
        gateway_base_url="https://example.test/v1",
        protocol={"prompt_sha256": "1" * 64, "seed": 17, "temperature": 0.1,
                  "max_tokens": 32, "repetitions": 2,
                  "probe_implementation_sha256": "2" * 64},
        documentation_status="deterministic_documented",
        documentation_snapshot_sha256="3" * 64,
        documentation_source_url_sha256="4" * 64,
        documentation_review={"review_type": "independent_review",
                              "reviewer_provenance_sha256": "5" * 64},
        observations=[ProviderSeedProbeObservation(
            status="completed", output_sha256="6" * 64,
            output_size_bytes=1, system_fingerprint="fp-fake",
        )] * 2,
    )
    provider = {
        "provider_adapter": "openai_compatible", "provider_model": "fake-model",
        "gateway_base_url_sha256": hashlib.sha256(b"https://example.test/v1").hexdigest(),
        "requested_decoding_seed": 17, "seed_forwarding_status": "forwarded",
        "deterministic_seed_control": "supported",
        "provider_system_fingerprint": "fp-fake", "system_fingerprint_status": "reported",
    }
    if mismatch:
        provider[mismatch] = "drift"
    def write():
        return write_model_gateway_provenance(
            store, episode_id="call-binding", analysis_population="excluded",
            method_condition="M4", seed_control_evidence_ref=capability,
            event={"event": "model_call_finished", "call_id": 0, "stage": "req2his",
                   "operation": "chat", "status": "completed",
                   "provider_response_provenance": provider},
        )
    if mismatch:
        with pytest.raises(ValueError):
            write()
    else:
        result = read_verified_model_gateway_provenance(store, write())
        assert result["seed_control_evidence_ref"] == capability.to_dict()
        assert result["g3_accepted"] is False
        forged = dict(result, provenance_id="mgp-" + "0" * 32)
        ref = store.put_validated_json("forged", forged, contract_key="model_gateway_provenance")
        with pytest.raises(ValueError, match="identity mismatch"):
            read_verified_model_gateway_provenance(store, ref)


def test_writer_persists_registered_non_authoritative_artifact(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = write_model_gateway_provenance(
        store,
        episode_id="episode-1",
        analysis_population="excluded",
        method_condition="M4",
        event={
            "event": "model_call_finished",
            "call_id": 0,
            "stage": "two_stage",
            "operation": "chat",
            "status": "completed",
            "provider_response_provenance": {
                "provider_adapter": "openai_compatible",
                "provider_model": "model-a",
                "gateway_base_url_sha256": "a" * 64,
                "requested_decoding_seed": 17,
                "seed_forwarding_status": "forwarded",
                "deterministic_seed_control": "requested_unverified",
                "provider_system_fingerprint": "fp_backend",
                "system_fingerprint_status": "reported",
            },
        },
    )

    assert reference is not None
    payload = json.loads(store.read_verified(reference))
    assert payload["call_id"] == 0
    assert payload["requested_decoding_seed"] == 17
    assert payload["seed_forwarding_status"] == "forwarded"
    assert payload["deterministic_seed_control"] == "requested_unverified"
    assert payload["official_authority"] is False
    assert payload["pass_credit_authority"] is False
    assert payload["g3_accepted"] is False
    assert payload["g4b_authorized"] is False


def test_writer_ignores_non_model_call_events(tmp_path) -> None:
    assert write_model_gateway_provenance(
        ArtifactStore(tmp_path / "store"),
        episode_id="episode-1",
        analysis_population="development",
        method_condition="M0",
        event={"event": "planner_started"},
    ) is None


def test_failed_provider_calls_do_not_persist_raw_messages():
    events = []
    budget = ModelCallBudget(1, event_sink=events.append)
    call, started = budget.reserve("req2his", "chat", 1)
    budget.finish(call, "req2his", "chat", started, output_chars=0,
                  error=RuntimeError("PRIVATE-PROVIDER-KEY-CANARY"))
    assert "PRIVATE-PROVIDER-KEY-CANARY" not in json.dumps(events)
    assert "PRIVATE-PROVIDER-KEY-CANARY" not in json.dumps(budget.summary())
    assert events[-1]["error_type"] == "RuntimeError"
    assert events[-1]["error"] == "provider_call_failed"


def test_budgeted_calls_keep_zero_based_ids_in_runner_provenance(tmp_path) -> None:
    class _Client:
        def stream_chat(self, messages):
            return "{}"

        def consume_transport_attempt_count(self):
            return 1

        def consume_token_usage(self):
            return {"input_tokens": 2, "output_tokens": 1, "cached_tokens": 0}

        def consume_response_provenance(self):
            return {
                "provider_adapter": "openai_compatible",
                "provider_model": "model-a",
                "gateway_base_url_sha256": "a" * 64,
                "requested_decoding_seed": 17,
                "seed_forwarding_status": "forwarded",
                "deterministic_seed_control": "requested_unverified",
                "provider_system_fingerprint": "fp_backend",
                "system_fingerprint_status": "reported",
            }

    store = ArtifactStore(tmp_path / "store")
    events_path = tmp_path / "events.jsonl"
    config = RunnerConfig(
        dataset_root=tmp_path / "dataset",
        export_root=tmp_path / "exports",
        run_root=tmp_path / "runs",
        provider="deepseek-his-v12",
        repair_provider="none",
        max_attempts=1,
        refresh_exports=False,
        line_b_targets={},
        tasks=[],
    )
    sample = PlannedSample(
        sample_id="sample-1",
        source="deepseek-his-v12",
        task_type="counter",
        width=8,
        project_name="counter-8",
        requirement="Design an 8-bit counter.",
        failure_origin="natural_llm",
        method_condition="M4",
        analysis_population="development",
        decoding_seed=17,
    )
    budget = ModelCallBudget(
        2,
        event_sink=_generation_event_sink(
            events_path,
            sample,
            config,
            artifact_store=store,
        ),
    )
    client = budget.client(_Client(), "req2his")

    client.stream_chat([{"role": "user", "content": "first"}])
    client.for_stage("his2project").stream_chat(
        [{"role": "user", "content": "second"}]
    )

    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    completed = [event for event in events if event["event"] == "model_call_finished"]
    assert [event["call_id"] for event in completed] == [0, 1]
    assert [call["call_id"] for call in budget.summary()["calls"]] == [0, 1]
    assert len({event["model_gateway_provenance_ref"]["key"] for event in completed}) == 2
    for event in completed:
        payload = json.loads(
            store.read_verified(event["model_gateway_provenance_ref"]["key"])
        )
        assert payload["call_id"] == event["call_id"]
