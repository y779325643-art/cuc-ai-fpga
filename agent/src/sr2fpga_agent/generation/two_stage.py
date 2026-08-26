"""Two-stage REQ2HIS then HIS2PROJECT generation."""

from __future__ import annotations

import json
import time
from typing import Any, Callable

from sr2fpga_agent.generation.his2project import HisProjectGenerator
from sr2fpga_agent.generation.req2his import SystemHisGenerator
from sr2fpga_agent.his_validation import (
    SystemHisValidationError,
    validate_system_his_payload_h_stages,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.model_budget import client_for_stage
from sr2fpga_agent.providers import OpenAICompatibleClient

class TwoStageProjectGenerator:
    """Generate a project through REQ2HIS followed by HIS2PROJECT."""

    def __init__(
        self,
        client: OpenAICompatibleClient,
        max_attempts: int = 1,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.system_his_generator = SystemHisGenerator(
            client_for_stage(client, "req2his"),
            max_attempts=max_attempts,
            event_sink=event_sink,
        )
        self.his_project_generator = HisProjectGenerator(
            client_for_stage(client, "his2project"),
            max_attempts=max_attempts,
        )
        self.event_sink = event_sink

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        system_his = self.generate_system_his(request, platform)
        return self.generate_from_system_his(request, platform, system_his)

    def generate_system_his(self, request: ProjectRequest, platform: PlatformProfile) -> dict[str, Any]:
        system_his = self._run_stage(
            "req2his",
            request,
            lambda: self.system_his_generator.generate(request, platform),
        )
        return system_his

    def generate_from_system_his(
        self,
        request: ProjectRequest,
        platform: PlatformProfile,
        system_his: dict[str, Any],
    ) -> GeneratedProject:
        validation_report = validate_system_his_payload_h_stages(
            request,
            system_his,
            platform=platform,
        )
        if not validation_report["passed"]:
            raise SystemHisValidationError(
                json.dumps(system_his, ensure_ascii=False),
                validation_report,
            )
        return self._run_stage(
            "his2project",
            request,
            lambda: self.his_project_generator.generate(request, platform, system_his),
        )

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
