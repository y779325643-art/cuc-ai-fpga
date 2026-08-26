"""Direct generation facades that consume only frozen public context."""

from __future__ import annotations

import re
from typing import Any, Mapping

from sr2fpga_agent.frozen_context import FrozenRequirementContext
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.parsers import parse_project_files
from sr2fpga_agent.prompts import _frozen_direct_project_messages
from sr2fpga_agent.repair import ProjectRepairer


class FrozenContextDirectProjectFacade:
    """One-call M0/M1 initial project facade without evaluator task metadata."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def emit_project(self, context: FrozenRequirementContext) -> GeneratedProject:
        project_name = _project_name(context.requirement_id)
        content = self._client.chat(
            _frozen_direct_project_messages(context, project_name=project_name)
        )
        files = parse_project_files(
            content,
            expected_task_type=None,
            manifest_policy="canonical",
        )
        return GeneratedProject(project_name=project_name, files=files)


class FrozenContextDirectProjectGenerator:
    """Legacy generator-shaped bridge that ignores ProjectRequest task metadata."""

    def __init__(self, client: Any, context: FrozenRequirementContext) -> None:
        self._facade = FrozenContextDirectProjectFacade(client)
        self._context = context

    def generate(self, request: Any, platform: Any) -> GeneratedProject:
        del request, platform
        return self._facade.emit_project(self._context)


class FrozenContextProjectRepairFacade:
    """M1 project repair facade; context is accepted but never augmented."""

    def __init__(self, client: Any) -> None:
        self._repairer = ProjectRepairer(client, max_attempts=1)

    def repair_project(
        self,
        context: FrozenRequirementContext,
        project: GeneratedProject,
        diagnosis: Mapping[str, Any],
    ) -> GeneratedProject:
        del context
        return self._repairer.repair(project, dict(diagnosis)).generated_project


def _project_name(requirement_id: str) -> str:
    suffix = re.sub(r"[^A-Za-z0-9]+", "_", requirement_id).strip("_")[-24:]
    return f"frozen_{suffix or 'requirement'}"
