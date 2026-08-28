import json
import hashlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.frozen_context import (
    context_from_validated_episode_pack,
    frozen_project_name,
)
from sr2fpga_agent.method_adapters import PairedArtifactCoordinator
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.parsers import parse_system_his_v12
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.provider_seed_capability import (
    ProviderSeedProbeObservation,
    write_development_provider_seed_capability,
)
from sr2fpga_agent.generation.direct_project import DirectProjectGenerator
from sr2fpga_agent.runner import (
    _bind_runner_method_generator,
    _config_fingerprint,
    _config_to_jsonable,
    _measurement_freeze_manifest,
    _method_artifact_completion_record,
    _project_generator_for_sample,
    _runner_pairing_key,
    _sample_attempt_limit,
    load_runner_config,
    planned_samples,
    run_batch,
    runner_preflight,
)
from sr2fpga_agent.system_his_fidelity import build_frozen_requirement_trace


class _Client:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[list[dict[str, str]]] = []

    def stream_chat(self, messages):
        self.calls.append(messages)
        return self.response

    def chat(self, messages):
        self.calls.append(messages)
        return self.response


class _TwoStageStub:
    def __init__(self, req2his_client, project_client) -> None:
        self.system_his_generator = SimpleNamespace(client=req2his_client)
        self.his_project_generator = SimpleNamespace(client=project_client)


