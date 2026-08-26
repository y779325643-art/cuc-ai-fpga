import json

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.model_gateway_provenance import write_model_gateway_provenance


def test_writer_persists_registered_non_authoritative_artifact(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = write_model_gateway_provenance(
        store,
        episode_id="episode-1",
        analysis_population="excluded",
        method_condition="M4",
        event={
            "event": "model_call_finished",
            "call_id": 1,
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
