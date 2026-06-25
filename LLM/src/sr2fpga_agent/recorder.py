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
        _write_json(eval_dir / "labels.json", labels)
        _write_json(eval_dir / "measured_qor.json", measured_qor)
        _write_json(eval_dir / "tool_versions.json", tool_versions)
        _write_json(eval_dir / "trajectory.json", trajectory)
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
            requirement = requirement_path.read_text(encoding="utf-8").strip() if requirement_path.exists() else ""
            system_his = json.loads(his_path.read_text(encoding="utf-8")) if his_path.exists() else None
            final_files = _read_project_files(final_project_dir) if final_project_dir.exists() else []

            if requirement_path.exists() and his_path.exists():
                requirement_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "requirement": requirement,
                        "system_his": system_his,
                    }
                )

            if system_his is not None and final_files:
                his_project_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "system_his": system_his,
                        "files": final_files,
                    }
                )
                requirement_project_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "requirement": requirement,
                        "files": final_files,
                    }
                )

            if final_files and predicted_qor_path.exists():
                predicted_qor_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "files": final_files,
                        "predicted_qor": json.loads(predicted_qor_path.read_text(encoding="utf-8")),
                    }
                )

            if final_files and measured_qor_path.exists():
                measured_qor_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
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
                                "attempt_id": attempt_dir.name,
                                "diagnosis": diagnosis,
                            }
                        )
                    if diagnosis_path.exists() and patch_path.exists():
                        patch_rows.append(
                            {
                                "sample_id": sample_id,
                                "metadata": metadata,
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


def _read_metadata(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "metadata.json"
    if not path.exists():
        return {}
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if "training_split" not in metadata:
        schema_version = str(metadata.get("system_his_schema_version", "legacy"))
        metadata["training_split"] = "clean" if schema_version == "system-his-v1.2" else "quarantine"
    return metadata


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