def _write_config(
    path,
    root,
    *,
    methods=("M3", "M4"),
    repair_provider="none",
    max_attempts=1,
    analysis_population="development",
) -> None:
    requirement = "Build an 8-bit synchronous counter with active-low reset."
    path.write_text(
        json.dumps(
            {
                "dataset_root": str(root / "datasets"),
                "export_root": str(root / "exports"),
                "run_root": str(root / "runs"),
                "provider": "his",
                "repair_provider": repair_provider,
                "max_attempts": max_attempts,
                "refresh_exports": False,
                "sources": {
                    "his": {
                        "kind": "openai_compat",
                        "model": "fake-model",
                        "base_url": "https://example.invalid/v1",
                        "api_key_env": "FAKE_API_KEY",
                        "generation_mode": "two_stage",
                        "system_his_schema_version": "system-his-v1.2",
                    }
                },
                "tasks": [
                    {
                        "source": "his",
                        "task_type": "counter",
                        "widths": [8],
                        "count": 1,
                        "requirement": requirement,
                        "method_condition": method,
                        "analysis_population": analysis_population,
                        **(
                             {
                                 "semantic_instance_id": "semantic-counter-001",
                                 "replicate_id": "replicate-000",
                                 "decoding_seed": 17,
                                 "paired_block_id": "pair-counter-001-seed-17",
                                 "decoding_control_mode": "documented_seed_control",
                                 "execution_schedule_seed": 909991,
                             }
                            if analysis_population == "excluded"
                            else {}
                        ),
                    }
                    for method in methods
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_direct_config(path, root) -> None:
    requirement = "Build an 8-bit synchronous counter with active-low reset."
    path.write_text(
        json.dumps(
            {
                "dataset_root": str(root / "datasets"),
                "export_root": str(root / "exports"),
                "run_root": str(root / "runs"),
                "provider": "direct",
                "repair_provider": "none",
                "max_attempts": 1,
                "refresh_exports": False,
                "sources": {
                    "direct": {
                        "kind": "deepseek",
                        "model": "fake-model",
                        "base_url": "https://example.invalid/v1",
                        "api_key_env": "FAKE_API_KEY",
                        "generation_mode": "direct",
                    }
                },
                "tasks": [
                    {
                        "source": "direct",
                        "task_type": "counter",
                        "widths": [8],
                        "count": 1,
                        "requirement": requirement,
                        "method_condition": method,
                    }
                    for method in ("M0", "M1")
                ],
            }
        ),
        encoding="utf-8",
    )


def _responses(metadata):
    context = context_from_validated_episode_pack(metadata["episode_pack"])
    platform = PlatformProfile("generic_verilog", "generic", "open_source")
    request = ProjectRequest(
        "counter",
        8,
        frozen_project_name(context),
        context.public_text,
    )
    project = ProjectGenerator().generate(request, platform)
    system_his = parse_system_his_v12(project.files["system_his.json"])
    system_his["intent"]["requirement_trace"] = build_frozen_requirement_trace(
        context,
        system_his,
    )
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": project.project_name,
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "rst_n", "direction": "input", "width": 1},
                    {"name": "en", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [
            {
                "path": "constraints/timing.sdc",
                "role": "constraint",
                "applicability": "advisory",
            },
            {
                "path": "sim/tb_top.v",
                "role": "candidate_testbench",
                "applicability": "advisory",
            },
            {
                "path": "reports/predicted_qor.json",
                "role": "predicted_qor",
                "applicability": "advisory",
            },
        ],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    free_files = {
        path: content
        for path, content in project.files.items()
        if path not in {"manifest.json", "system_his.json"}
    }
    free_files["manifest.json"] = json.dumps(manifest)
    free_project = json.dumps(
        {"project_name": project.project_name, "files": free_files}
    )
    return context, json.dumps(system_his), free_project


def test_standard_config_resolves_explicit_m3_and_paired_m4(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path)

    config = load_runner_config(config_path)
    samples = planned_samples(config)
    metadata = [sample.metadata(config) for sample in samples]

    assert [item["method_condition"] for item in metadata] == ["M3", "M4"]
    assert [item["model_call_budget"]["max_model_calls"] for item in metadata] == [2, 2]
    assert [item["contract_skeleton_mode"] for item in metadata] == [
        "none_free_full_project",
        "behavior_files",
    ]
    assert samples[0].paired_requirement_id == samples[1].paired_requirement_id
    assert all("episode_pack" in item for item in metadata)


def test_m0_m1_runner_bridge_shares_one_frozen_direct_initial_project(tmp_path) -> None:
    config_path = tmp_path / "direct-runner.json"
    _write_direct_config(config_path, tmp_path)
    config = load_runner_config(config_path)
    m0_sample, m1_sample = planned_samples(config)
    m0_metadata = m0_sample.metadata(config)
    m1_metadata = m1_sample.metadata(config)
    context, _, project_response = _responses(m0_metadata)
    m0_client = _Client(project_response)
    m1_client = _Client(project_response)
    store = ArtifactStore(tmp_path / "method-artifacts")
    coordinator = PairedArtifactCoordinator(store)

    m0_generator = _bind_runner_method_generator(
        DirectProjectGenerator(m0_client),
        m0_metadata,
        config=config,
        sample=m0_sample,
        method_artifact_store=store,
        paired_artifact_coordinator=coordinator,
    )
    m1_generator = _bind_runner_method_generator(
        DirectProjectGenerator(m1_client),
        m1_metadata,
        config=config,
        sample=m1_sample,
        method_artifact_store=store,
        paired_artifact_coordinator=coordinator,
    )
    request = ProjectRequest("counter", 8, "private-name", context.public_text)
    platform = PlatformProfile("generic_verilog", "generic", "open_source")
    m0_project = m0_generator.generate(request, platform)
    m1_project = m1_generator.generate(request, platform)

    assert len(m0_client.calls) + len(m1_client.calls) == 1
    assert m0_project.files == m1_project.files
    assert m0_generator.last_outcome.candidate.artifact_ref == (
        m1_generator.last_outcome.candidate.artifact_ref
    )
    serialized = json.dumps([*m0_client.calls, *m1_client.calls], ensure_ascii=False)
    assert context.public_projection_sha256 in serialized
    assert "private-name" not in serialized
    record = _method_artifact_completion_record(m0_generator, m0_metadata)
    assert record == {
        "method_condition": "M0",
        "candidate_artifact_ref": m0_generator.last_outcome.candidate.artifact_ref.to_dict(),
        "project_package_sha256": m0_generator.last_outcome.candidate.project_package_sha256,
        "planning_kind": None,
        "planning_artifact_ref": None,
        "skeleton_artifact_ref": None,
        "skeleton_project_sha256": None,
        "h_status": "not_applicable",
        "skeleton_mode": "legacy_full_project",
        "his_corrections_used": 0,
    }


def test_standard_config_resolves_explicit_m2_as_two_call_no_skeleton(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path, methods=("M2",))

    config = load_runner_config(config_path)
    sample = planned_samples(config)[0]
    metadata = sample.metadata(config)

    assert metadata["method_condition"] == "M2"
    assert metadata["model_call_budget"]["max_model_calls"] == 2
    assert metadata["contract_skeleton_mode"] == "none"
    assert "episode_pack" in metadata


def test_method_contract_scopes_calls_repairs_and_excluded_pack(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M2", "M3", "M4", "M5"),
        repair_provider="his",
        max_attempts=3,
        analysis_population="excluded",
    )

    config = load_runner_config(config_path)
    metadata = [sample.metadata(config) for sample in planned_samples(config)]

    assert [item["method_condition"] for item in metadata] == ["M2", "M3", "M4", "M5"]
    assert [item["model_call_budget"]["max_model_calls"] for item in metadata] == [
        2,
        2,
        2,
        4,
    ]
    assert [item["repair_provider_resolved"] for item in metadata] == [
        "none",
        "none",
        "none",
        "his",
    ]
    assert [_sample_attempt_limit(config, item["method_condition"]) for item in metadata] == [
        1,
        1,
        1,
        3,
    ]
    assert all(item["analysis_population"] == "excluded" for item in metadata)
    assert all(
        item["episode_pack"]["audit_only"]["analysis_population"] == "excluded"
        for item in metadata
    )
    assert {
         (
             item["semantic_instance_id"],
             item["replicate_id"],
             item["decoding_seed"],
             item["paired_block_id"],
             item["decoding_control_mode"],
             item["execution_schedule_seed"],
             item["pairing_identity_source"],
        )
        for item in metadata
    } == {
        (
             "semantic-counter-001",
             "replicate-000",
             17,
             "pair-counter-001-seed-17",
             "documented_seed_control",
             909991,
             "explicit",
        )
    }


@pytest.mark.parametrize(
    "missing_field",
    (
        "semantic_instance_id",
        "replicate_id",
        "decoding_seed",
        "paired_block_id",
        "decoding_control_mode",
        "execution_schedule_seed",
    ),
)
def test_excluded_config_requires_complete_first_class_pairing_identity(
    tmp_path, missing_field
) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    del payload["tasks"][0][missing_field]
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SystemExit, match="first-class pairing identity"):
        load_runner_config(config_path)


def test_runner_pairing_key_uses_explicit_instance_seed_and_block(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M3", "M4"),
        analysis_population="excluded",
    )
    config = load_runner_config(config_path)
    m3_sample, m4_sample = planned_samples(config)
    m3_context = context_from_validated_episode_pack(m3_sample.metadata(config)["episode_pack"])
    m4_context = context_from_validated_episode_pack(m4_sample.metadata(config)["episode_pack"])

    m3_pairing = _runner_pairing_key(config, m3_sample, m3_context)
    m4_pairing = _runner_pairing_key(config, m4_sample, m4_context)

    assert m3_pairing.semantic_instance_id == "semantic-counter-001"
    assert m3_pairing.replicate_id == "replicate-000"
    assert m3_pairing.decoding_seed == 17
    assert m3_pairing.paired_block_id == "pair-counter-001-seed-17"
    assert m3_pairing == m4_pairing


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("wire_api", "responses"),
        ("reasoning_effort", "xhigh"),
        ("disable_response_storage", True),
    ),
)
def test_pairing_and_measurement_freeze_bind_wire_configuration(
    tmp_path, field, value
) -> None:
    base_path = tmp_path / "base.json"
    configured_path = tmp_path / "configured.json"
    _write_config(
        base_path,
        tmp_path / "base",
        methods=("M4",),
        analysis_population="excluded",
    )
    _write_config(
        configured_path,
        tmp_path / "configured",
        methods=("M4",),
        analysis_population="excluded",
    )
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    configured_payload = json.loads(configured_path.read_text(encoding="utf-8"))
    if field != "wire_api":
        base_payload["sources"]["his"]["wire_api"] = "responses"
        configured_payload["sources"]["his"]["wire_api"] = "responses"
        base_path.write_text(json.dumps(base_payload), encoding="utf-8")
    configured_payload["sources"]["his"][field] = value
    configured_path.write_text(json.dumps(configured_payload), encoding="utf-8")

    base = load_runner_config(base_path)
    configured = load_runner_config(configured_path)
    base_sample = planned_samples(base)[0]
    configured_sample = planned_samples(configured)[0]
    base_context = context_from_validated_episode_pack(
        base_sample.metadata(base)["episode_pack"]
    )
    configured_context = context_from_validated_episode_pack(
        configured_sample.metadata(configured)["episode_pack"]
    )

    assert _runner_pairing_key(
        base, base_sample, base_context
    ).model_provenance_sha256 != _runner_pairing_key(
        configured, configured_sample, configured_context
    ).model_provenance_sha256
    freeze = _measurement_freeze_manifest(
        configured,
        "wire-config-bound",
        _config_fingerprint(configured),
        [configured_sample],
        tool_versions={},
    )
    assert freeze["sources"][0][field] == value


def test_excluded_paired_block_rejects_conflicting_seed_before_dispatch(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M3", "M4"),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tasks"][1]["decoding_seed"] = 18
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    config = load_runner_config(config_path)

    with pytest.raises(SystemExit, match="bound to conflicting"):
        planned_samples(config)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("replicate_id", "replicate-001"),
        ("execution_schedule_seed", 909992),
        ("decoding_control_mode", "stochastic_blocked"),
    ),
)
def test_excluded_paired_block_rejects_conflicting_block_identity_field(
    tmp_path, field, value
) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M3", "M4"),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tasks"][1][field] = value
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    config = load_runner_config(config_path)

    with pytest.raises(SystemExit, match="bound to conflicting"):
        planned_samples(config)


