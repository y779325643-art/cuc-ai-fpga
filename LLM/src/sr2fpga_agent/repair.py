"""LLM-backed generated-project repair."""

from __future__ import annotations

from typing import Any

from LLM.src.sr2fpga_agent.models import GeneratedProject, RepairResult
from LLM.src.sr2fpga_agent.parsers import (
    _diagnosis_mentions_path,
    _minimize_repaired_project,
    _project_system_his_schema,
    _project_task_type,
    _validate_repair_preserves_l0_when_not_repairing_l0,
    _validate_system_his_contract_unchanged,
    diff_projects,
    parse_project_files,
    parse_system_his_v12,
)
from LLM.src.sr2fpga_agent.path_safety import build_patch_metadata
from LLM.src.sr2fpga_agent.prompts import _repair_messages
from LLM.src.sr2fpga_agent.providers import OpenAICompatibleClient
from LLM.src.sr2fpga_agent.system_his_v12_checker import SCHEMA_VERSION as SYSTEM_HIS_V12_SCHEMA

class DeepSeekRepairer:
    """Repair a generated project package using DeepSeek and a tool diagnosis."""

    def __init__(self, client: OpenAICompatibleClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def repair(self, project: GeneratedProject, diagnosis: dict[str, object]) -> RepairResult:
        messages = _repair_messages(project, diagnosis)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(content, expected_task_type=_project_task_type(project.files))
                if _project_system_his_schema(project.files) == SYSTEM_HIS_V12_SCHEMA:
                    original_system_his: dict[str, Any] | None = None
                    try:
                        original_system_his = parse_system_his_v12(project.files["system_his.json"])
                    except ValueError:
                        original_system_his = None
                    try:
                        repaired_system_his = parse_system_his_v12(files["system_his.json"])
                    except ValueError as exc:
                        raise ValueError(f"DeepSeek repair system_his.json failed validation: {exc}") from exc
                    if original_system_his is not None and not _diagnosis_mentions_path(diagnosis, "system_his.json"):
                        try:
                            _validate_system_his_contract_unchanged(original_system_his, repaired_system_his)
                        except ValueError as exc:
                            raise ValueError(f"System-HIS v1.2 contract changed during RTL repair: {exc}") from exc
                repaired_project = _minimize_repaired_project(
                    project,
                    GeneratedProject(project_name=project.project_name, files=files),
                    diagnosis,
                )
                if _project_system_his_schema(project.files) == SYSTEM_HIS_V12_SCHEMA:
                    _validate_repair_preserves_l0_when_not_repairing_l0(repaired_project, diagnosis)
                patch_metadata = build_patch_metadata(project, repaired_project, diagnosis)
                return RepairResult(
                    generated_project=repaired_project,
                    patch_diff=diff_projects(project, repaired_project),
                    patch_metadata=patch_metadata,
                )
            except ValueError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek repairer did not run")
