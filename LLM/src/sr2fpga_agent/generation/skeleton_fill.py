"""Oracle System-HIS skeleton-fill generation."""

from __future__ import annotations

import time
from typing import Any, Callable

from LLM.src.sr2fpga_agent.generation.his2project import DeepSeekHisProjectGenerator
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.parsers import parse_system_his_v12
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.providers import OpenAICompatibleClient
from LLM.src.sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity

class DeepSeekOracleHisProjectGenerator:
    """Generate behavior files from deterministic oracle System-HIS v1.2."""

    his_source_used_for_generation = "oracle_fallback"

    def __init__(
        self,
        client: OpenAICompatibleClient,
        max_attempts: int = 3,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.oracle_generator = ProjectGenerator()
        self.his_project_generator = DeepSeekHisProjectGenerator(client, max_attempts=max_attempts)
        self.event_sink = event_sink

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        system_his = self._run_stage(
            "oracle_req2his",
            request,
            lambda: self._oracle_system_his(request, platform),
        )
        return self._run_stage(
            "his2project",
            request,
            lambda: self.his_project_generator.generate(request, platform, system_his),
        )

    def _oracle_system_his(self, request: ProjectRequest, platform: PlatformProfile) -> dict[str, Any]:
        project = self.oracle_generator.generate(request, platform)
        system_his = parse_system_his_v12(project.files["system_his.json"])
        fidelity = check_system_his_req_fidelity(request, system_his)
        if not fidelity.passed:
            raise ValueError("Oracle System-HIS REQ2HIS fidelity failed: " + "; ".join(fidelity.errors))
        return system_his

    def _run_stage(self, stage: str, request: ProjectRequest, action):
        start = time.monotonic()
        self._emit_stage_event("generation_stage_started", stage, request)
        try:
            result = action()
        except Exception as exc:
            self._emit_stage_event(
                "generation_stage_failed",
                stage,
                request,
                duration_seconds=time.monotonic() - start,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise
        self._emit_stage_event(
            "generation_stage_finished",
            stage,
            request,
            duration_seconds=time.monotonic() - start,
        )
        return result

    def _emit_stage_event(self, event: str, stage: str, request: ProjectRequest, **extra: Any) -> None:
        if self.event_sink is None:
            return
        self.event_sink(
            {
                "event": event,
                "stage": stage,
                "project_name": request.project_name,
                "task_type": request.task_type,
                "width": request.width,
                **extra,
            }
        )