def test_stochastic_blocked_explicit_identity_allows_null_requested_seed(
    tmp_path,
) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tasks"][0]["decoding_control_mode"] = "stochastic_blocked"
    payload["tasks"][0]["decoding_seed"] = None
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    sample = planned_samples(load_runner_config(config_path))[0]

    assert sample.decoding_seed is None
    assert sample.replicate_id == "replicate-000"
    assert sample.execution_schedule_seed == 909991
    assert sample.decoding_control_mode == "stochastic_blocked"


def test_stochastic_blocked_requires_explicit_null_requested_seed_field(
    tmp_path,
) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tasks"][0]["decoding_control_mode"] = "stochastic_blocked"
    del payload["tasks"][0]["decoding_seed"]
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SystemExit, match="first-class pairing identity"):
        load_runner_config(config_path)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("semantic_instance_id", 123),
        ("replicate_id", 456),
        ("paired_block_id", 789),
    ),
)
def test_explicit_identity_ids_reject_non_string_values(tmp_path, field, value) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tasks"][0][field] = value
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SystemExit, match=f"{field} must be a string"):
        load_runner_config(config_path)


def test_explicit_identity_ids_use_contract_ascii_vocabulary(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tasks"][0]["replicate_id"] = "replicate-零"
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SystemExit, match="replicate_id contains unsafe characters"):
        load_runner_config(config_path)


