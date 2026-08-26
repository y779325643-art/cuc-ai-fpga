"""Direct requirement-to-project generation."""

from __future__ import annotations

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.model_budget import record_parser_schema_retry
from sr2fpga_agent.parsers import parse_project_files
from sr2fpga_agent.prompts import _project_messages
from sr2fpga_agent.providers import OpenAICompatibleClient

class DirectProjectGenerator:
    """Generate a project package directly from a requirement."""

    def __init__(self, client: OpenAICompatibleClient, max_attempts: int = 1) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        messages = _project_messages(request, platform)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(
                    content,
                    expected_task_type=request.task_type,
                    manifest_policy="canonical",
                )
                return GeneratedProject(project_name=request.project_name, files=files)
            except ValueError as exc:
                last_error = exc
                if _attempt + 1 < self.max_attempts:
                    record_parser_schema_retry(self.client, "parse_project_files")
        if last_error is not None:
            raise last_error
        raise RuntimeError("Direct project generator did not run")
