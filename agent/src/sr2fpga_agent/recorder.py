"""Dataset recording utilities for SR2FPGA generated samples."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sr2fpga_agent.models import GeneratedProject, PatchMetadata, PlatformProfile, ToolResult
from sr2fpga_agent.path_safety import project_file_target, validate_sample_id
from sr2fpga_agent.system_his_compatibility import load_system_his_compatibility_envelope


_TRAINING_VIEW_POLICY_ID = "sr2fpga-paper1-freeze-8.2-positive-views"
_TRAINING_VIEW_POLICY_VERSION = "2026-08-14"
_KNOWN_FILE_ORIGINS = frozenset({"deterministic", "model_generated"})


@dataclass(frozen=True)
class AttemptRecord:
    """One generation or repair attempt and its tool outcomes."""

    attempt_id: int
    generated_project: GeneratedProject
    tool_results: dict[str, ToolResult]
    diagnosis: dict[str, Any] | None = None
    patch_diff: str = ""
    patch_metadata: PatchMetadata | None = None


class DatasetRecorder:
    """Persist SR2FPGA samples and export training views."""

    def __init__(self, dataset_root: Path) -> None:
        self.dataset_root = dataset_root

    def start_sample(
        self,
        sample_id: str,
        requirement: str,
        platform_profile: PlatformProfile,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        validate_sample_id(sample_id)
        sample_dir = self.dataset_root / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "requirement.txt").write_text(requirement.rstrip() + "\n", encoding="utf-8")
        _write_json(sample_dir / "platform_profile.json", asdict(platform_profile))
        if metadata is not None:
            _write_json(sample_dir / "metadata.json", metadata)
        return sample_dir

    def write_attempt(self, sample_id: str, attempt: AttemptRecord) -> Path:
        validate_sample_id(sample_id)
        attempt_dir = self.dataset_root / sample_id / "attempts" / f"attempt_{attempt.attempt_id:03d}"
        project_dir = attempt_dir / "generated_project"
        _write_project(project_dir, attempt.generated_project, replace_existing=False)
        eval_dir = attempt_dir / "eval"
        eval_dir.mkdir(parents=True, exist_ok=True)
        for stage, result in attempt.tool_results.items():
            log_text = result.stdout
            if result.stderr:
                log_text = f"{log_text}{result.stderr}"
            (eval_dir / f"{stage}.log").write_text(log_text, encoding="utf-8")
            _write_json(eval_dir / f"{stage}.json", asdict(result))

        if attempt.diagnosis is not None:
            _write_json(attempt_dir / "diagnosis.json", attempt.diagnosis)
        if attempt.patch_diff:
            (attempt_dir / "patch.diff").write_text(attempt.patch_diff, encoding="utf-8")
        if attempt.patch_metadata is not None:
            _write_json(attempt_dir / "patch.json", attempt.patch_metadata.to_dict())
        return attempt_dir

    def update_patch_metadata(self, sample_id: str, attempt_id: int, patch_metadata: PatchMetadata) -> None:
        validate_sample_id(sample_id)
        _write_json(
            self.dataset_root / sample_id / "attempts" / f"attempt_{attempt_id:03d}" / "patch.json",
            patch_metadata.to_dict(),
        )

    def write_final(
        self,
        sample_id: str,
        generated_project: GeneratedProject,
        labels: dict[str, Any],
        measured_qor: dict[str, Any],
        tool_versions: dict[str, str],
        trajectory: dict[str, Any],
    ) -> Path:
        validate_sample_id(sample_id)
        sample_dir = self.dataset_root / sample_id
        _write_project(sample_dir / "final" / "generated_project", generated_project)
        eval_dir = sample_dir / "eval"
        eval_dir.mkdir(parents=True, exist_ok=True)
        episode = _system_his_episode(sample_id, generated_project, labels, measured_qor, trajectory)
        eligibility = _training_view_eligibility(
            sample_id=sample_id,
            requirement_present=_has_nonempty_text(sample_dir / "requirement.txt"),
            system_his_present="system_his.json" in generated_project.files,
            final_file_paths=sorted(generated_project.files),
            metadata=_read_metadata(sample_dir),
            episode=episode,
            labels=labels,
            decision_phase="write_final",
        )
        episode["training_view_eligibility"] = eligibility
        req2file = episode["derived_training_views"]["req2file"]
        req2file["available"] = eligibility["views"]["requirement_to_file"]["eligible"]
        req2file["verified_positive"] = eligibility["views"]["requirement_to_file"]["eligible"]
        req2file["eligibility_policy_id"] = _TRAINING_VIEW_POLICY_ID
        req2file["eligibility_policy_version"] = _TRAINING_VIEW_POLICY_VERSION
        req2file["exclusion_reasons"] = eligibility["views"]["requirement_to_file"]["reasons"]
        _write_json(eval_dir / "labels.json", labels)
        _write_json(eval_dir / "measured_qor.json", measured_qor)
        _write_json(eval_dir / "tool_versions.json", tool_versions)
        _write_json(eval_dir / "training_view_eligibility.json", eligibility)
        _write_json(eval_dir / "trajectory.json", episode)
        return sample_dir

    def export_training_views(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        requirement_rows: list[dict[str, Any]] = []
        his_project_rows: list[dict[str, Any]] = []
        requirement_project_rows: list[dict[str, Any]] = []
        requirement_file_rows: list[dict[str, Any]] = []
        diagnosis_rows: list[dict[str, Any]] = []
        patch_rows: list[dict[str, Any]] = []
        predicted_qor_rows: list[dict[str, Any]] = []
        measured_qor_rows: list[dict[str, Any]] = []
        eligibility_rows: list[dict[str, Any]] = []

        for sample_dir in sorted(path for path in self.dataset_root.iterdir() if path.is_dir()):
            sample_id = sample_dir.name
            requirement_path = sample_dir / "requirement.txt"
            final_project_dir = sample_dir / "final" / "generated_project"
            his_path = final_project_dir / "system_his.json"
            predicted_qor_path = final_project_dir / "reports" / "predicted_qor.json"
            measured_qor_path = sample_dir / "eval" / "measured_qor.json"
            metadata = _read_metadata(sample_dir)
            episode = _read_episode(sample_dir)
            labels = _read_labels(sample_dir)
            independent_oracle = _is_independent_oracle_episode(episode)
            requirement = requirement_path.read_text(encoding="utf-8").strip() if requirement_path.exists() else ""
            system_his = json.loads(his_path.read_text(encoding="utf-8")) if his_path.exists() else None
            final_files = (
                _read_project_files(final_project_dir, episode=episode)
                if final_project_dir.exists()
                else []
            )
            eligibility = _training_view_eligibility(
                sample_id=sample_id,
                requirement_present=bool(requirement),
                system_his_present=system_his is not None,
                final_file_paths=[item["path"] for item in final_files],
                metadata=metadata,
                episode=episode,
                labels=labels,
                decision_phase="export",
            )
            episode = dict(episode)
            episode["training_view_eligibility"] = eligibility
            eligibility_rows.append(eligibility)
            _write_json(sample_dir / "eval" / "training_view_eligibility.json", eligibility)

            if eligibility["views"]["requirement_to_his"]["eligible"]:
                requirement_rows.append(
                    {
                        "sample_id": sample_id,
                        "verified_positive": True,
                        "training_view_eligibility": eligibility["views"]["requirement_to_his"],
                        "metadata": metadata,
                        "episode": episode,
                        "requirement": requirement,
                        "system_his": system_his,
                        "system_his_origin": _file_origin_from_episode(episode, "system_his.json"),
                    }
                )

            if eligibility["views"]["his_to_project"]["eligible"]:
                his_project_rows.append(
                    {
                        "sample_id": sample_id,
                        "verified_positive": True,
                        "training_view_eligibility": eligibility["views"]["his_to_project"],
                        "metadata": metadata,
                        "episode": episode,
                        "system_his": system_his,
                        "files": final_files,
                    }
                )

            if eligibility["views"]["requirement_to_project"]["eligible"]:
                requirement_project_rows.append(
                    {
                        "sample_id": sample_id,
                        "verified_positive": True,
                        "training_view_eligibility": eligibility["views"]["requirement_to_project"],
                        "metadata": metadata,
                        "episode": episode,
                        "requirement": requirement,
                        "files": final_files,
                    }
                )

            if eligibility["views"]["requirement_to_file"]["eligible"]:
                for file_item in final_files:
                    requirement_file_rows.append(
                        {
                            "sample_id": sample_id,
                            "source_episode_id": _source_episode_id(sample_id, episode),
                            "view": "req2file",
                            "verified_positive": True,
                            "training_view_eligibility": eligibility["views"]["requirement_to_file"],
                            "official_eval_unit": False,
                            "standalone_pass_credit": False,
                            "metadata": metadata,
                            "episode": episode,
                            "requirement": requirement,
                            "file_path": file_item["path"],
                            "file_content": file_item["content"],
                            "file_origin": file_item["origin"],
                        }
                    )

            if final_files and predicted_qor_path.exists():
                predicted_qor_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": _episode_without_verification(episode),
                        "files": final_files,
                        "predicted_qor": json.loads(predicted_qor_path.read_text(encoding="utf-8")),
                    }
                )

            if final_files and measured_qor_path.exists():
                measured_qor_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": episode,
                        "files": final_files,
                        "measured_qor": json.loads(measured_qor_path.read_text(encoding="utf-8")),
                    }
                )

            attempts_dir = sample_dir / "attempts"
            if attempts_dir.exists():
                for attempt_dir in sorted(path for path in attempts_dir.iterdir() if path.is_dir()):
                    diagnosis_path = attempt_dir / "diagnosis.json"
                    patch_path = attempt_dir / "patch.diff"
                    patch_metadata_path = attempt_dir / "patch.json"
                    if diagnosis_path.exists():
                        diagnosis = _sanitize_training_payload(
                            json.loads(diagnosis_path.read_text(encoding="utf-8")),
                            independent_oracle=independent_oracle,
                        )
                        diagnosis_rows.append(
                            {
                                "sample_id": sample_id,
                                "verified_positive": False,
                                "training_target_class": "diagnostic",
                                "metadata": metadata,
                                "episode": episode,
                                "attempt_id": attempt_dir.name,
                                "diagnosis": diagnosis,
                            }
                        )
                    if diagnosis_path.exists() and patch_path.exists():
                        patch_rows.append(
                            {
                                "sample_id": sample_id,
                                "verified_positive": False,
                                "training_target_class": "diagnostic_unverified",
                                "metadata": metadata,
                                "episode": episode,
                                "attempt_id": attempt_dir.name,
                                "diagnosis": _sanitize_training_payload(
                                    json.loads(diagnosis_path.read_text(encoding="utf-8")),
                                    independent_oracle=independent_oracle,
                                ),
                                "patch": patch_path.read_text(encoding="utf-8"),
                                "patch_metadata": (
                                    _sanitize_training_payload(
                                        json.loads(patch_metadata_path.read_text(encoding="utf-8")),
                                        independent_oracle=independent_oracle,
                                    )
                                    if patch_metadata_path.exists()
                                    else None
                                ),
                            }
                        )

        _write_jsonl(output_dir / "requirement_to_his.jsonl", requirement_rows)
        _write_jsonl(output_dir / "his_to_project.jsonl", his_project_rows)
        _write_jsonl(output_dir / "requirement_to_project.jsonl", requirement_project_rows)
        _write_jsonl(output_dir / "requirement_to_file.jsonl", requirement_file_rows)
        _write_jsonl(output_dir / "failure_to_diagnosis.jsonl", diagnosis_rows)
        _write_jsonl(output_dir / "failure_to_patch.jsonl", patch_rows)
        _write_jsonl(output_dir / "project_to_predicted_qor.jsonl", predicted_qor_rows)
        _write_jsonl(output_dir / "project_to_measured_qor.jsonl", measured_qor_rows)
        _write_jsonl(output_dir / "training_view_eligibility.jsonl", eligibility_rows)


def _write_project(project_dir: Path, project: GeneratedProject, *, replace_existing: bool = True) -> None:
    if replace_existing and project_dir.exists():
        shutil.rmtree(project_dir)
    for relative_path, content in project.files.items():
        target = project_file_target(project_dir, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as output:
            for row in rows:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _has_nonempty_text(path: Path) -> bool:
    return path.is_file() and bool(path.read_text(encoding="utf-8").strip())


def _episode_without_verification(episode: dict[str, Any]) -> dict[str, Any]:
    result = dict(episode)
    result.pop("verification", None)
    return result


def _system_his_episode(
    sample_id: str,
    generated_project: GeneratedProject,
    labels: dict[str, Any],
    measured_qor: dict[str, Any],
    trajectory: dict[str, Any],
) -> dict[str, Any]:
    episode = dict(trajectory)
    episode.setdefault("sample_id", sample_id)
    generated_his = _read_project_json(generated_project, "system_his.json")
    episode.setdefault("oracle_his", None)
    episode.setdefault("generated_his", generated_his)
    episode.setdefault("his_validation", _his_validation_from_labels(labels))
    episode.setdefault("req_his_fidelity", _empty_req_his_fidelity())
    if "oracle_profile" in episode:
        episode["oracle_profile"] = _sanitize_oracle_profile(episode.get("oracle_profile"))
    episode["derived_training_views"] = _derived_training_views_metadata(
        sample_id,
        episode.get("derived_training_views"),
    )
    episode["project"] = _merge_project_episode_metadata(
        episode.get("project"),
        _project_episode_metadata(generated_project),
    )
    episode.setdefault("verification", _verification_episode_metadata(labels, measured_qor))
    if _is_independent_oracle_episode(episode):
        episode["verification"] = _verification_without_label_mismatches(episode.get("verification"))
    episode.setdefault("data_release", _data_release_tiers())
    return episode


def _source_episode_id(sample_id: str, episode: dict[str, Any]) -> str:
    episode_id = str(episode.get("sample_id", "")).strip()
    return episode_id or sample_id


def _training_view_eligibility(
    *,
    sample_id: str,
    requirement_present: bool,
    system_his_present: bool,
    final_file_paths: list[str],
    metadata: dict[str, Any],
    episode: dict[str, Any],
    labels: dict[str, Any],
    decision_phase: str,
) -> dict[str, Any]:
    terminal_candidate = bool(final_file_paths)
    automatic_pass_credit = _automatic_pass_credit(labels, episode)
    provenance_compliant = _explicit_compliance(labels, episode, "provenance")
    budget_compliant = _budget_compliance(labels, episode, metadata)
    vpp_l3 = _explicit_vpp_l3(labels, episode)
    h_stages_applicable = _training_h_stage_applicability(
        metadata, episode, system_his_present
    )
    file_origins = {
        path: _file_origin_from_episode(episode, path)
        for path in final_file_paths
    }

    common_reasons: list[str] = []
    if not terminal_candidate:
        common_reasons.append("terminal_candidate_missing")
    if automatic_pass_credit is not True:
        common_reasons.append("automatic_pass_credit_not_explicit_true")
    if provenance_compliant is not True:
        common_reasons.append("provenance_compliance_not_explicit_true")
    if budget_compliant is not True:
        common_reasons.append("budget_compliance_not_explicit_true")
    source = str(metadata.get("source", "")).strip()
    generator_provider = str(metadata.get("generator_provider", "")).strip()
    if not source or not generator_provider:
        common_reasons.append("generation_source_provenance_missing")
    if metadata.get("failure_origin") == "deterministic_template":
        common_reasons.append("deterministic_reference_not_training_source")
    boundary = metadata.get("requirement_boundary")
    boundary_disposition = boundary.get("disposition") if isinstance(boundary, dict) else None
    if boundary_disposition != "ready":
        if isinstance(boundary_disposition, str) and boundary_disposition:
            common_reasons.append(f"requirement_boundary_{boundary_disposition}")
        else:
            common_reasons.append("requirement_boundary_not_explicit_ready")
    if any(origin == "unknown" for origin in file_origins.values()):
        common_reasons.append("file_provenance_incomplete")
    if _patch_credit_is_incomplete(episode):
        common_reasons.append("patch_credit_not_explicit_true")
    official_hidden_count = metadata.get("official_hidden_outcome_reference_count")
    if official_hidden_count != 0:
        common_reasons.append("official_hidden_outcome_reference_count_not_zero")
    if _contains_contract_version(episode, "official-hidden-outcome-v1"):
        common_reasons.append("official_hidden_outcome_reference_forbidden")

    requirement_reasons = [] if requirement_present else ["requirement_missing"]
    if not system_his_present:
        his_reasons = ["system_his_missing"]
    elif h_stages_applicable is True:
        his_reasons = _his_positive_reasons(episode)
    else:
        his_reasons = ["h_stages_not_applicable_for_his_view"]
    if h_stages_applicable is True:
        project_h_reasons = _his_positive_reasons(episode)
    elif h_stages_applicable is False:
        project_h_reasons = []
    else:
        project_h_reasons = ["h_stage_applicability_unknown"]
    project_reasons = _verified_project_reasons(episode, vpp_l3)

    views = {
        "requirement_to_his": _view_eligibility(
            [
                *common_reasons,
                *requirement_reasons,
                *his_reasons,
                *(
                    []
                    if labels.get("generated_his_pass_credit") is True
                    else ["generated_his_pass_credit_not_explicit_true"]
                ),
            ]
        ),
        "his_to_project": _view_eligibility(
            [*common_reasons, *his_reasons, *project_reasons]
        ),
        "requirement_to_project": _view_eligibility(
            [
                *common_reasons,
                *requirement_reasons,
                *project_h_reasons,
                *project_reasons,
            ]
        ),
        "requirement_to_file": _view_eligibility(
            [
                *common_reasons,
                *requirement_reasons,
                *project_h_reasons,
                *project_reasons,
            ]
        ),
    }
    return {
        "sample_id": sample_id,
        "source_episode_id": _source_episode_id(sample_id, episode),
        "policy_id": _TRAINING_VIEW_POLICY_ID,
        "policy_version": _TRAINING_VIEW_POLICY_VERSION,
        "decision_phase": decision_phase,
        "source": source or None,
        "generator_provider": generator_provider or None,
        "terminal_candidate": terminal_candidate,
        "automatic_pass_credit": automatic_pass_credit,
        "provenance_compliant": provenance_compliant,
        "budget_compliant": budget_compliant,
        "vpp_l3": vpp_l3,
        "h_stages_applicable": h_stages_applicable,
        "requirement_disposition": boundary_disposition,
        "file_provenance": file_origins,
        "views": views,
    }


def _view_eligibility(reasons: list[str]) -> dict[str, Any]:
    unique_reasons = list(dict.fromkeys(reasons))
    return {
        "eligible": not unique_reasons,
        "reasons": unique_reasons,
        "policy_id": _TRAINING_VIEW_POLICY_ID,
        "policy_version": _TRAINING_VIEW_POLICY_VERSION,
    }


def _contains_contract_version(value: Any, contract_version: str) -> bool:
    if isinstance(value, dict):
        if value.get("contract_version") == contract_version:
            return True
        return any(
            _contains_contract_version(item, contract_version) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_contract_version(item, contract_version) for item in value)
    return False


def _automatic_pass_credit(labels: dict[str, Any], episode: dict[str, Any]) -> bool | None:
    value = labels.get("automatic_pass_credit")
    measurement = episode.get("measurement")
    if isinstance(measurement, dict):
        final = measurement.get("final")
        if isinstance(final, dict) and final.get("automatic_pass_credit") is False:
            return False
    return value if isinstance(value, bool) else None


def _explicit_compliance(
    labels: dict[str, Any], episode: dict[str, Any], name: str
) -> bool | None:
    values: list[bool] = []
    label_value = labels.get(f"{name}_compliant")
    if isinstance(label_value, bool):
        values.append(label_value)
    section = episode.get(name)
    if isinstance(section, dict):
        compliant = section.get("compliant")
        if isinstance(compliant, bool):
            values.append(compliant)
        status = section.get("status")
        if status == "compliant":
            values.append(True)
        elif status in {"violation", "noncompliant"}:
            values.append(False)
    if False in values:
        return False
    return True if True in values else None


def _explicit_vpp_l3(labels: dict[str, Any], episode: dict[str, Any]) -> bool | None:
    values: list[bool] = []
    value = labels.get("vpp_l3")
    if isinstance(value, bool):
        values.append(value)
    verification = episode.get("verification")
    if isinstance(verification, dict):
        vpp = verification.get("vpp_l3")
        if isinstance(vpp, dict):
            status = vpp.get("status")
            if status == "pass":
                values.append(True)
            elif status == "fail":
                values.append(False)
    if False in values:
        return False
    return True if True in values else None


def _budget_compliance(
    labels: dict[str, Any], episode: dict[str, Any], metadata: dict[str, Any]
) -> bool | None:
    explicit = _explicit_compliance(labels, episode, "budget")
    if explicit is not True:
        return explicit
    summary = metadata.get("model_call_budget")
    if not isinstance(summary, dict):
        return False
    maximum = summary.get("max_model_calls")
    used = summary.get("model_calls_used")
    failed = summary.get("model_calls_failed")
    remaining = summary.get("remaining_model_calls")
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in (maximum, used, failed, remaining)
    ):
        return False
    if used > maximum or failed > used or remaining != maximum - used:
        return False
    calls = summary.get("calls")
    if not isinstance(calls, list) or len(calls) != used:
        return False
    for call_id, call in enumerate(calls):
        if not isinstance(call, dict) or call.get("call_id") != call_id:
            return False
        if call.get("status") not in {"completed", "failed"}:
            return False
    if sum(call["status"] == "failed" for call in calls) != failed:
        return False
    # A consistent call ledger is necessary evidence, but it cannot attest the
    # independently frozen token, retry, repair, tool, wall-time, and EDA
    # ceilings.  Only an evaluator-produced all-axis compliance result may make
    # a positive training target eligible.
    return True


def _patch_credit_is_incomplete(episode: dict[str, Any]) -> bool:
    patches = episode.get("patches")
    if not isinstance(patches, list):
        return False
    return any(
        not isinstance(patch, dict) or patch.get("automatic_pass_credit") is not True
        for patch in patches
    )


def _training_h_stage_applicability(
    metadata: dict[str, Any], episode: dict[str, Any], system_his_present: bool
) -> bool | None:
    method_condition = str(metadata.get("method_condition", "")).strip().upper()
    if method_condition:
        method_token = method_condition.replace("_", " ").replace("-", " ").split()[0]
        method_match = re.fullmatch(r"M([0-6])[A-Z]*", method_token)
        if method_match is not None:
            return int(method_match.group(1)) >= 3
    if str(metadata.get("contract_skeleton_mode", "")).strip() == "legacy_full_project":
        return False
    validation = episode.get("his_validation")
    if isinstance(validation, dict):
        if validation.get("not_applicable_reason") == "method_does_not_emit_system_his":
            return False
        h0 = validation.get("h0")
        h0_status = h0.get("status") if isinstance(h0, dict) else None
        if h0_status in {"pass", "fail", "not_run"}:
            return True
        if h0_status == "not_applicable":
            return False
    return False if not system_his_present else None


def _his_positive_reasons(episode: dict[str, Any]) -> list[str]:
    validation = episode.get("his_validation")
    if not isinstance(validation, dict):
        return ["his_validation_missing"]
    reasons: list[str] = []
    for stage in ("h0", "h1", "h2"):
        record = validation.get(stage)
        status = record.get("status") if isinstance(record, dict) else None
        if status != "pass":
            reasons.append(f"{stage}_not_pass")
    h3 = validation.get("h3")
    h3_status = h3.get("status") if isinstance(h3, dict) else None
    if h3_status not in {"pass", "not_applicable"}:
        reasons.append("h3_not_pass_or_not_applicable")
    return reasons


def _verified_project_reasons(
    episode: dict[str, Any], vpp_l3: bool | None
) -> list[str]:
    reasons: list[str] = []
    if vpp_l3 is not True:
        reasons.append("vpp_l3_not_explicit_true")
    verification = episode.get("verification")
    if not isinstance(verification, dict):
        return [*reasons, "verification_missing"]
    for stage in ("l0", "l1", "l3"):
        record = verification.get(stage)
        status = record.get("status") if isinstance(record, dict) else None
        if status != "pass":
            reasons.append(f"{stage}_not_pass")
    l2 = verification.get("l2_core")
    if not isinstance(l2, dict):
        l2 = verification.get("l2")
    if not isinstance(l2, dict):
        reasons.extend(["public_l2_not_pass", "hidden_l2_not_pass"])
    else:
        public = l2.get("public")
        public_status = public.get("status") if isinstance(public, dict) else l2.get("status")
        hidden = l2.get("hidden")
        hidden_status = hidden.get("status") if isinstance(hidden, dict) else None
        if public_status != "pass":
            reasons.append("public_l2_not_pass")
        if hidden_status != "pass":
            reasons.append("hidden_l2_not_pass")
    return reasons


def _file_origin_from_episode(episode: dict[str, Any], path: str) -> str:
    project = episode.get("project")
    files = project.get("files") if isinstance(project, dict) else None
    metadata = files.get(path) if isinstance(files, dict) else None
    origin = metadata.get("origin") if isinstance(metadata, dict) else None
    origin_source = metadata.get("origin_source") if isinstance(metadata, dict) else None
    return origin if origin_source == "explicit" and origin in _KNOWN_FILE_ORIGINS else "unknown"


_ORACLE_KINDS = frozenset({"python_reference"})
_ORACLE_STATUSES = frozenset({"pass", "fail", "not_run", "infrastructure_error"})
_SCENARIO_STATUSES = frozenset({"pass", "fail", "not_run"})
_SCENARIO_CLASSES = frozenset(
    {"public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"}
)
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SAFE_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sanitize_oracle_profile(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    kind = raw.get("kind")
    status = raw.get("status")
    valid_kind = isinstance(kind, str) and kind in _ORACLE_KINDS
    profile: dict[str, Any] = {
        "kind": kind if valid_kind else "python_reference",
        "status": (
            status
            if valid_kind and isinstance(status, str) and status in _ORACLE_STATUSES
            else "not_run"
        ),
    }
    for key in (
        "family_id",
        "reference_model",
        "reference_version",
        "skip_reason",
        "failure_origin",
        "failure_type",
    ):
        token = _safe_token(raw.get(key))
        if token is not None:
            profile[key] = token
    bundle_sha256 = raw.get("bundle_sha256")
    if isinstance(bundle_sha256, str) and _SAFE_SHA256.fullmatch(bundle_sha256):
        profile["bundle_sha256"] = bundle_sha256

    scenario_counts = raw.get("scenario_counts")
    if isinstance(scenario_counts, dict):
        profile["scenario_counts"] = {
            name: count
            for name, count in scenario_counts.items()
            if name in _SCENARIO_CLASSES and _is_non_negative_int(count)
        }
    class_status = raw.get("class_status")
    if isinstance(class_status, dict):
        profile["class_status"] = {
            name: class_value
            for name, class_value in class_status.items()
            if name in _SCENARIO_CLASSES
            and isinstance(class_value, str)
            and class_value in _SCENARIO_STATUSES
        }
    scenarios: list[dict[str, Any]] = []
    raw_scenarios = raw.get("scenarios")
    if isinstance(raw_scenarios, list):
        for raw_scenario in raw_scenarios:
            if not isinstance(raw_scenario, dict):
                continue
            scenario_class = raw_scenario.get("scenario_class")
            scenario_id = _safe_token(raw_scenario.get("scenario_id"))
            if (
                not isinstance(scenario_class, str)
                or scenario_class not in _SCENARIO_CLASSES
                or scenario_id is None
            ):
                continue
            scenario: dict[str, Any] = {
                "scenario_id": scenario_id,
                "scenario_class": scenario_class,
            }
            seed_sha256 = raw_scenario.get("seed_sha256")
            if isinstance(seed_sha256, str) and _SAFE_SHA256.fullmatch(seed_sha256):
                scenario["seed_sha256"] = seed_sha256
            for key in ("transaction_count", "input_record_width_bits", "expected_record_width_bits"):
                if _is_non_negative_int(raw_scenario.get(key)):
                    scenario[key] = raw_scenario[key]
            for key in ("input_fields", "expected_fields"):
                fields = _sanitize_oracle_fields(raw_scenario.get(key))
                if fields:
                    scenario[key] = fields
            if scenario_class == "public_smoke":
                for key in ("input_sha256", "expected_sha256"):
                    digest = raw_scenario.get(key)
                    if isinstance(digest, str) and _SAFE_SHA256.fullmatch(digest):
                        scenario[key] = digest
            scenarios.append(scenario)
    if scenarios:
        profile["scenarios"] = scenarios
    profile["hidden_vectors_exported"] = False
    return profile


def _sanitize_oracle_fields(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    fields: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        name = _safe_token(raw.get("name"))
        msb = raw.get("msb")
        lsb = raw.get("lsb")
        signed = raw.get("signed")
        if (
            name is not None
            and _is_non_negative_int(msb)
            and _is_non_negative_int(lsb)
            and msb >= lsb
            and isinstance(signed, bool)
        ):
            fields.append({"name": name, "msb": msb, "lsb": lsb, "signed": signed})
    return fields


def _safe_token(value: Any) -> str | None:
    return value if isinstance(value, str) and _SAFE_TOKEN.fullmatch(value) else None


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


_WITHHELD_SCENARIO_CLASSES = _SCENARIO_CLASSES - {"public_smoke"}
_WITHHELD_CONTEXT_KEYS = _WITHHELD_SCENARIO_CLASSES | {"hidden"}
_WITHHELD_DIAGNOSTIC_KEYS = frozenset(
    {
        "scenario_id",
        "scenario_class",
        "status",
        "failure_origin",
        "failure_type",
        "stage",
        "signal",
        "cycle",
        "transaction_id",
        "mismatch_type",
        "tool_status",
    }
)
_PUBLIC_MISMATCH_KEYS = _WITHHELD_DIAGNOSTIC_KEYS | {"expected", "actual"}
_SAFE_DIAGNOSTIC_TOKEN_KEYS = frozenset(
    {
        "scenario_id",
        "scenario_class",
        "status",
        "failure_origin",
        "failure_type",
        "stage",
        "signal",
        "mismatch_type",
        "tool_status",
        "patch_id",
        "diagnosis_id",
        "format",
    }
)
_SAFE_DIAGNOSTIC_INT_KEYS = frozenset({"cycle", "transaction_id"})
_SAFE_DIAGNOSTIC_BOOL_KEYS = frozenset(
    {"allowed_edit_regions_respected", "touched_trusted_artifacts", "automatic_pass_credit"}
)
_RAW_TRAINING_KEYS = frozenset(
    {
        "seed",
        "stdout",
        "stderr",
        "command",
        "raw_log",
        "raw_path",
        "evaluator_path",
    }
)


def _sanitize_training_payload(
    value: Any,
    *,
    withheld: bool = False,
    independent_oracle: bool = False,
    _scope: str | None = None,
) -> Any:
    scope = _scope or ("withheld" if withheld else "root" if independent_oracle else "legacy")
    if isinstance(value, dict):
        scenario_class = value.get("scenario_class")
        if scope == "withheld":
            local_scope = "withheld"
        elif scope == "untrusted":
            local_scope = (
                "withheld"
                if isinstance(scenario_class, str) and scenario_class in _WITHHELD_SCENARIO_CLASSES
                else "untrusted"
            )
        elif scenario_class == "public_smoke":
            local_scope = "public"
        elif isinstance(scenario_class, str) and scenario_class in _WITHHELD_SCENARIO_CLASSES:
            local_scope = "withheld"
        elif "scenario_class" in value:
            local_scope = "untrusted"
        elif scope == "candidate":
            local_scope = "untrusted"
        else:
            local_scope = scope
        result: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_")
            if _is_raw_training_key(normalized):
                continue
            child_scope = (
                "withheld"
                if normalized in _WITHHELD_CONTEXT_KEYS
                else "candidate"
                if local_scope == "root"
                else local_scope
            )
            if isinstance(item, (dict, list, tuple)):
                if local_scope == "withheld":
                    continue
                if _safe_token(normalized) is None:
                    continue
                sanitized = _sanitize_training_payload(
                    item,
                    independent_oracle=independent_oracle,
                    _scope=child_scope,
                )
                if local_scope == "legacy" or sanitized not in ({}, []):
                    result[key] = sanitized
                continue
            if local_scope == "legacy":
                result[key] = item
            elif _safe_diagnostic_scalar(normalized, item, local_scope):
                result[key] = item
        return result
    if isinstance(value, (list, tuple)):
        item_scope = "candidate" if scope == "root" else scope
        sanitized_items = [
            _sanitize_training_payload(
                item,
                independent_oracle=independent_oracle,
                _scope=item_scope,
            )
            for item in value
        ]
        return [item for item in sanitized_items if item not in ({}, [])]
    return value if scope == "legacy" else None


def _safe_diagnostic_scalar(key: str, value: Any, scope: str) -> bool:
    allowed = _PUBLIC_MISMATCH_KEYS if scope == "public" else _WITHHELD_DIAGNOSTIC_KEYS
    if key not in allowed and key not in _SAFE_DIAGNOSTIC_BOOL_KEYS:
        return False
    if key in _SAFE_DIAGNOSTIC_TOKEN_KEYS:
        if key == "scenario_class":
            return value in _SCENARIO_CLASSES
        if key == "status":
            return value in _ORACLE_STATUSES
        return _safe_token(value) is not None
    if key in _SAFE_DIAGNOSTIC_INT_KEYS:
        return _is_non_negative_int(value)
    if key in _SAFE_DIAGNOSTIC_BOOL_KEYS:
        return isinstance(value, bool)
    if key in {"expected", "actual"}:
        return value is None or isinstance(value, (bool, int, float)) or (
            isinstance(value, str) and len(value) <= 256 and "\n" not in value and "\r" not in value
        )
    return False


def _is_raw_training_key(key: str) -> bool:
    if key in _RAW_TRAINING_KEYS or key.endswith("_seed"):
        return True
    return key.startswith("raw_") and ("log" in key or "path" in key)


def _is_independent_oracle_episode(episode: Any) -> bool:
    if not isinstance(episode, dict):
        return False
    profile = episode.get("oracle_profile")
    if not isinstance(profile, dict) or profile.get("kind") != "python_reference":
        return False
    return profile.get("skip_reason") not in {"disabled_by_config", "unsupported_family"}


def _verification_without_label_mismatches(value: Any) -> dict[str, Any]:
    verification = dict(value) if isinstance(value, dict) else {}
    l2_core = dict(verification.get("l2_core")) if isinstance(verification.get("l2_core"), dict) else {}
    public = dict(l2_core.get("public")) if isinstance(l2_core.get("public"), dict) else {}
    public["mismatch_detail"] = []
    l2_core["public"] = public
    verification["l2_core"] = l2_core
    return verification


def _derived_training_views_metadata(sample_id: str, existing: Any) -> dict[str, Any]:
    views = dict(existing) if isinstance(existing, dict) else {}
    req2file = views.get("req2file")
    req2file = dict(req2file) if isinstance(req2file, dict) else {}
    req2file.update(
        {
            "available": True,
            "official_eval_unit": False,
            "standalone_pass_credit": False,
            "source_episode_id": sample_id,
        }
    )
    views["req2file"] = req2file
    return views


def _read_project_json(project: GeneratedProject, path: str) -> dict[str, Any] | None:
    content = project.files.get(path)
    if content is None:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _empty_req_his_fidelity() -> dict[str, Any]:
    return {
        "interface_extraction": None,
        "clock_reset_fidelity": None,
        "parameter_fidelity": None,
        "behavior_intent_fidelity": None,
        "verification_intent_fidelity": None,
        "constraint_fidelity": None,
    }


def _his_validation_from_labels(labels: dict[str, Any]) -> dict[str, Any]:
    return {
        stage: {"status": str(labels.get(f"{stage}_status", "not_run")), "diagnostics": []}
        for stage in ("h0", "h1", "h2", "h3")
    }


def _merge_project_episode_metadata(existing: Any, defaults: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(existing, dict):
        return defaults
    merged = dict(defaults)
    merged.update(existing)
    explicit_files = existing.get("files")
    explicit_files = explicit_files if isinstance(explicit_files, dict) else {}
    files: dict[str, dict[str, Any]] = {}
    for path, default_metadata in defaults["files"].items():
        metadata = dict(default_metadata)
        explicit_metadata = explicit_files.get(path)
        if isinstance(explicit_metadata, dict):
            origin = explicit_metadata.get("origin")
            metadata = {**explicit_metadata, **metadata}
            metadata["origin"] = origin if origin in _KNOWN_FILE_ORIGINS else "unknown"
            metadata["origin_source"] = (
                "explicit" if origin in _KNOWN_FILE_ORIGINS else "invalid"
            )
        files[path] = metadata
    merged["files"] = files
    merged.update(_project_provenance_summary(files))
    return merged


def _project_episode_metadata(project: GeneratedProject) -> dict[str, Any]:
    files = {
        path: _project_file_metadata(path, content)
        for path, content in sorted(project.files.items())
    }
    return {
        "files": files,
        "behavior_hole_count": sum(item["behavior_holes"] for item in files.values()),
        **_project_provenance_summary(files),
    }


def _project_file_metadata(path: str, content: str) -> dict[str, Any]:
    return {
        "origin": _project_file_origin(path),
        "origin_source": "missing",
        "bytes": len(content.encode("utf-8")),
        "behavior_holes": _behavior_hole_count(content),
    }


def _project_file_origin(path: str) -> str:
    del path
    return "unknown"


def _project_provenance_summary(files: dict[str, dict[str, Any]]) -> dict[str, Any]:
    deterministic_artifacts = [
        path for path, item in files.items() if item.get("origin") == "deterministic"
    ]
    model_generated_artifacts = [
        path for path, item in files.items() if item.get("origin") == "model_generated"
    ]
    unknown_artifacts = [
        path for path, item in files.items() if item.get("origin") not in _KNOWN_FILE_ORIGINS
    ]
    total_bytes = sum(
        item.get("bytes", 0) for item in files.values() if isinstance(item.get("bytes"), int)
    )
    model_bytes = sum(
        item.get("bytes", 0)
        for item in files.values()
        if item.get("origin") == "model_generated" and isinstance(item.get("bytes"), int)
    )
    return {
        "deterministic_artifacts": deterministic_artifacts,
        "model_generated_artifacts": model_generated_artifacts,
        "unknown_provenance_artifacts": unknown_artifacts,
        "provenance_complete": not unknown_artifacts,
        "model_token_fraction": (
            round(model_bytes / total_bytes, 6)
            if total_bytes and not unknown_artifacts
            else None
        ),
    }


def _behavior_hole_count(content: str) -> int:
    delimited = content.count("__BEHAVIOR_HOLE__")
    plain = content.replace("__BEHAVIOR_HOLE__", "").count("BEHAVIOR_HOLE")
    todo = content.count("TODO_BEHAVIOR")
    return delimited + plain + todo


def _verification_episode_metadata(labels: dict[str, Any], measured_qor: dict[str, Any]) -> dict[str, Any]:
    checks = labels.get("checks", {})
    checks = checks if isinstance(checks, dict) else {}
    return {
        "l0": {"status": _check_status(checks.get("l0_complete")), "errors": []},
        "l1": {
            "status": _check_status(checks.get("l1_lint_pass")),
            "warnings": _dict_list(labels.get("l1_warnings")),
            "errors": [],
        },
        "l2_core": _l2_core_verification_metadata(labels, checks),
        "l2s": {
            "status": _check_status(checks.get("l2s_pass")),
            "divergences": _string_list(checks.get("l2s_divergences")),
        },
        "l3": {
            "status": _check_status(checks.get("l3_synth_pass")),
            "lut": measured_qor.get("lut"),
            "ff": measured_qor.get("ff"),
            "bram": measured_qor.get("bram"),
            "dsp": measured_qor.get("dsp"),
            "cells": measured_qor.get("cells"),
            "warnings": _dict_list(labels.get("l3_warnings")),
            "bram_miss": bool(labels.get("l3_bram_miss", False)),
        },
        "l4_open": _l4_open_verification_metadata(labels, measured_qor, checks),
        "l4_commercial": _l4_commercial_verification_metadata(labels, measured_qor, checks),
        "l4_agreement": {"class": str(checks.get("l4_agreement_class", "not_applicable"))},
        "l5": {"status": "not_run", "log_path": None},
    }


def _l2_core_verification_metadata(
    labels: dict[str, Any], checks: dict[str, Any]
) -> dict[str, Any]:
    status = labels.get("l2_sim_status", checks.get("l2_sim_status"))
    if status not in {"pass", "fail", "not_run"}:
        status = _check_status(checks.get("l2_sim_pass"))
    skip_reason = labels.get("l2_sim_skip_reason", checks.get("l2_sim_skip_reason"))
    if status == "not_run" and not isinstance(skip_reason, str):
        skip_reason = "not_reached"
    public = {
        "status": status,
        "mismatch_detail": _dict_list(labels.get("l2_mismatch_detail")),
    }
    result = {
        "status": status,
        "public": public,
        "hidden": {"status": _check_status(checks.get("l2_hidden_pass"))},
        "stress": {"status": _check_status(checks.get("l2_stress_pass"))},
        "coverage": {
            "scenario_profile": checks.get("l2_coverage_profile"),
            "seeds": _int_list(checks.get("l2_coverage_seeds")),
        },
    }
    if status == "not_run":
        result["skip_reason"] = skip_reason
        public["skip_reason"] = skip_reason
    return result


def _l4_open_verification_metadata(
    labels: dict[str, Any], measured_qor: dict[str, Any], checks: dict[str, Any]
) -> dict[str, Any]:
    qor = measured_qor.get("l4_openxc7", {})
    qor = qor if isinstance(qor, dict) else {}
    status = labels.get("l4_open_status")
    if status not in {"pass", "fail", "not_run"}:
        legacy_pass = _first_present(checks, "l4_open_pass", "l4_lite_timing_pass")
        if legacy_pass is True:
            status = "pass"
        elif labels.get("l4_failure_family") or qor.get("status") == "fail":
            status = "fail"
        else:
            status = "not_run"
    skip_reason = labels.get("l4_open_skip_reason", qor.get("skip_reason"))
    if status == "not_run" and not isinstance(skip_reason, str):
        skip_reason = "l3_failed" if checks.get("l3_synth_pass") is False else "not_selected_by_policy"
    return {
        "tool": str(qor.get("tool", checks.get("l4_open_tool", "openxc7_nextpnr"))),
        "board_profile": qor.get("board_profile"),
        "constraint_scope": str(qor.get("constraint_scope", "logical_only")),
        "board_constraints_applied": qor.get("board_constraints_applied") is True,
        "status": status,
        "skip_reason": skip_reason if status == "not_run" else None,
        "wns_ns": qor.get("wns_ns"),
        "fmax_mhz": qor.get("fmax_mhz"),
        "lut": qor.get("lut"),
        "ff": qor.get("ff"),
        "bram": qor.get("bram"),
        "dsp": qor.get("dsp"),
        "drc_warnings": _string_list(qor.get("drc_warnings")),
        "critical_warnings": _string_list(qor.get("critical_warnings")),
        "runtime_sec": qor.get("runtime_sec"),
        "report_paths": _string_list(qor.get("report_paths")),
        "failure_family": labels.get("l4_failure_family", qor.get("failure_family")),
        "provenance": (
            dict(qor["provenance"])
            if isinstance(qor.get("provenance"), dict)
            else {}
        ),
    }


def _l4_commercial_verification_metadata(
    labels: dict[str, Any], measured_qor: dict[str, Any], checks: dict[str, Any]
) -> dict[str, Any]:
    qor = measured_qor.get("l4_commercial", {})
    qor = qor if isinstance(qor, dict) else {}
    status = labels.get("l4_commercial_status", qor.get("status"))
    if status not in {"pass", "fail", "not_run"}:
        status = _check_status(_first_present(checks, "l4_commercial_pass", "vivado_timing_pass"))
    skip_reason = labels.get("l4_commercial_skip_reason", qor.get("skip_reason"))
    return {
        "tool": str(qor.get("tool", checks.get("l4_commercial_tool", "vivado"))),
        "constraint_scope": str(qor.get("constraint_scope", "logical_only")),
        "board_constraints_applied": qor.get("board_constraints_applied") is True,
        "official_board_ready": qor.get("official_board_ready") is True,
        "status": status,
        "skip_reason": skip_reason if status == "not_run" else None,
        "wns_ns": qor.get("wns_ns"),
        "fmax_mhz": qor.get("fmax_mhz"),
        "lut": qor.get("lut"),
        "ff": qor.get("ff"),
        "bram": qor.get("bram"),
        "dsp": qor.get("dsp"),
        "drc_warnings": _string_list(qor.get("drc_warnings")),
        "expected_board_drc_exceptions": _string_list(qor.get("expected_board_drc_exceptions")),
        "invalidating_critical_warnings": _string_list(qor.get("invalidating_critical_warnings")),
        "methodology_warnings": _string_list(qor.get("methodology_warnings")),
        "runtime_sec": qor.get("runtime_sec"),
        "report_paths": _string_list(qor.get("report_paths")),
        "provenance": (
            dict(qor["provenance"])
            if isinstance(qor.get("provenance"), dict)
            else {}
        ),
    }


def _first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _check_status(value: Any) -> str:
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    return "not_run"


def _data_release_tiers() -> dict[str, str]:
    return {
        "requirement": "open_public",
        "oracle_his": "open_public",
        "generated_his": "open_public",
        "his_validation": "open_public",
        "req_his_fidelity": "open_public",
        "generated_project": "open_public",
        "open_tool_labels": "open_public",
        "l4_open": "open_public",
        "l4_commercial": "restricted_reference",
        "vivado_structured_metadata": "restricted_reference",
        "vivado_raw_artifacts": "internal_only",
    }


def _read_metadata(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "metadata.json"
    if not path.exists():
        return {}
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if "training_split" not in metadata:
        schema_version = str(metadata.get("system_his_schema_version", "legacy"))
        metadata["training_split"] = (
            load_system_his_compatibility_envelope()
            .classify(schema_version)
            .training_partition
        )
    return metadata


def _read_labels(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "eval" / "labels.json"
    if not path.exists():
        return {}
    labels = json.loads(path.read_text(encoding="utf-8"))
    return labels if isinstance(labels, dict) else {}


def _read_episode(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "eval" / "trajectory.json"
    if not path.exists():
        return {}
    episode = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(episode, dict):
        return {}
    result = dict(episode)
    if "oracle_profile" in result:
        result["oracle_profile"] = _sanitize_oracle_profile(result.get("oracle_profile"))
    if _is_independent_oracle_episode(result):
        result["verification"] = _verification_without_label_mismatches(result.get("verification"))
    return result


def _read_project_files(
    project_dir: Path, *, episode: dict[str, Any]
) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for path in sorted(item for item in project_dir.rglob("*") if item.is_file()):
        relative_path = path.relative_to(project_dir)
        if any(part.startswith(".") for part in relative_path.parts):
            continue
        files.append(
            {
                "path": relative_path.as_posix(),
                "content": path.read_text(encoding="utf-8"),
                "origin": _file_origin_from_episode(episode, relative_path.as_posix()),
            }
        )
    return files