def test_legacy_development_derived_identity_remains_non_g3(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path, methods=("M4",))

    sample = planned_samples(load_runner_config(config_path))[0]

    assert sample.pairing_identity_source == "development_derived"
    assert sample.replicate_id == ""
    assert sample.execution_schedule_seed is None
    assert sample.decoding_control_mode == ""


def test_replicate_and_schedule_identity_never_enter_m0_m5_model_prompts(
    tmp_path,
) -> None:
    direct_path = tmp_path / "direct.json"
    _write_direct_config(direct_path, tmp_path / "direct")
    direct_payload = json.loads(direct_path.read_text(encoding="utf-8"))
    for task in direct_payload["tasks"]:
        task.update(
            {
                "analysis_population": "excluded",
                "semantic_instance_id": "semantic-counter-001",
                "replicate_id": "replicate-prompt-spy-7f4c",
                "decoding_seed": 17,
                "paired_block_id": "pair-counter-prompt-spy",
                "decoding_control_mode": "documented_seed_control",
                "execution_schedule_seed": 909991,
            }
        )
    direct_path.write_text(json.dumps(direct_payload), encoding="utf-8")

    his_path = tmp_path / "his.json"
    _write_config(
        his_path,
        tmp_path / "his",
        methods=("M2", "M3", "M4", "M5"),
        analysis_population="excluded",
    )

    captured_by_method = {}
    for config in (load_runner_config(direct_path), load_runner_config(his_path)):
        for sample in planned_samples(config):
            metadata = sample.metadata(config)
            context, his_response, project_response = _responses(metadata)
            store = ArtifactStore(tmp_path / "prompt-stores" / sample.method_condition)
            if sample.method_condition in {"M0", "M1"}:
                clients = [_Client(project_response)]
                base_generator = DirectProjectGenerator(clients[0])
            else:
                first_response = (
                    "Use one counter module with synchronous state."
                    if sample.method_condition == "M2"
                    else his_response
                )
                second_response = (
                    project_response
                    if sample.method_condition in {"M2", "M3"}
                    else json.dumps({"behavior_files": {}})
                )
                clients = [_Client(first_response), _Client(second_response)]
                base_generator = _TwoStageStub(*clients)
            generator = _bind_runner_method_generator(
                base_generator,
                metadata,
                config=config,
                sample=sample,
                method_artifact_store=store,
                paired_artifact_coordinator=PairedArtifactCoordinator(store),
            )
            generator.generate(
                ProjectRequest("counter", 8, "private-name", context.public_text),
                PlatformProfile("generic_verilog", "generic", "open_source"),
            )
            method_calls = [call for client in clients for call in client.calls]
            assert method_calls
            captured_by_method[sample.method_condition] = method_calls

    assert set(captured_by_method) == {"M0", "M1", "M2", "M3", "M4", "M5"}
    serialized = json.dumps(captured_by_method, ensure_ascii=False)
    assert "replicate-prompt-spy-7f4c" not in serialized
    assert "909991" not in serialized


