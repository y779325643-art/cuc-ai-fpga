import copy
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.provider_seed_capability import (
    ProviderSeedProbeObservation,
    load_development_provider_seed_capability,
    require_paired_confirmatory_seed_capability,
    write_development_provider_seed_capability,
)


def _protocol(repetitions: int = 3) -> dict:
    return {
        "prompt_sha256": "1" * 64,
        "seed": 17,
        "temperature": 0.1,
        "max_tokens": 32,
        "repetitions": repetitions,
        "probe_implementation_sha256": "2" * 64,
    }


def _review(review_type: str = "self_reviewed_development") -> dict:
    return {
        "review_type": review_type,
        "reviewer_provenance_sha256": "3" * 64,
    }


def _completed(
    output_sha256: str = "b" * 64,
    fingerprint: str | None = "fp-a",
) -> ProviderSeedProbeObservation:
    return ProviderSeedProbeObservation(
        status="completed",
        output_sha256=output_sha256,
        system_fingerprint=fingerprint,
        input_tokens=8,
        output_tokens=4,
        cached_tokens=0,
        output_size_bytes=15,
    )


def _write(
    tmp_path,
    *,
    documentation_status: str,
    observations: list[ProviderSeedProbeObservation],
    review_type: str = "self_reviewed_development",
):
    store = ArtifactStore(tmp_path / "store")
    ref = write_development_provider_seed_capability(
        store,
        provider_adapter="openai_compatible",
        provider_model="frozen-model",
        gateway_base_url="https://api.example/v1",
        protocol=_protocol(len(observations)),
        documentation_status=documentation_status,
        documentation_snapshot_sha256="a" * 64,
        documentation_source_url_sha256="c" * 64,
        documentation_review=_review(review_type),
        observations=observations,
    )
    return store, ref, json.loads(store.read_verified(ref))


def test_best_effort_documented_probe_remains_ineligible(tmp_path) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="best_effort_documented",
        observations=[_completed(), _completed(), _completed()],
    )

    assert payload["probe_status"] == "complete"
    assert payload["exact_output_match"] is True
    assert payload["seed_control_classification"] == "best_effort_observed"
    assert payload["paired_confirmatory_eligible"] is False
    assert payload["g3_accepted"] is False


def test_undocumented_seed_with_matching_outputs_stays_unverified(tmp_path) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="seed_undocumented",
        observations=[_completed(), _completed(), _completed()],
    )

    assert payload["seed_control_classification"] == "unverified"
    assert payload["paired_confirmatory_eligible"] is False
    assert "seed_not_documented" in payload["limitations"]


def test_output_mismatch_is_fail_closed(tmp_path) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="deterministic_documented",
        review_type="independent_review",
        observations=[_completed(), _completed("c" * 64), _completed()],
    )

    assert payload["seed_control_classification"] == "nonrepeatable_observed"
    assert payload["paired_confirmatory_eligible"] is False
    assert "output_mismatch" in payload["limitations"]


@pytest.mark.parametrize(
    ("fingerprints", "expected_status", "expected_limitation"),
    (
        (("fp-a", None, "fp-a"), "missing", "fingerprint_missing"),
        (("fp-a", "fp-b", "fp-a"), "inconsistent", "fingerprint_inconsistent"),
    ),
)
def test_backend_identity_gap_is_not_misclassified_as_output_nonrepeatability(
    tmp_path, fingerprints, expected_status, expected_limitation
) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="deterministic_documented",
        review_type="independent_review",
        observations=[_completed(fingerprint=value) for value in fingerprints],
    )

    assert payload["exact_output_match"] is True
    assert payload["fingerprint_status"] == expected_status
    assert payload["seed_control_classification"] == "backend_identity_unverified"
    assert expected_limitation in payload["limitations"]
    assert "output_mismatch" not in payload["limitations"]
    assert payload["paired_confirmatory_eligible"] is False


