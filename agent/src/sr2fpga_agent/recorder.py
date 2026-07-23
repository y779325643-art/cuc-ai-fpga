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
        _write_json(eval_dir / "labels.json", labels)
        _write_json(eval_dir / "measured_qor.json", measured_qor)
        _write_json(eval_dir / "tool_versions.json", tool_versions)
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

        for sample_dir in sorted(path for path in self.dataset_root.iterdir() if path.is_dir()):
            sample_id = sample_dir.name
            requirement_path = sample_dir / "requirement.txt"
            final_project_dir = sample_dir / "final" / "generated_project"
            his_path = final_project_dir / "system_his.json"
            predicted_qor_path = final_project_dir / "reports" / "predicted_qor.json"
            measured_qor_path = sample_dir / "eval" / "measured_qor.json"
            metadata = _read_metadata(sample_dir)
            episode = _read_episode(sample_dir)
            independent_oracle = _is_independent_oracle_episode(episode)
            requirement = requirement_path.read_text(encoding="utf-8").strip() if requirement_path.exists() else ""
            system_his = json.loads(his_path.read_text(encoding="utf-8")) if his_path.exists() else None
            final_files = _read_project_files(final_project_dir) if final_project_dir.exists() else []

            if requirement_path.exists() and his_path.exists():
                requirement_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": episode,
                        "requirement": requirement,
                        "system_his": system_his,
                    }
                )

            if system_his is not None and final_files:
                his_project_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": episode,
                        "system_his": system_his,
                        "files": final_files,
                    }
                )
                requirement_project_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": episode,
                        "requirement": requirement,
                        "files": final_files,
                    }
                )
                for file_item in final_files:
                    requirement_file_rows.append(
                        {
                            "sample_id": sample_id,
                            "source_episode_id": _source_episode_id(sample_id, episode),
                            "view": "req2file",
                            "official_eval_unit": False,
                            "standalone_pass_credit": False,
                            "metadata": metadata,
                            "episode": episode,
                            "requirement": requirement,
                            "file_path": file_item["path"],
                            "file_content": file_item["content"],
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
    if isinstance(existing.get("files"), dict):
        files = dict(defaults["files"])
        files.update(existing["files"])
        merged["files"] = files
    return merged


def _project_episode_metadata(project: GeneratedProject) -> dict[str, Any]:
    files = {
        path: _project_file_metadata(path, content)
        for path, content in sorted(project.files.items())
    }
    model_bytes = sum(item["bytes"] for item in files.values() if item["origin"] == "model_generated")
    total_bytes = sum(item["bytes"] for item in files.values())
    return {
        "files": files,
        "deterministic_artifacts": [
            path
            for path, item in files.items()
            if item["origin"] == "deterministic"
        ],
        "model_generated_artifacts": [
            path
            for path, item in files.items()
            if item["origin"] == "model_generated"
        ],
        "model_token_fraction": round(model_bytes / total_bytes, 6) if total_bytes else None,
        "behavior_hole_count": sum(item["behavior_holes"] for item in files.values()),
    }


def _project_file_metadata(path: str, content: str) -> dict[str, Any]:
    return {
        "origin": _project_file_origin(path),
        "bytes": len(content.encode("utf-8")),
        "behavior_holes": _behavior_hole_count(content),
    }


def _project_file_origin(path: str) -> str:
    if path == "system_his.json" or path == "manifest.json":
        return "deterministic"
    if path.startswith("constraints/"):
        return "deterministic"
    if path.startswith("rtl/") or path.startswith("sim/"):
        return "model_generated"
    if path == "reports/predicted_qor.json":
        return "model_generated"
    if path.startswith("reports/"):
        return "deterministic"
    return "unknown"


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
        "l2_core": {
            "status": _check_status(checks.get("l2_sim_pass")),
            "public": {
                "status": _check_status(checks.get("l2_sim_pass")),
                "mismatch_detail": _dict_list(labels.get("l2_mismatch_detail")),
            },
            "hidden": {"status": _check_status(checks.get("l2_hidden_pass"))},
            "stress": {"status": _check_status(checks.get("l2_stress_pass"))},
            "coverage": {
                "scenario_profile": checks.get("l2_coverage_profile"),
                "seeds": _int_list(checks.get("l2_coverage_seeds")),
            },
        },
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
        metadata["training_split"] = "clean" if schema_version == "system-his-v1.2" else "quarantine"
    return metadata


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


def _read_project_files(project_dir: Path) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for path in sorted(item for item in project_dir.rglob("*") if item.is_file()):
        relative_path = path.relative_to(project_dir)
        if any(part.startswith(".") for part in relative_path.parts):
            continue
        files.append(
            {
                "path": relative_path.as_posix(),
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return files
