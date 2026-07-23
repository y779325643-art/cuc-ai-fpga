"""Requirement-to-System-HIS generation."""

from __future__ import annotations

from typing import Any, Callable

from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.parsers import parse_system_his_v12
from sr2fpga_agent.prompts import _system_his_v12_messages, _with_system_his_retry_feedback
from sr2fpga_agent.providers import OpenAICompatibleClient
from sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity

class DeepSeekSystemHisGenerator:
    """Generate a System-HIS v1.2 architecture contract from a short request."""

    def __init__(
        self,
        client: OpenAICompatibleClient,
        max_attempts: int = 3,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.client = client
        self.max_attempts = max_attempts
        self.event_sink = event_sink

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> dict[str, Any]:
        messages = _system_his_v12_messages(request, platform)
        last_error: ValueError | None = None
        for attempt_id in range(self.max_attempts):
            content = self.client.stream_chat(messages)
            try:
                system_his = parse_system_his_v12(content)
                fidelity = check_system_his_req_fidelity(request, system_his)
                if not fidelity.passed:
                    raise ValueError("DeepSeek System-HIS REQ2HIS fidelity failed: " + "; ".join(fidelity.errors))
                return system_his
            except ValueError as exc:
                last_error = exc
                if attempt_id + 1 < self.max_attempts:
                    self._emit_retry_event(request, attempt_id, exc)
                messages = _with_system_his_retry_feedback(messages, str(exc), content, task_type=request.task_type)
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek System-HIS generator did not run")

    def _emit_retry_event(self, request: ProjectRequest, attempt_id: int, exc: ValueError) -> None:
        if self.event_sink is None:
            return
        self.event_sink(
            {
                "event": "generation_stage_retry",
                "stage": "req2his",
                "attempt_id": attempt_id,
                "project_name": request.project_name,
                "task_type": request.task_type,
                "width": request.width,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
