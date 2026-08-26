"""System-HIS-to-project skeleton fill generation."""

from __future__ import annotations

import json
from typing import Any

from sr2fpga_agent.contract_skeleton import build_contract_skeleton_project, merge_behavior_files
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.model_budget import record_parser_schema_retry
from sr2fpga_agent.parsers import parse_behavior_files
from sr2fpga_agent.prompts import _his_project_messages, _with_his_project_retry_feedback
from sr2fpga_agent.providers import OpenAICompatibleClient
from sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers
from sr2fpga_agent.system_his_v12_checker import check_system_his_v12_against_rtl

class HisProjectGenerator:
    """Generate a project package from a checked System-HIS v1.2 contract."""

    def __init__(self, client: OpenAICompatibleClient, max_attempts: int = 1) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def generate(
        self,
        request: ProjectRequest,
        platform: PlatformProfile,
        system_his: dict[str, Any],
    ) -> GeneratedProject:
        messages = _his_project_messages(request, platform, system_his)
        skeleton = build_contract_skeleton_project(request, platform, system_his)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.stream_chat(messages)
            try:
                behavior_files = parse_behavior_files(content)
                project = merge_behavior_files(skeleton, behavior_files)
                identifier_issues = check_rtl_identifiers(project, _project_rtl_sources(project))
                if identifier_issues:
                    raise ValueError(
                        "HIS2PROJECT RTL failed identifier check: "
                        + "; ".join(
                            f"{issue.path}:{issue.line}: Verilog reserved keyword '{issue.identifier}' used as {issue.context}"
                            for issue in identifier_issues
                        )
                    )
                contract_result = check_system_his_v12_against_rtl(system_his, project)
                if not contract_result.passed:
                    raise ValueError(
                        "HIS2PROJECT RTL failed System-HIS v1.2 cross-check: "
                        + "; ".join(contract_result.errors)
                    )
                return project
            except ValueError as exc:
                last_error = exc
                if _attempt + 1 < self.max_attempts:
                    record_parser_schema_retry(self.client, "parse_behavior_or_contract")
                    messages = _with_his_project_retry_feedback(messages, str(exc), content)
        if last_error is not None:
            raise last_error
        raise RuntimeError("HIS2PROJECT generator did not run")


def _project_rtl_sources(project: GeneratedProject) -> list[str]:
    try:
        manifest = json.loads(project.files.get("manifest.json", "{}"))
    except json.JSONDecodeError:
        manifest = {}
    sources = manifest.get("sources")
    if isinstance(sources, list):
        return [source for source in sources if isinstance(source, str) and source.endswith(".v")]
    return sorted(path for path in project.files if path.endswith(".v"))
