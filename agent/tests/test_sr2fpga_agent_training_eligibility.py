import copy
import hashlib
import json

import pytest

from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import build_project_envelope
from sr2fpga_agent.training_eligibility import (
    EvaluatorEligibilityEvidence,
    TrainingEligibilityPolicy,
    build_training_eligibility_certificate,
    validate_training_eligibility_certificate,
)


def _sha256(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _episode_pack() -> dict[str, object]:
    public = {
        "requirement_id": "requirement-001",
        "revision_id": "revision-001",
        "public_text": "Build an eight-bit synchronous counter.",
        "fact_records": [],
        "platform_profile_id": "platform-open-source",
        "platform_profile_sha256": "a" * 64,
        "capability_profile_id": "capability-basic-rtl",
        "capability_profile_sha256": "b" * 64,
        "disposition": "ready",
    }
    public["public_projection_sha256"] = _sha256(public)
    without_hash = {
        "contract_version": "episode-pack-v1",
        "pack_id": "pack-001",
        "public_context": public,
        "audit_only": {
            "episode_id": "episode-001",
            "analysis_population": "development",
            "method_condition_id": "M0",
            "evaluator_metadata_sha256": "c" * 64,
            "private_ref_ids": [],
        },
    }
    return {**without_hash, "pack_sha256": _sha256(without_hash)}


def _project(*, increment: str = "1'b1") -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "direct_counter",
        "top": {
            "module": "direct_top",
            "source": "src/design.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "src/design.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return GeneratedProject(
        project_name="direct_counter",
        files={
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "src/design.v": (
                "module direct_top(input wire clk, output reg [7:0] count);\n"
                f"  always @(posedge clk) count <= count + {increment};\n"
                "endmodule\n"
            ),
        },
    )


def _policies(project: GeneratedProject, *, trusted_rtl: bool = False):
    policies = {
        path: {"owner": "model", "origin": "model_generated", "editable": True}
        for path in project.files
    }
    if trusted_rtl:
        policies["src/design.v"] = {
            "owner": "trusted_builder",
            "origin": "deterministic",
            "editable": False,
        }
    return policies


def _artifacts(*, qualification_status: str = "completed", outcome: str = "pass", trusted_rtl: bool = False):
    pack = _episode_pack()
    initial_project = _project()
    terminal_project = _project(increment="2'b10" if trusted_rtl else "1'b1")
    initial = build_project_envelope(
        initial_project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="d" * 64,
        snapshot_id="snapshot-initial",
        file_policies=_policies(initial_project, trusted_rtl=trusted_rtl),
    )
    terminal = build_project_envelope(
        terminal_project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256="d" * 64,
        snapshot_id="snapshot-terminal",
        file_policies=_policies(terminal_project, trusted_rtl=trusted_rtl),
    )
    candidate = {
        "contract_version": "terminal-candidate-v1",
        "candidate_id": "candidate-final",
        "episode_id": "episode-001",
        "method_condition_id": "M0",
        "project_name": "direct_counter",
        "project_envelope_sha256": terminal["envelope_sha256"],
        "requirement_projection_sha256": pack["public_context"]["public_projection_sha256"],
        "creation_event_id": "event-" + "e" * 64,
        "project_files": [
            {
                "path": item["path"],
                "artifact_key": f"candidate/{item['path']}",
                "sha256": item["sha256"],
            }
            for item in terminal["files"]
        ],
        "public_evidence_sha256": [],
    }
    qualification = {
        "contract_version": "training-qualification-outcome-v1",
        "evaluation_scope": "training_qualification",
        "episode_id": "episode-001",
        "method_condition_id": "M0",
        "terminal_candidate_sha256": _sha256(candidate),
        "training_split_id": "train-split-dev",
        "purpose": "training_release_qualification",
        "public_pack_sha256": pack["pack_sha256"],
        "private_pack_sha256": "f" * 64,
        "execution_status": qualification_status,
        "evaluator_evidence_refs": ["evidence/training-qualification-001"],
    }
    if qualification_status == "completed":
        qualification["outcome"] = outcome
    else:
        qualification["infrastructure_reason"] = "toolchain unavailable"
    return pack, initial, candidate, terminal, qualification


def _policy(*, source_classes=("model_generated",), failure_origins=("natural_llm",)):
    return TrainingEligibilityPolicy.create(
        policy_id="development-training-policy",
        training_split_id="train-split-dev",
        episode_ids=("episode-001",),
        allowed_source_classes=source_classes,
        allowed_failure_origins=failure_origins,
    )


def _evidence(**overrides):
    values = {
        "source_class": "model_generated",
        "failure_origin": "natural_llm",
        "initial_snapshot_pre_feedback": True,
        "method_applicable_h_pass": True,
        "provenance_complete": True,
        "budget_compliant": True,
        "hidden_material_redacted": True,
        "leakage_audit_pass": True,
        "official_hidden_outcome_refs": (),
    }
    values.update(overrides)
    return EvaluatorEligibilityEvidence(**values)


def _build(artifacts, *, policy=None, evidence=None):
    pack, initial, candidate, terminal, qualification = artifacts
    return build_training_eligibility_certificate(
        episode_pack=pack,
        initial_project_envelope=initial,
        terminal_candidate=candidate,
        terminal_project_envelope=terminal,
        qualification_outcome=qualification,
        policy=policy or _policy(),
        evidence=evidence or _evidence(),
    )


def test_completed_pass_issues_hash_bound_eligible_certificate() -> None:
    certificate = _build(_artifacts())

    assert certificate["eligibility_status"] == "eligible"
    assert certificate["exclusion_reason_ids"] == []
    assert all(certificate["checks"].values())
    validate_training_eligibility_certificate(certificate)


@pytest.mark.parametrize(
    ("status", "outcome"), (("completed", "fail"), ("not_run", "pass"))
)
def test_fail_and_not_run_are_ineligible_without_becoming_artifact_errors(status, outcome) -> None:
    certificate = _build(_artifacts(qualification_status=status, outcome=outcome))

    assert certificate["eligibility_status"] == "ineligible"
    assert "training_qualification_not_completed_pass" in certificate["exclusion_reason_ids"]


def test_official_hidden_outcome_reference_is_ineligible() -> None:
    certificate = _build(
        _artifacts(),
        evidence=_evidence(official_hidden_outcome_refs=("official-hidden-outcome/001",)),
    )

    assert certificate["official_hidden_outcome_ref_count"] == 1
    assert "official_hidden_outcome_reference_present" in certificate["exclusion_reason_ids"]


def test_reference_source_is_hard_excluded_even_when_policy_lists_it() -> None:
    certificate = _build(
        _artifacts(),
        policy=_policy(source_classes=("B_ref",)),
        evidence=_evidence(source_class="B_ref"),
    )

    assert certificate["checks"]["source_policy_allowed"] is False
    assert "source_policy_disallowed" in certificate["exclusion_reason_ids"]


def test_changed_trusted_surface_is_ineligible() -> None:
    certificate = _build(_artifacts(trusted_rtl=True))

    assert certificate["checks"]["trusted_edit_surface_intact"] is False
    assert "trusted_edit_surface_changed" in certificate["exclusion_reason_ids"]


def test_terminal_candidate_binding_mismatch_is_rejected() -> None:
    artifacts = list(_artifacts())
    artifacts[4] = {**artifacts[4], "terminal_candidate_sha256": "0" * 64}

    with pytest.raises(ValueError, match="qualification terminal candidate"):
        _build(tuple(artifacts))


def test_tampered_certificate_hash_and_reasons_are_rejected() -> None:
    certificate = _build(_artifacts())
    tampered_hash = {**certificate, "source_class": "other"}

    with pytest.raises(ValueError, match="artifact_sha256 mismatch"):
        validate_training_eligibility_certificate(tampered_hash)

    tampered_reasons = copy.deepcopy(certificate)
    tampered_reasons["eligibility_status"] = "ineligible"
    tampered_reasons["exclusion_reason_ids"] = ["invented_reason"]
    without_hash = {k: v for k, v in tampered_reasons.items() if k != "artifact_sha256"}
    tampered_reasons["artifact_sha256"] = _sha256(without_hash)
    with pytest.raises(ValueError, match="exclusion reasons are not canonical"):
        validate_training_eligibility_certificate(tampered_reasons)
