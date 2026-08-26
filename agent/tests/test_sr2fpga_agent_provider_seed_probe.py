import json
import hashlib

import pytest

from sr2fpga_agent import provider_seed_probe
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore


class _ProbeClient:
    last_config = None

    def __init__(self, config) -> None:
        type(self).last_config = config
        self.calls = 0

    def chat(self, _messages):
        self.calls += 1
        return '{"status":"ok"}'

    def consume_token_usage(self):
        return {"input_tokens": 12, "output_tokens": 4, "cached_tokens": 0}

    def consume_response_provenance(self):
        return {
            "system_fingerprint_status": "reported",
            "provider_system_fingerprint": "fp-test",
        }


class _EmptyProbeClient(_ProbeClient):
    def chat(self, _messages):
        self.calls += 1
        return ""


class _ParserFailureProbeClient(_ProbeClient):
    def chat(self, _messages):
        self.calls += 1
        raise ValueError("malformed provider response")


def _artifact_payload(root, report: dict) -> dict:
    reference = ArtifactRef(**report["artifact_ref"])
    return json.loads(ArtifactStore(root).read_verified(reference))


def test_probe_cli_writes_bounded_non_authoritative_artifact(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")
    monkeypatch.setattr(provider_seed_probe, "OpenAICompatibleClient", _ProbeClient)

    provider_seed_probe.main(
        [
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--model",
            "fake-model",
            "--base-url",
            "https://example.invalid/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--seed",
            "17",
            "--repetitions",
            "3",
            "--max-tokens",
            "32",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    assert report["probe_status"] == "complete"
    assert report["seed_control_classification"] == "unverified"
    assert report["paired_confirmatory_eligible"] is False
    assert report["provider_token_usage_status"] == "provider_reported"
    assert report["input_tokens"] == 36
    assert report["output_tokens"] == 12
    payload = _artifact_payload(tmp_path / "artifacts", report)
    assert payload["probe_protocol"] == {
        "prompt_sha256": hashlib.sha256(
            provider_seed_probe._PROBE_PROMPT.encode("utf-8")
        ).hexdigest(),
        "seed": 17,
        "temperature": 0.1,
        "max_tokens": 32,
        "repetitions": 3,
        "probe_implementation_sha256": hashlib.sha256(
            provider_seed_probe.Path(provider_seed_probe.__file__).read_bytes()
        ).hexdigest(),
    }
    assert [item["call_index"] for item in payload["observations"]] == [0, 1, 2]
    assert all(item["output_size_bytes"] > 0 for item in payload["observations"])
    assert all(item["output_sha256"] for item in payload["observations"])
    assert _ProbeClient.last_config.seed == 17
    assert _ProbeClient.last_config.max_tokens == 32


def test_probe_cli_rejects_empty_provider_output(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")
    monkeypatch.setattr(
        provider_seed_probe, "OpenAICompatibleClient", _EmptyProbeClient
    )

    provider_seed_probe.main(
        [
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--model",
            "fake-model",
            "--base-url",
            "https://example.invalid/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--repetitions",
            "3",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    assert report["probe_status"] == "infrastructure_error"
    assert report["failed_repetitions"] == 1
    assert report["failure_categories"] == ["response_invalid"]
    assert report["seed_control_classification"] == "unavailable"


def test_probe_cli_hashes_checked_documentation_snapshot(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")
    monkeypatch.setattr(provider_seed_probe, "OpenAICompatibleClient", _ProbeClient)
    snapshot = tmp_path / "provider-doc.md"
    snapshot.write_text("documented best-effort seed behavior", encoding="utf-8")

    provider_seed_probe.main(
        [
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--model",
            "fake-model",
            "--base-url",
            "https://example.invalid/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--repetitions",
            "2",
            "--documentation-status",
            "best_effort_documented",
            "--documentation-snapshot",
            str(snapshot),
            "--documentation-source-url",
            "https://example.invalid/provider-seed-docs",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    assert report["documentation_snapshot_sha256"] == hashlib.sha256(
        snapshot.read_bytes()
    ).hexdigest()
    assert report["documentation_source_url_sha256"] == hashlib.sha256(
        b"https://example.invalid/provider-seed-docs"
    ).hexdigest()
    assert report["documentation_review_type"] == "self_reviewed_development"
    payload = _artifact_payload(tmp_path / "artifacts", report)
    assert payload["documentation_review"]["reviewer_provenance_sha256"]
    assert payload["paired_confirmatory_eligible"] is False


def test_probe_cli_requires_snapshot_for_checked_documentation(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")

    with pytest.raises(SystemExit, match="documentation-snapshot is required"):
        provider_seed_probe.main(
            [
                "--artifact-root",
                str(tmp_path / "artifacts"),
                "--model",
                "fake-model",
                "--base-url",
                "https://example.invalid/v1",
                "--api-key-env",
                "TEST_API_KEY",
                "--documentation-status",
                "best_effort_documented",
            ]
        )


def test_probe_cli_requires_source_url_for_checked_documentation(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")
    snapshot = tmp_path / "provider-doc.md"
    snapshot.write_text("seed docs", encoding="utf-8")

    with pytest.raises(SystemExit, match="documentation-source-url is required"):
        provider_seed_probe.main(
            [
                "--artifact-root",
                str(tmp_path / "artifacts"),
                "--model",
                "fake-model",
                "--base-url",
                "https://example.invalid/v1",
                "--api-key-env",
                "TEST_API_KEY",
                "--documentation-status",
                "best_effort_documented",
                "--documentation-snapshot",
                str(snapshot),
            ]
        )


def test_probe_cli_closes_artifact_on_non_runtime_parser_exception(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")
    monkeypatch.setattr(
        provider_seed_probe, "OpenAICompatibleClient", _ParserFailureProbeClient
    )

    provider_seed_probe.main(
        [
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--model",
            "fake-model",
            "--base-url",
            "https://example.invalid/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--repetitions",
            "3",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    payload = _artifact_payload(tmp_path / "artifacts", report)
    assert payload["probe_status"] == "infrastructure_error"
    assert payload["failed_repetitions"] == 1
    assert payload["observations"][0]["failure_category"] == "response_invalid"
    assert "malformed provider response" not in json.dumps(payload)


@pytest.mark.parametrize(
    ("message", "expected"),
    (
        ("request failed with HTTP 401", "authentication"),
        ("request failed with HTTP 429: insufficient_quota", "quota"),
        ("seed is not supported", "seed_rejected"),
        ("model does not exist", "model_unavailable"),
        ("request timed out", "timeout"),
        ("request failed with HTTP 503", "provider_error"),
    ),
)
def test_probe_failure_categories_are_sanitized(message, expected) -> None:
    assert provider_seed_probe._categorize_probe_failure(message) == expected