@pytest.mark.parametrize("model_budget", (None, ModelCallBudget(2)))
def test_runner_forwards_planned_seed_to_provider_builder(tmp_path, model_budget) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M3",),
        analysis_population="excluded",
    )
    config = load_runner_config(config_path)
    sample = planned_samples(config)[0]
    observed = {}

    def build(_connection, **kwargs):
        observed.update(kwargs)
        return object()

    with (
        patch(
            "sr2fpga_agent.runner.build_project_generator_for_connection",
            side_effect=build,
        ),
        patch(
            "sr2fpga_agent.runner._bind_runner_method_generator",
            side_effect=lambda generator, *_args, **_kwargs: generator,
        ),
    ):
        _project_generator_for_sample(
            {},
            config,
            sample,
            tmp_path / "events.jsonl",
            model_budget=model_budget,
        )

    assert observed["decoding_seed"] == 17


def test_strict_paired_seed_control_stops_before_run_side_effects(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["require_paired_confirmatory_seed_control"] = True
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    config = load_runner_config(config_path)

    with pytest.raises(SystemExit, match="lacks a provider seed capability manifest"):
        run_batch(config, run_id="strict-seed-control")

    assert not (tmp_path / "runs" / "strict-seed-control").exists()


def test_strict_seed_control_rejects_responses_with_chat_capability(
    tmp_path, monkeypatch
) -> None:
    store = ArtifactStore(tmp_path / "capability-store")
    ref = write_development_provider_seed_capability(
        store,
        provider_adapter="openai_compatible",
        provider_model="fake-model",
        gateway_base_url="https://example.invalid/v1",
        protocol={
            "prompt_sha256": "1" * 64,
            "seed": 17,
            "temperature": 0.1,
            "max_tokens": 32,
            "repetitions": 2,
            "probe_implementation_sha256": "2" * 64,
        },
        documentation_status="deterministic_documented",
        documentation_snapshot_sha256="a" * 64,
        documentation_source_url_sha256="c" * 64,
        documentation_review={
            "review_type": "independent_review",
            "reviewer_provenance_sha256": "3" * 64,
        },
        observations=[
            ProviderSeedProbeObservation(
                "completed", "b" * 64, "fp-a", output_size_bytes=15
            ),
            ProviderSeedProbeObservation(
                "completed", "b" * 64, "fp-a", output_size_bytes=15
            ),
        ],
    )
    manifest_path = tmp_path / "seed-capability.json"
    manifest_path.write_bytes(store.read_verified(ref))
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M4",),
        analysis_population="excluded",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["require_paired_confirmatory_seed_control"] = True
    payload["sources"]["his"]["wire_api"] = "responses"
    payload["sources"]["his"]["seed_capability_manifest"] = str(manifest_path)
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("FAKE_API_KEY", "fake-key")

    report = runner_preflight(
        load_runner_config(config_path),
        run_id="responses-seed-control",
        validate_provider=False,
    )

    assert report["ok"] is False
    assert any(
        "wire_api=responses cannot use a seed-control capability" in error
        for error in report["errors"]
    )
    assert not (tmp_path / "runs" / "responses-seed-control").exists()


def test_seed_capability_snapshot_is_content_bound_without_local_path(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "capability-store")
    ref = write_development_provider_seed_capability(
        store,
        provider_adapter="openai_compatible",
        provider_model="fake-model",
        gateway_base_url="https://example.invalid/v1",
        protocol={
            "prompt_sha256": "1" * 64,
            "seed": 17,
            "temperature": 0.1,
            "max_tokens": 32,
            "repetitions": 2,
            "probe_implementation_sha256": "2" * 64,
        },
        documentation_status="best_effort_documented",
        documentation_snapshot_sha256="a" * 64,
        documentation_source_url_sha256="c" * 64,
        documentation_review={
            "review_type": "self_reviewed_development",
            "reviewer_provenance_sha256": "3" * 64,
        },
        observations=[
            ProviderSeedProbeObservation(
                "completed", "b" * 64, "fp-a", output_size_bytes=15
            ),
            ProviderSeedProbeObservation(
                "completed", "b" * 64, "fp-a", output_size_bytes=15
            ),
        ],
    )
    manifest_path = tmp_path / "local" / "seed-capability.json"
    manifest_path.parent.mkdir()
    manifest_bytes = store.read_verified(ref)
    manifest_path.write_bytes(manifest_bytes)

    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path, methods=("M4",), analysis_population="excluded")
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["sources"]["his"]["seed_capability_manifest"] = str(manifest_path)
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    config = load_runner_config(config_path)
    samples = planned_samples(config)

    serialized = _config_to_jsonable(config)
    source_ref = serialized["sources"]["his"]["seed_capability_ref"]
    assert "seed_capability_manifest" not in serialized["sources"]["his"]
    assert source_ref == {
        "capability_profile_id": ref.key.removeprefix(
            "provider-seed-capabilities/"
        ),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "seed_control_classification": "best_effort_observed",
        "paired_confirmatory_eligible": False,
    }

    freeze = _measurement_freeze_manifest(
        config,
        "content-bound-seed-profile",
        _config_fingerprint(config),
        samples,
        tool_versions={},
    )
    assert freeze["sources"][0]["seed_capability_ref"] == source_ref
    assert str(manifest_path) not in json.dumps(freeze)


