"""M2 untyped planning and project emission from frozen public context."""

from __future__ import annotations

from typing import Any, Mapping

from sr2fpga_agent.frozen_context import (
    FrozenRequirementContext,
    frozen_public_project_request,
)
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.parsers import parse_project_files
from sr2fpga_agent.prompts import (
    _frozen_project_from_untyped_plan_messages,
    _frozen_untyped_plan_messages,
)


class FrozenContextUntypedPlanFacade:
    """Two-call M2 facade with no typed architecture or hidden metadata."""

    def __init__(self, plan_client: Any, project_client: Any) -> None:
        self._plan_client = plan_client
        self._project_client = project_client

    def emit_plan(self, context: FrozenRequirementContext) -> Mapping[str, Any]:
        factory = getattr(self._plan_client, "with_output_format", None)
        client = factory("text") if callable(factory) else self._plan_client
        plan_text = client.stream_chat(
            _frozen_untyped_plan_messages(context)
        ).strip()
        if not plan_text:
            raise ValueError("M2 untyped plan must be non-empty")
        return {"plan_text": plan_text}

    def emit_project(
        self,
        context: FrozenRequirementContext,
        plan: Mapping[str, Any],
    ) -> GeneratedProject:
        if set(plan) != {"plan_text"} or not isinstance(plan["plan_text"], str):
            raise ValueError("M2 planning artifact must contain only plan_text")
        plan_text = plan["plan_text"].strip()
        if not plan_text:
            raise ValueError("M2 untyped plan must be non-empty")
        project_name = frozen_public_project_request(context).project_name
        content = self._project_client.stream_chat(
            _frozen_project_from_untyped_plan_messages(
                context,
                plan_text,
                project_name=project_name,
            )
        )
        files = parse_project_files(
            content,
            expected_task_type=None,
            manifest_policy="canonical",
        )
        return GeneratedProject(project_name, files)