def test_cli_style_self_review_cannot_form_positive_candidate(tmp_path) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="deterministic_documented",
        observations=[_completed(), _completed(), _completed()],
    )

    assert payload["seed_control_classification"] == "unverified"
    assert payload["paired_confirmatory_eligible"] is False
    assert "independent_documentation_review_required" in payload["limitations"]
    with pytest.raises(ValueError, match="independent documentation review"):
        require_paired_confirmatory_seed_capability(
            payload,
            provider_adapter="openai_compatible",
            provider_model="frozen-model",
            gateway_base_url="https://api.example/v1",
        )


def test_synthetic_independent_review_fixture_can_pass_development_guard(
    tmp_path,
) -> None:
    store, ref, payload = _write(
        tmp_path,
        documentation_status="deterministic_documented",
        review_type="independent_review",
        observations=[_completed(), _completed(), _completed()],
    )
    manifest = tmp_path / "capability.json"
    manifest.write_bytes(store.read_verified(ref))
    loaded = load_development_provider_seed_capability(str(manifest))

    require_paired_confirmatory_seed_capability(
        loaded,
        provider_adapter="openai_compatible",
        provider_model="frozen-model",
        gateway_base_url="https://api.example/v1",
    )
    assert payload["paired_confirmatory_eligible"] is True
    assert payload["official_outcome"] is False
    assert payload["g3_accepted"] is False
    assert payload["g4b_authorized"] is False


def test_loader_recomputes_every_persisted_summary_field(tmp_path) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="deterministic_documented",
        review_type="independent_review",
        observations=[_completed(), _completed(), _completed()],
    )
    mutations = {
        "capability_profile_id": "seedcap-" + "f" * 32,
        "probe_protocol_sha256": "f" * 64,
        "requested_decoding_seed": 18,
        "planned_repetitions": 4,
        "completed_repetitions": 2,
        "failed_repetitions": 1,
        "failure_categories": ["unknown"],
        "probe_status": "partial",
        "output_sha256s": ["d" * 64] * 3,
        "system_fingerprints": ["fp-b"] * 3,
        "exact_output_match": False,
        "fingerprint_match": False,
        "provider_token_usage_status": "partial",
        "input_tokens": 25,
        "output_tokens": 13,
        "cached_tokens": 1,
        "limitations": ["output_mismatch", "development_only_no_campaign_authority"],
    }
    for field, value in mutations.items():
        tampered = copy.deepcopy(payload)
        tampered[field] = value
        manifest = tmp_path / f"tampered-{field}.json"
        manifest.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(ValueError):
            load_development_provider_seed_capability(str(manifest))

    combined_mutations = [
        {
            "fingerprint_status": "inconsistent",
            "fingerprint_match": False,
        },
        {
            "seed_control_classification": "unverified",
            "paired_confirmatory_eligible": False,
        },
    ]
    for index, changes in enumerate(combined_mutations):
        tampered = copy.deepcopy(payload)
        tampered.update(changes)
        manifest = tmp_path / f"tampered-combined-{index}.json"
        manifest.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(ValueError):
            load_development_provider_seed_capability(str(manifest))


def test_raw_protocol_or_observation_tamper_is_fail_closed(tmp_path) -> None:
    _, _, payload = _write(
        tmp_path,
        documentation_status="deterministic_documented",
        review_type="independent_review",
        observations=[_completed(), _completed(), _completed()],
    )
    raw_mutations = []
    changed_protocol = copy.deepcopy(payload)
    changed_protocol["probe_protocol"]["prompt_sha256"] = "e" * 64
    raw_mutations.append(changed_protocol)
    changed_observation = copy.deepcopy(payload)
    changed_observation["observations"][0]["output_size_bytes"] += 1
    raw_mutations.append(changed_observation)
    changed_order = copy.deepcopy(payload)
    changed_order["observations"][1]["call_index"] = 0
    raw_mutations.append(changed_order)

    for index, tampered in enumerate(raw_mutations):
        manifest = tmp_path / f"tampered-raw-{index}.json"
        manifest.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(ValueError):
            load_development_provider_seed_capability(str(manifest))