def test_unknown_method_condition_remains_fail_closed(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path, methods=("M9",))

    with pytest.raises(SystemExit, match="Unsupported or not-yet-implemented method_condition: M9"):
        load_runner_config(config_path)


def test_m3_m4_runner_bridge_reuses_his_and_m3_never_calls_skeleton(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path)
    config = load_runner_config(config_path)
    m3_sample, m4_sample = planned_samples(config)
    m3_metadata = m3_sample.metadata(config)
    m4_metadata = m4_sample.metadata(config)
    context, his_response, free_project_response = _responses(m3_metadata)

    req2his_client = _Client(his_response)
    m3_project_client = _Client(free_project_response)
    m4_project_client = _Client(json.dumps({"behavior_files": {}}))
    store = ArtifactStore(tmp_path / "method-artifacts")
    coordinator = PairedArtifactCoordinator(store)

    m3_generator = _bind_runner_method_generator(
        _TwoStageStub(req2his_client, m3_project_client),
        m3_metadata,
        config=config,
        sample=m3_sample,
        method_artifact_store=store,
        paired_artifact_coordinator=coordinator,
    )
    m4_generator = _bind_runner_method_generator(
        _TwoStageStub(req2his_client, m4_project_client),
        m4_metadata,
        config=config,
        sample=m4_sample,
        method_artifact_store=store,
        paired_artifact_coordinator=coordinator,
    )
    request = ProjectRequest("counter", 8, "private-name", context.public_text)
    platform = PlatformProfile("generic_verilog", "generic", "open_source")

    with patch(
        "sr2fpga_agent.generation.context_his.build_contract_skeleton_project",
        side_effect=AssertionError("M3 must not invoke the deterministic skeleton"),
    ):
        m3_project = m3_generator.generate(request, platform)
    m4_project = m4_generator.generate(request, platform)

    assert len(req2his_client.calls) == 1
    assert len(m3_project_client.calls) == 1
    assert len(m4_project_client.calls) == 1
    assert "system_his.json" in m3_project.files
    assert "system_his.json" in m4_project.files
    assert store.reference(
        f"method-emissions/{context.revision_id}/M3/initial-project"
    ) is not None
    assert store.reference(
        f"method-emissions/{context.revision_id}/M4/initial-project"
    ) is not None


