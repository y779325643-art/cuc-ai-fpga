"""Dataset recording utilities for SR2FPGA generated samples."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ToolResult


@dataclass(frozen=True)
class AttemptRecord:
    """One generation or repair attempt and its tool outcomes."""

    attempt_id: int
    generated_project: GeneratedProject
    tool_results: dict[str, ToolResult]
    diagnosis: dict[str, Any] | None = None
    patch_diff: str = ""


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
        sample_dir = self.dataset_root / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "requirement.txt").write_text(requirement.rstrip() + "\n", encoding="utf-8")
        _write_json(sample_dir / "platform_profile.json", asdict(platform_profile))
        if metadata is not None:
            _write_json(sample_dir / "metadata.json", metadata)
        return sample_dir

    def write_attempt(self, sample_id: str, attempt: AttemptRecord) -> Path:
        attempt_dir = self.dataset_root / sample_id / "attempts" / f"attempt_{attempt.attempt_id:03d}"
        _write_project(attempt_dir / "generated_project", attempt.generated_project)
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
        return attempt_dir

    def write_final(
        self,
        sample_id: str,
        generated_project: GeneratedProject,
        labels: dict[str, Any],
        measured_qor: dict[str, Any],
        tool_versions: dict[str, str],
        trajectory: dict[str, Any],
    ) -> Path:
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
                    if diagnosis_path.exists():
                        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
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
                                "diagnosis": json.loads(diagnosis_path.read_text(encoding="utf-8")),
                                "patch": patch_path.read_text(encoding="utf-8"),
                            }
                        )

        _write_jsonl(output_dir / "requirement_to_his.jsonl", requirement_rows)
        _write_jsonl(output_dir / "his_to_project.jsonl", his_project_rows)
        _write_jsonl(output_dir / "requirement_to_project.jsonl", requirement_project_rows)
        _write_jsonl(output_dir / "failure_to_diagnosis.jsonl", diagnosis_rows)
        _write_jsonl(output_dir / "failure_to_patch.jsonl", patch_rows)
        _write_jsonl(output_dir / "project_to_predicted_qor.jsonl", predicted_qor_rows)
        _write_jsonl(output_dir / "project_to_measured_qor.jsonl", measured_qor_rows)


def _write_project(project_dir: Path, project: GeneratedProject) -> None:
    for relative_path, content in project.files.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")


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
    episode.setdefault("req_his_fidelity", _empty_req_his_fidelity())
    episode["project"] = _merge_project_episode_metadata(
        episode.get("project"),
        _project_episode_metadata(generated_project),
    )
    episode.setdefault("verification", _verification_episode_metadata(labels, measured_qor))
    episode.setdefault("data_release", _data_release_tiers())
    return episode


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
    if path.startswith("constraints/") or path.startswith("reports/"):
        return "deterministic"
    if path.startswith("rtl/") or path.startswith("sim/"):
        return "model_generated"
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
            "warnings": [],
            "errors": [],
        },
        "l2_core": {
            "status": _check_status(checks.get("l2_sim_pass")),
            "public": {"status": _check_status(checks.get("l2_sim_pass")), "mismatch_detail": []},
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
            "bram_miss": False,
        },
        "l4_open": {
            "tool": str(checks.get("l4_open_tool", "openxc7_nextpnr")),
            "status": _check_status(_first_present(checks, "l4_open_pass", "l4_lite_timing_pass")),
        },
        "l4_commercial": {
            "tool": str(checks.get("l4_commercial_tool", "vivado")),
            "status": _check_status(_first_present(checks, "l4_commercial_pass", "vivado_timing_pass")),
        },
        "l4_agreement": {"class": str(checks.get("l4_agreement_class", "not_applicable"))},
        "l5": {"status": "not_run", "log_path": None},
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
    return episode if isinstance(episode, dict) else {}


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