def test_m2_runner_bridge_emits_untyped_plan_then_canonical_project(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(config_path, tmp_path, methods=("M2",))
    config = load_runner_config(config_path)
    sample = planned_samples(config)[0]
    metadata = sample.metadata(config)
    context, _, project_response = _responses(metadata)
    plan_client = _Client(
        "Use one top-level counter module, synchronous logic, and an active-low reset."
    )
    project_client = _Client(project_response)
    store = ArtifactStore(tmp_path / "method-artifacts")

    generator = _bind_runner_method_generator(
        _TwoStageStub(plan_client, project_client),
        metadata,
        config=config,
        sample=sample,
        method_artifact_store=store,
        paired_artifact_coordinator=PairedArtifactCoordinator(store),
    )
    request = ProjectRequest("counter", 8, "private-name", context.public_text)
    platform = PlatformProfile("generic_verilog", "generic", "open_source")

    with patch(
        "sr2fpga_agent.generation.context_his.build_contract_skeleton_project",
        side_effect=AssertionError("M2 must not invoke the deterministic skeleton"),
    ):
        project = generator.generate(request, platform)

    assert len(plan_client.calls) == 1
    assert len(project_client.calls) == 1
    assert "system_his.json" not in project.files
    assert store.reference(
        f"method-emissions/{context.revision_id}/M2/untyped-plan"
    ) is not None
    assert store.reference(
        f"method-emissions/{context.revision_id}/M2/initial-project"
    ) is not None
    serialized_plan_prompt = json.dumps(plan_client.calls, ensure_ascii=False)
    serialized_project_prompt = json.dumps(project_client.calls, ensure_ascii=False)
    assert context.public_projection_sha256 in serialized_plan_prompt
    assert "private-name" not in serialized_plan_prompt
    assert "family_id" not in serialized_plan_prompt
    assert "private-name" not in serialized_project_prompt


def test_m5_runner_bridge_uses_first_class_adapter_with_h_correction_budget(tmp_path) -> None:
    config_path = tmp_path / "runner.json"
    _write_config(
        config_path,
        tmp_path,
        methods=("M5",),
        repair_provider="his",
        max_attempts=2,
    )
    config = load_runner_config(config_path)
    sample = planned_samples(config)[0]
    metadata = sample.metadata(config)
    context, his_response, _ = _responses(metadata)
    his_client = _Client(his_response)
    behavior_client = _Client(json.dumps({"behavior_files": {}}))
    store = ArtifactStore(tmp_path / "method-artifacts")

    generator = _bind_runner_method_generator(
        _TwoStageStub(his_client, behavior_client),
        metadata,
        config=config,
        sample=sample,
        method_artifact_store=store,
        paired_artifact_coordinator=PairedArtifactCoordinator(store),
    )
    request = ProjectRequest("counter", 8, "private-name", context.public_text)
    platform = PlatformProfile("generic_verilog", "generic", "open_source")
    project = generator.generate(request, platform)

    assert metadata["method_condition"] == "M5"
    assert metadata["model_call_budget"]["max_model_calls"] == 3
    assert len(his_client.calls) == 1
    assert len(behavior_client.calls) == 1
    assert "system_his.json" in project.files
    assert store.reference(
        f"method-emissions/{context.revision_id}/M5/initial-project"
    ) is not None
