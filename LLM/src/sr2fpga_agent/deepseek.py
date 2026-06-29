"""OpenAI-compatible LLM providers for SR2FPGA project generation."""

from __future__ import annotations

import difflib
import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from LLM.src.sr2fpga_agent.contract_skeleton import build_contract_skeleton_project, merge_behavior_files
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, RepairResult
from LLM.src.sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0
from LLM.src.sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity
from LLM.src.sr2fpga_agent.system_his_v12_checker import SCHEMA_VERSION as SYSTEM_HIS_V12_SCHEMA
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12_against_rtl


REQUIRED_PROJECT_FILES = {
    "system_his.json",
    "manifest.json",
    "rtl/top.v",
    "constraints/timing.sdc",
    "sim/tb_top.v",
    "reports/predicted_qor.json",
}

MULTIMODULE_RTL_EXAMPLES = {
    "uart_tx": ["rtl/top.v", "rtl/baud_tick_gen.v", "rtl/uart_tx_core.v"],
    "spi_master": ["rtl/top.v", "rtl/clock_divider.v", "rtl/spi_master_core.v"],
    "pwm_controller": ["rtl/top.v", "rtl/pwm_timer.v", "rtl/pwm_channel.v"],
    "fir_filter": ["rtl/top.v", "rtl/mac_unit.v", "rtl/fir_filter_core.v"],
    "streaming_valid_ready": ["rtl/top.v", "rtl/skid_buffer.v", "rtl/stream_stage.v"],
    "matrix_vector_mac": [
        "rtl/top.v",
        "rtl/vector_rom.v",
        "rtl/mac_unit.v",
        "rtl/dot_product_engine.v",
    ],
    "composed_event_counter": ["rtl/top.v", "rtl/event_gate.v", "rtl/counter_core.v"],
    "composed_stream_accumulator": ["rtl/top.v", "rtl/skid_buffer.v", "rtl/accumulator_core.v"],
    "composed_stream_fork": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/stream_fork.v",
        "rtl/stream_stage.v",
    ],
    "composed_dual_stream_join": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/stream_join.v",
        "rtl/accumulator_core.v",
        "rtl/stream_stage.v",
    ],
    "composed_vector_mac_pipeline": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/vector_mac_core.v",
        "rtl/stream_stage.v",
    ],
    "composed_td_update_core": [
        "rtl/top.v",
        "rtl/td_input_stage.v",
        "rtl/discount_core.v",
        "rtl/td_update_core.v",
        "rtl/stream_stage.v",
    ],
}


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    """OpenAI-compatible chat completions API configuration."""

    api_key: str
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: int = 120
    transport_attempts: int = 3
    retry_backoff_seconds: float = 0.5


class OpenAICompatibleClient:
    """Small stdlib HTTP client for OpenAI-compatible chat completions."""

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = self._chat_payload(messages)
        data = self._request_with_retries(payload, _read_chat_completion_json)

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "OpenAI-compatible API response did not contain choices[0].message.content"
            ) from exc

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        payload = self._chat_payload(messages)
        payload["stream"] = True
        return self._request_with_retries(payload, _read_streaming_chat_content)

    def _chat_payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": _messages_for_model(self.config.model, messages),
            "temperature": 0.1,
        }
        if _model_supports_json_response_format(self.config.model):
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _request_with_retries(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        last_error: _TransientOpenAICompatibleError | None = None
        attempts = max(1, self.config.transport_attempts)
        for attempt in range(attempts):
            try:
                return self._request_once(payload, reader)
            except _TransientOpenAICompatibleError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                delay = self.config.retry_backoff_seconds * (attempt + 1)
                if delay > 0:
                    time.sleep(delay)
        if last_error is not None:
            raise RuntimeError(str(last_error)) from last_error
        raise RuntimeError("OpenAI-compatible API request did not run")

    def _request_once(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=_default_ssl_context(),
            ) as response:
                return reader(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"OpenAI-compatible API request failed with HTTP {exc.code}: {body}"
            if exc.code in TRANSIENT_HTTP_STATUS_CODES:
                raise _TransientOpenAICompatibleError(message) from exc
            raise RuntimeError(message) from exc
        except TimeoutError as exc:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API request timed out") from exc
        except urllib.error.URLError as exc:
            raise _TransientOpenAICompatibleError(f"OpenAI-compatible API request failed: {exc.reason}") from exc


@dataclass(frozen=True)
class AnthropicCompatibleConfig:
    """Anthropic Messages API configuration."""

    api_key: str
    model: str = "claude-opus-4-8"
    base_url: str = "https://api.anthropic.com/v1"
    timeout_seconds: int = 120
    max_tokens: int = 16384
    anthropic_version: str = "2023-06-01"
    transport_attempts: int = 3
    retry_backoff_seconds: float = 0.5


class AnthropicCompatibleClient:
    """Small stdlib HTTP client for Anthropic-compatible Messages APIs."""

    def __init__(self, config: AnthropicCompatibleConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        data = self._request_with_retries(_anthropic_messages_payload(self.config, messages))
        return _read_anthropic_message_text(data)

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        return self.chat(messages)

    def _request_with_retries(self, payload: dict[str, Any]) -> Any:
        last_error: _TransientOpenAICompatibleError | None = None
        attempts = max(1, self.config.transport_attempts)
        for attempt in range(attempts):
            try:
                return self._request_once(payload)
            except _TransientOpenAICompatibleError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                delay = self.config.retry_backoff_seconds * (attempt + 1)
                if delay > 0:
                    time.sleep(delay)
        if last_error is not None:
            raise RuntimeError(str(last_error)) from last_error
        raise RuntimeError("Anthropic-compatible API request did not run")

    def _request_once(self, payload: dict[str, Any]) -> Any:
        url = self.config.base_url.rstrip("/") + "/messages"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": self.config.anthropic_version,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=_default_ssl_context(),
            ) as response:
                return _read_chat_completion_json(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"Anthropic-compatible API request failed with HTTP {exc.code}: {body}"
            if exc.code in TRANSIENT_HTTP_STATUS_CODES:
                raise _TransientOpenAICompatibleError(message) from exc
            raise RuntimeError(message) from exc
        except TimeoutError as exc:
            raise _TransientOpenAICompatibleError("Anthropic-compatible API request timed out") from exc
        except urllib.error.URLError as exc:
            raise _TransientOpenAICompatibleError(f"Anthropic-compatible API request failed: {exc.reason}") from exc


def _default_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


TRANSIENT_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class _TransientOpenAICompatibleError(RuntimeError):
    pass


def _model_supports_json_response_format(model: str) -> bool:
    return not model.startswith("claude-")


def _messages_for_model(model: str, messages: list[dict[str, str]]) -> list[dict[str, str]]:
    if not model.startswith("claude-"):
        return messages
    system_parts: list[str] = []
    rewritten: list[dict[str, str]] = []
    for message in messages:
        role = message.get("role", "")
        content = str(message.get("content", ""))
        if role == "system":
            system_parts.append(content)
            continue
        rewritten.append({"role": role, "content": content})
    if not system_parts:
        return rewritten
    system_text = "\n\n".join(system_parts)
    if rewritten and rewritten[0].get("role") == "user":
        first = rewritten[0]
        rewritten[0] = {
            "role": "user",
            "content": f"System instructions:\n{system_text}\n\nUser request:\n{first.get('content', '')}",
        }
        return rewritten
    return [{"role": "user", "content": f"System instructions:\n{system_text}"}] + rewritten


def _read_chat_completion_json(response: Any) -> Any:
    return json.loads(response.read().decode("utf-8"))


def _anthropic_messages_payload(
    config: AnthropicCompatibleConfig,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    system_parts: list[str] = []
    anthropic_messages: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role", ""))
        content = str(message.get("content", ""))
        if role == "system":
            system_parts.append(content)
        elif role in {"user", "assistant"}:
            anthropic_messages.append({"role": role, "content": content})
    if not anthropic_messages:
        anthropic_messages.append({"role": "user", "content": "Return a JSON object."})
    payload: dict[str, Any] = {
        "model": config.model,
        "max_tokens": config.max_tokens,
        "messages": anthropic_messages,
        "temperature": 0.1,
    }
    if system_parts:
        payload["system"] = "\n\n".join(system_parts)
    return payload


def _read_anthropic_message_text(data: Any) -> str:
    try:
        content = data["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Anthropic-compatible API response did not contain content") from exc
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text") is not None:
                chunks.append(str(item["text"]))
        if chunks:
            return "".join(chunks)
    raise RuntimeError("Anthropic-compatible API response did not contain text content")


def _read_streaming_chat_content(response: Any) -> str:
    chunks: list[str] = []
    while True:
        raw_line = response.readline()
        if not raw_line:
            break
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if data == "[DONE]":
            break
        try:
            event = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI-compatible streaming response contained invalid chat completion data") from exc
        if isinstance(event, dict) and "error" in event:
            raise RuntimeError(f"OpenAI-compatible streaming response error: {event['error']}")
        choices = event.get("choices") if isinstance(event, dict) else None
        if not choices:
            continue
        try:
            delta = choices[0].get("delta", {})
        except (AttributeError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenAI-compatible streaming response contained invalid chat completion data") from exc
        content = delta.get("content")
        if content is not None:
            chunks.append(str(content))
    return "".join(chunks)


class DeepSeekProjectGenerator:
    """Generate a project package by asking DeepSeek for required files."""

    def __init__(self, client: OpenAICompatibleClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        messages = _project_messages(request, platform)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(content, expected_task_type=request.task_type)
                return GeneratedProject(project_name=request.project_name, files=files)
            except ValueError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek generator did not run")


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
            content = self.client.chat(messages)
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


class DeepSeekHisProjectGenerator:
    """Generate a project package from a checked System-HIS v1.2 contract."""

    def __init__(self, client: OpenAICompatibleClient, max_attempts: int = 3) -> None:
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
                    messages = _with_his_project_retry_feedback(messages, str(exc), content)
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek HIS2PROJECT generator did not run")


def _project_rtl_sources(project: GeneratedProject) -> list[str]:
    try:
        manifest = json.loads(project.files.get("manifest.json", "{}"))
    except json.JSONDecodeError:
        manifest = {}
    sources = manifest.get("sources")
    if isinstance(sources, list):
        return [source for source in sources if isinstance(source, str) and source.endswith(".v")]
    return sorted(path for path in project.files if path.endswith(".v"))


class DeepSeekTwoStageProjectGenerator:
    """Generate a project through REQ2HIS followed by HIS2PROJECT."""

    def __init__(
        self,
        client: OpenAICompatibleClient,
        max_attempts: int = 3,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.system_his_generator = DeepSeekSystemHisGenerator(
            client,
            max_attempts=max_attempts,
            event_sink=event_sink,
        )
        self.his_project_generator = DeepSeekHisProjectGenerator(client, max_attempts=max_attempts)
        self.event_sink = event_sink

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        system_his = self._run_stage(
            "req2his",
            request,
            lambda: self.system_his_generator.generate(request, platform),
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
                return RepairResult(
                    generated_project=repaired_project,
                    patch_diff=diff_projects(project, repaired_project),
                )
            except ValueError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek repairer did not run")


def parse_project_files(content: str, expected_task_type: str | None = None) -> dict[str, str]:
    """Parse DeepSeek JSON output into project files."""
    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek output is not valid JSON: {exc.msg}") from exc

    raw_files = payload.get("files")
    if isinstance(raw_files, dict):
        files = {str(path): str(file_content) for path, file_content in raw_files.items()}
    elif isinstance(raw_files, list):
        files = _files_from_list(raw_files)
    else:
        raise ValueError("DeepSeek output must contain files as an object or list")

    files = {path: _ensure_trailing_newline(content) for path, content in files.items()}
    missing = sorted(REQUIRED_PROJECT_FILES - set(files))
    if missing:
        raise ValueError(f"DeepSeek output is missing required files: {', '.join(missing)}")
    _validate_manifest(files)
    _validate_expected_rtl_structure(files, expected_task_type)
    return files


def parse_behavior_files(content: str) -> dict[str, str]:
    """Parse HIS2PROJECT JSON output into behavior-only file bodies."""

    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek HIS2PROJECT behavior output is not valid JSON: {exc.msg}") from exc
    if "files" in payload:
        raise ValueError("HIS2PROJECT response must contain behavior_files, not files")
    raw_behavior = payload.get("behavior_files")
    if not isinstance(raw_behavior, dict):
        raise ValueError("HIS2PROJECT response must contain behavior_files as an object")
    return {str(path): str(body) for path, body in raw_behavior.items()}


def parse_system_his_v12(content: str) -> dict[str, Any]:
    """Parse and validate DeepSeek output as System-HIS v1.2 JSON."""
    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek System-HIS output is not valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("DeepSeek System-HIS output must be a JSON object")
    system_his = payload.get("system_his", payload)
    if not isinstance(system_his, dict):
        raise ValueError("DeepSeek System-HIS output field system_his must be an object")

    result = check_system_his_v12(system_his)
    if not result.passed:
        raise ValueError("DeepSeek System-HIS v1.2 failed validation: " + "; ".join(result.errors))
    return system_his


def _validate_system_his_contract_unchanged(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    frozen_keys = ("schema_version", "top", "state", "components", "instances", "data_flow", "control_flow", "artifacts")
    for key in frozen_keys:
        if _canonical_json(expected.get(key)) != _canonical_json(actual.get(key)):
            raise ValueError(f"DeepSeek HIS2PROJECT changed frozen System-HIS contract section '{key}'")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def diff_projects(old: GeneratedProject, new: GeneratedProject) -> str:
    """Return a unified diff between two generated project file maps."""
    chunks: list[str] = []
    for path in sorted(set(old.files) | set(new.files)):
        old_content = old.files.get(path, "")
        new_content = new.files.get(path, "")
        if old_content == new_content:
            continue
        chunks.extend(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
    return "".join(chunks)


def _minimize_repaired_project(
    original: GeneratedProject,
    repaired: GeneratedProject,
    diagnosis: dict[str, object],
) -> GeneratedProject:
    files = dict(repaired.files)
    if (
        original.files.get("manifest.json") != repaired.files.get("manifest.json")
        and _manifest_is_valid_for_project(original.files)
        and not _diagnosis_mentions_path(diagnosis, "manifest.json")
    ):
        files["manifest.json"] = original.files["manifest.json"]
    return GeneratedProject(project_name=repaired.project_name, files=files)


def _manifest_is_valid_for_project(files: dict[str, str]) -> bool:
    try:
        _validate_manifest(files)
    except ValueError:
        return False
    return True


def _validate_repair_preserves_l0_when_not_repairing_l0(
    repaired_project: GeneratedProject,
    diagnosis: dict[str, object],
) -> None:
    if str(diagnosis.get("stage", "")) == "l0_consistency":
        return
    l0_result = check_project_l0(repaired_project)
    if l0_result.passed:
        return
    raise ValueError("DeepSeek repair introduced L0 contract violations: " + "; ".join(l0_result.errors))


def _diagnosis_mentions_path(diagnosis: dict[str, object], path: str) -> bool:
    affected_files = diagnosis.get("affected_files")
    if isinstance(affected_files, list) and path in {str(item) for item in affected_files}:
        return True
    return path.lower() in json.dumps(diagnosis, ensure_ascii=False).lower()


def _ensure_trailing_newline(content: str) -> str:
    return content if content.endswith("\n") else content + "\n"


def _validate_manifest(files: dict[str, str]) -> None:
    try:
        manifest = json.loads(files["manifest.json"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc

    missing_fields: list[str] = []
    if not isinstance(manifest.get("top_module"), str) or not manifest["top_module"]:
        missing_fields.append("top_module")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        missing_fields.append("sources")

    simulation = manifest.get("simulation")
    testbench = simulation.get("testbench") if isinstance(simulation, dict) else None
    if not isinstance(testbench, str) or not testbench:
        missing_fields.append("simulation.testbench")

    if missing_fields:
        raise ValueError(f"manifest.json missing required fields: {', '.join(missing_fields)}")

    missing_sources = sorted(path for path in sources if path not in files)
    if missing_sources:
        raise ValueError(f"manifest.json references missing source files: {', '.join(missing_sources)}")
    if testbench not in files:
        raise ValueError(f"manifest.json references missing testbench file: {testbench}")


def _validate_expected_rtl_structure(files: dict[str, str], expected_task_type: str | None) -> None:
    if expected_task_type not in MULTIMODULE_RTL_EXAMPLES:
        return

    manifest = json.loads(files["manifest.json"])
    sources = manifest["sources"]
    rtl_sources = [path for path in sources if path.startswith("rtl/") and path.endswith(".v")]
    if "rtl/top.v" not in rtl_sources:
        raise ValueError("manifest.json sources must include rtl/top.v for multi-module tasks")
    if len(rtl_sources) < 3:
        raise ValueError(
            "DeepSeek output for multi-module task "
            f"{expected_task_type} must include rtl/top.v and at least two submodule .v files"
        )


def _project_task_type(files: dict[str, str]) -> str | None:
    try:
        system_his = json.loads(files.get("system_his.json", "{}"))
    except json.JSONDecodeError:
        return None
    task_type = system_his.get("task_type")
    return task_type if isinstance(task_type, str) else None


def _project_system_his_schema(files: dict[str, str]) -> str:
    try:
        system_his = json.loads(files.get("system_his.json", "{}"))
    except json.JSONDecodeError:
        return ""
    schema_version = system_his.get("schema_version") if isinstance(system_his, dict) else ""
    return schema_version if isinstance(schema_version, str) else ""


def _files_from_list(raw_files: list[Any]) -> dict[str, str]:
    files: dict[str, str] = {}
    for item in raw_files:
        if not isinstance(item, dict) or "path" not in item or "content" not in item:
            raise ValueError("Each file entry must contain path and content")
        files[str(item["path"])] = str(item["content"])
    return files


def _strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _system_his_v12_messages(request: ProjectRequest, platform: PlatformProfile) -> list[dict[str, str]]:
    system = (
        "You are an FPGA system architect. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate RTL, testbench code, constraints, bitstreams, or tool reports."
    )
    user = f"""
Generate a canonical System-HIS v1.2 architecture contract for SR2FPGA.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- user_prompt: {request.description or "No extra user prompt provided."}

Target platform:
- name: {platform.name}
- vendor: {platform.vendor}
- family: {platform.family}
- part: {platform.part}
- board: {platform.board}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Return only System-HIS JSON with schema_version "system-his-v1.2".
Do not generate RTL or project files in this step.

Required top-level sections:
- intent
- top
- state
- components
- instances
- data_flow
- control_flow
- timing
- resources
- verification
- artifacts

Architectural rules:
- Start from top-level ports, interfaces, clocks, resets, and parameters.
- Every clock and reset declared in top.clocks/top.resets must also appear in top.ports.
- top.resets[].polarity must be active_low or active_high.
- top.resets[].kind must be sync or async.
- Use {{"name": "rst_n", "polarity": "active_low", "kind": "sync"}} unless the task explicitly says otherwise.
- Record architectural state, not incidental RTL temporaries.
- State names across registers, counters, fsms, buffers, and memories must be globally unique.
- Separate component definitions from concrete instances.
- Every component must include name, semantic_kind, source, ports, and intent.
- Every components[].source must be one of artifacts.rtl_sources.
- Do not use placeholder sources such as "library"; use concrete RTL paths like rtl/top.v.
- Every instance must include name, component, parameter_values, clock, reset, and owns_state.
- Every instances[].owns_state must be a JSON array; use [] when the instance owns no state.
- Every instances[].parameter_values key must be declared in that component's parameters.
- top.clocks[].target_fmax_mhz and timing.target_fmax_mhz must be positive numbers.
- Every data_flow endpoint must name top.<port> or <instance>.<port>.
- data_flow.timing is optional, but when present it must include
  latency_cycles >= 0, initiation_interval > 0, and optional non-empty throughput.
- Separate data movement from control rules.
- control_flow rules should use kinds such as reset_rule, handshake_rule,
  enable_rule, stall_rule, counter_update, fsm_transition, or buffer_occupancy.
- Structured control_flow rules should use when/effect objects when modeling
  machine-checkable behavior. The guard grammar allows atoms {"signal","op","value"} or
  all_of/any_of lists with depth <= 2; signal must reference a declared top port,
  top clock/reset, instance port, state, data_flow name, or <fsm>.state.
- control_flow.effect.target must reference a declared data_flow name or state name; do not target
  top ports, instance ports, all, or module names directly.
- Every state.fsms[] entry must declare owner or use <instance>.<fsm> naming.
- FSM owner must be top or an instances[].name.
- fsm_transition rules must reference a declared state.fsms entry and use
  from/to states declared by that FSM.
- Use width objects with expr and resolved when a parameterized width is useful.
- Keep verification as scenarios and pass_condition, not full testbench code.

{_system_his_v12_task_guidance(request.task_type)}

Return this JSON shape:
{{
  "schema_version": "system-his-v1.2",
  "intent": {{
    "user_prompt": "...",
    "design_goal": "...",
    "assumptions": []
  }},
  "top": {{
    "name": "top",
    "parameters": [],
    "clocks": [],
    "resets": [],
    "ports": [],
    "interfaces": []
  }},
  "state": {{
    "registers": [],
    "counters": [],
    "fsms": [],
    "buffers": [],
    "memories": []
  }},
  "components": [],
  "instances": [],
  "data_flow": [
    {{
      "name": "...",
      "path": ["top.input_port", "instance.input_port", "instance.output_port", "top.output_port"],
      "payload": {{"name": "...", "width": {{"expr": "DATA_WIDTH", "resolved": 8}}}},
      "protocol": "valid_ready",
      "timing": {{"latency_cycles": 1, "initiation_interval": 1, "throughput": "one transfer per cycle when ready"}}
    }}
  ],
  "control_flow": [
    {{
      "name": "...",
      "kind": "enable_rule",
      "when": {{"signal": "top.valid", "op": "==", "value": 1}},
      "effect": {{"action": "assert", "target": "..."}},
      "related_state": [],
      "related_flows": []
    }}
  ],
  "timing": {{
    "primary_clock": "clk",
    "target_fmax_mhz": 100,
    "constraints": ["constraints/timing.sdc"]
  }},
  "resources": {{
    "optimization_goal": "area_first",
    "expected": {{"lut": "low", "ff": "low", "bram": 0, "dsp": 0}}
  }},
  "verification": {{
    "testbench": "sim/tb_top.v",
    "scenarios": [],
    "pass_condition": "testbench prints TEST_PASS and no TEST_FAIL"
  }},
  "artifacts": {{
    "top_module": "top",
    "rtl_sources": [],
    "testbench": "sim/tb_top.v",
    "constraints": ["constraints/timing.sdc"],
    "manifest": "manifest.json",
    "predicted_qor": "reports/predicted_qor.json"
  }}
}}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _with_system_his_retry_feedback(
    messages: list[dict[str, str]],
    error: str,
    previous_content: str,
    task_type: str = "",
) -> list[dict[str, str]]:
    task_guidance = _system_his_v12_retry_guidance(task_type)
    return [
        *messages,
        {
            "role": "user",
            "content": (
                "Your previous System-HIS output failed validation. "
                "Repair that JSON in place and return a corrected complete System-HIS JSON object only.\n\n"
                "Validation error:\n"
                f"{error}\n\n"
                "System-HIS v1.2 IR repair checklist:\n"
                "- Every components[] object must include name, semantic_kind, source, ports, and intent.\n"
                "- Every components[].source must be one of artifacts.rtl_sources.\n"
                "- Do not use placeholder sources such as \"library\"; use concrete RTL paths like rtl/top.v.\n"
                "- Every instances[] object must include name, component, parameter_values, clock, reset, and owns_state.\n"
                "- Every instances[].owns_state must be a JSON array; use [] when the instance owns no state.\n"
                "- Every instances[].parameter_values key must be declared in that component's parameters.\n"
                "- Every instance name must be unique and every component value must match a declared components[].name.\n"
                "- Every top clock/reset should be listed in top.clocks/top.resets and also in top.ports.\n"
                "- top.clocks[].target_fmax_mhz and timing.target_fmax_mhz must be positive numbers.\n"
                "- top.resets[].polarity must be active_low or active_high.\n"
                "- top.resets[].kind must be sync or async.\n"
                "- Use {\"name\": \"rst_n\", \"polarity\": \"active_low\", \"kind\": \"sync\"} unless the task "
                "explicitly says otherwise.\n"
                "- data_flow.path endpoints must use top.<port> or <instance>.<port>; do not use component names as endpoints.\n"
                "- control_flow.when signal values must reference declared top ports, instance ports, state names, "
                "data_flow names, or <fsm>.state.\n"
                "- control_flow.effect.target must reference a declared data_flow name or state name; do not target "
                "top ports, instance ports, all, or module names directly.\n"
                "- State names across registers, counters, fsms, buffers, and memories must be globally unique; "
                "prefix repeated per-instance state names such as out0_valid_reg and out1_valid_reg.\n"
                "- Every state.fsms[] entry must declare owner or use <instance>.<fsm> naming.\n"
                "- FSM owner must be top or an instances[].name.\n"
                "- FSMs must declare non-empty states, initial, and reset_state, and transitions must use those states.\n\n"
                f"{task_guidance}\n"
                "Previous invalid System-HIS JSON:\n"
                f"{previous_content.strip()}"
            ),
        },
    ]


def _system_his_v12_task_guidance(task_type: str) -> str:
    if task_type == "composed_dual_stream_join":
        return (
            "Required architecture for composed_dual_stream_join:\n"
            "- components: skid_buffer, stream_join, accumulator_core, stream_stage\n"
            "- instances: in0_buffer, in1_buffer, join_core, accumulator, out_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- Do not use Verilog reserved keywords such as fork, join, or buf as instance names.\n"
            "- in0_buffer and in1_buffer must both reference component skid_buffer.\n"
            "- data_flow must use named path arrays, not from/to-only edges.\n"
            "- control_flow entries must each include name, kind, when/effect for structured rules, related_state, and related_flows.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/skid_buffer.v, rtl/stream_join.v, "
            "rtl/accumulator_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_vector_mac_pipeline":
        return (
            "Required architecture for composed_vector_mac_pipeline:\n"
            "- components: skid_buffer, vector_mac_core, stream_stage\n"
            "- instances: feature_buffer, weight_buffer, mac_core, score_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- feature_buffer and weight_buffer must both reference component skid_buffer.\n"
            "- vector_mac_core owns vector_index, accumulator, and pending_score state.\n"
            "- top ports must include feature_valid, feature_data, feature_ready, weight_valid, "
            "weight_data, weight_ready, bias, score_valid, score_data, and score_ready.\n"
            "- data_flow must pair feature and weight streams into vector_mac_core and stage score output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/skid_buffer.v, "
            "rtl/vector_mac_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_td_update_core":
        return (
            "Required architecture for composed_td_update_core:\n"
            "- components: td_input_stage, discount_core, td_update_core, stream_stage\n"
            "- instances: input_stage, discount, update, output_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- top ports must include in_valid, in_ready, reward, value, next_value, gamma, alpha, "
            "out_valid, out_ready, td_error, and updated_value.\n"
            "- td_input_stage owns captured reward/value/next_value state.\n"
            "- td_update_core or stream_stage owns td_error and updated_value state if registered.\n"
            "- data_flow must describe tuple capture, discount calculation, TD update, and output staging.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/td_input_stage.v, rtl/discount_core.v, "
            "rtl/td_update_core.v, and rtl/stream_stage.v."
        )
    if task_type == "composed_stream_fork":
        return (
            "Required architecture for composed_stream_fork:\n"
            "- components: skid_buffer, stream_fork, stream_stage\n"
            "- instances: input_buffer, fork_core, out0_stage, out1_stage\n"
            "- Do not collapse this topology into one fused component.\n"
            "- Do not use Verilog reserved keywords such as fork, join, or buf as instance names.\n"
            "- data_flow must use named path arrays and control_flow must reference existing state and flows."
        )
    if task_type == "composed_stream_accumulator":
        return (
            "Required architecture for composed_stream_accumulator:\n"
            "- components: skid_buffer, accumulator_core\n"
            "- instances: input_buffer, accumulator\n"
            "- data_flow must use named path arrays and control_flow must reference existing state and flows."
        )
    if task_type == "composed_event_counter":
        return (
            "Required architecture for composed_event_counter:\n"
            "- components: event_gate, counter_core\n"
            "- instances: event_gate, counter\n"
            "- data_flow must use named path arrays and control_flow must reference existing state and flows."
        )
    return ""


def _system_his_v12_retry_guidance(task_type: str) -> str:
    common = (
        "Task-specific retry guidance after checker failure:\n"
        "- Do not leave fsm, from, to, effect.action, or effect.target empty.\n"
        "- Do not emit fsm_transition unless state.fsms declares that FSM and its states.\n"
        "- If no FSM is needed, use handshake_rule, enable_rule, or stall_rule instead.\n"
    )
    if task_type == "composed_dual_stream_join":
        return (
            common
            + "- Required top ports: clk, rst_n, in0_valid, in0_data, in1_valid, in1_data, out_ready, "
            "in0_ready, in1_ready, out_valid, out_data\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_vector_mac_pipeline":
        return (
            common
            + "- Required top ports: clk, rst_n, feature_valid, feature_data, weight_valid, "
            "weight_data, bias, score_ready, feature_ready, weight_ready, score_valid, score_data\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_td_update_core":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, reward, value, next_value, gamma, alpha, "
            "out_ready, in_ready, out_valid, td_error, updated_value\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_stream_fork":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, out0_ready, out1_ready, "
            "in_ready, out0_valid, out0_data, out1_valid, out1_data\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_stream_accumulator":
        return (
            common
            + "- Required top ports: clk, rst_n, in_valid, in_data, in_ready, sample_valid, sum\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
    if task_type == "composed_event_counter":
        return common + "- Required top ports: clk, rst_n, event_valid, count\n"
    return common


def _his_project_messages(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, Any],
) -> list[dict[str, str]]:
    system_his_text = json.dumps(system_his, ensure_ascii=False, indent=2)
    skeleton_files = build_contract_skeleton_project(request, platform, system_his).files
    skeleton_text = json.dumps(skeleton_files, ensure_ascii=False, indent=2)
    behavior_paths = [path for path, content in sorted(skeleton_files.items()) if "BEHAVIOR_HOLE" in content]
    behavior_entries = "\n".join(f'    "{path}": "...",' for path in behavior_paths).rstrip(",")
    system = (
        "You generate behavioral RTL bodies for checked System-HIS architecture contracts. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Generate behavior bodies for a contract-preserving SR2FPGA Verilog RTL skeleton.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- user_prompt: {request.description or "No extra user prompt provided."}

Platform:
- name: {platform.name}
- vendor: {platform.vendor}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Checked System-HIS v1.2:
{system_his_text}

Contract-preserving deterministic skeleton:
{skeleton_text}

Rules:
- Treat the System-HIS as the frozen architecture contract.
- Use the deterministic skeleton as the structural source of truth.
- Preserve module headers, top-level port lists, instance names, parameter
  overrides, manifest sources, timing constraints, and testbench top instantiation
  from the skeleton.
- Fill BEHAVIOR_HOLE regions with behavioral RTL only; do not create structural
  names that are absent from the checked System-HIS.
- Do not change component, instance, top port, data_flow, or control_flow names.
- Generate RTL that implements the top-down architecture contract.
- Use declared FSM state localparams from the deterministic skeleton when
  implementing state machines.
- Do not rename, omit, or replace System-HIS state.fsms states; every declared
  state name must remain visible in the generated RTL module.
- Do not use Verilog reserved keywords for any RTL identifier, including modules,
  instances, regs, wires, arrays, blocks, and parameters. Avoid names such as
  fork, join, buf, begin, end, module, wire, input, output, and reg.
- Do not return system_his.json, manifest.json, rtl/top.v, constraints, testbench,
  reports, complete modules, module headers, or endmodule lines.
- The deterministic skeleton already supplies structure, constraints, manifest,
  reports, and testbench. Your output supplies only replacement text for each
  BEHAVIOR_HOLE marker.
{_icarus_testbench_rules()}

Behavior files with BEHAVIOR_HOLE markers:
{json.dumps(behavior_paths, ensure_ascii=False, indent=2)}

Return JSON in this exact shape. The value of each behavior file must be a JSON
string; escape newlines as \\n and escape any double quotes inside file contents:
{{
  "behavior_files": {{
{behavior_entries}
  }}
}}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _with_his_project_retry_feedback(
    messages: list[dict[str, str]],
    error: str,
    previous_content: str,
) -> list[dict[str, str]]:
    return [
        *messages,
        {
            "role": "user",
            "content": (
                "Your previous behavior_files output failed validation. "
                "Repair that JSON in place and return a corrected complete behavior_files JSON object only.\n\n"
                "Validation error:\n"
                f"{error}\n\n"
                "HIS2PROJECT behavior repair checklist:\n"
                "- Return behavior_files only, not files.\n"
                "- Each behavior_files value must contain only the replacement body for one BEHAVIOR_HOLE.\n"
                "- Do not include module declarations, module headers, port lists, or endmodule lines.\n"
                "- Do not return system_his.json, manifest.json, rtl/top.v, constraints, testbench, or reports.\n\n"
                "Previous invalid behavior_files JSON:\n"
                f"{previous_content.strip()}"
            ),
        },
    ]


def _project_messages(request: ProjectRequest, platform: PlatformProfile) -> list[dict[str, str]]:
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    rtl_contract = _rtl_contract_for_task(request.task_type)
    system = (
        "You generate complete FPGA RTL project packages as JSON. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Generate a Verilog RTL project package for SR2FPGA.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- description: {request.description or "No extra description provided."}

Platform:
- name: {platform.name}
- vendor: {platform.vendor}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Required files:
{required_files}

RTL structure:
{rtl_contract}

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
{_additional_project_file_entries(request.task_type)}
    "constraints/timing.sdc": "...",
    "sim/tb_top.v": "...",
    "reports/predicted_qor.json": "..."
  }}
}}

The manifest.json file content must itself be JSON and must contain this tool
pipeline schema:
{{
  "project_name": "{request.project_name}",
  "top_module": "top",
  "sources": {_manifest_sources_example(request.task_type)},
  "constraints": {{"timing": "constraints/timing.sdc"}},
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}

The Verilog must be synthesizable and the testbench must print TEST_PASS on success.
{_icarus_testbench_rules()}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _repair_messages(project: GeneratedProject, diagnosis: dict[str, object]) -> list[dict[str, str]]:
    files_text = "\n\n".join(
        f"### {path}\n{content}" for path, content in sorted(project.files.items())
    )
    diagnosis_text = json.dumps(diagnosis, ensure_ascii=False, indent=2)
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    task_type = _project_task_type(project.files)
    rtl_contract = _repair_rtl_contract(project.files, task_type)
    system_his_prompt = _repair_system_his_prompt(project.files, project.project_name)
    system = (
        "You repair FPGA RTL project packages as JSON. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Repair this SR2FPGA project package.

Failure diagnosis:
{diagnosis_text}

Current project files:
{files_text}

Required files:
{required_files}

RTL structure:
{rtl_contract}

Preserve every file that is not needed for the fix byte-for-byte. If
manifest.json already has a valid top_module, sources, and simulation.testbench,
copy the original manifest.json unchanged unless the failure log specifically
points to manifest.json.

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
{_additional_repair_file_entries(project.files, task_type)}
    "constraints/timing.sdc": "...",
    "sim/tb_top.v": "...",
    "reports/predicted_qor.json": "..."
  }}
}}

The manifest.json file content must itself be JSON and must contain this tool
pipeline schema:
{{
  "project_name": "{project.project_name}",
  "top_module": "top",
  "sources": {_repair_sources_example(project.files, task_type)},
  "constraints": {{"timing": "constraints/timing.sdc"}},
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}

{system_his_prompt}

Make the smallest practical fix for the failing tool log. Preserve pure
Verilog RTL and ensure the testbench prints TEST_PASS on success.
{_icarus_testbench_rules()}
{_unused_parameter_repair_rules(diagnosis)}
{_functional_mismatch_repair_rules(diagnosis)}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _icarus_testbench_rules() -> str:
    return (
        "Testbench portability rules:\n"
        "- The testbench must compile with Icarus Verilog using iverilog -g2012.\n"
        "- Do not initialize unpacked arrays with aggregate literals such as "
        "`reg [7:0] seq [0:2] = {8'd1, 8'd2, 8'd3};`.\n"
        "- Use initial block assignments instead, for example `seq[0] = 8'd1;`.\n"
        "- Drive and withdraw valid-ready stimulus away from the DUT sampling edge, "
        "for example on negedge clk for posedge-clocked RTL.\n"
        "- Do not hold input valid high until out_valid; deassert or advance each "
        "input valid after its own input ready handshake so one packet cannot be "
        "accepted repeatedly while the testbench waits for output.\n"
        "- Observe outputs after nonblocking assignments have settled, for example on "
        "negedge clk or after an explicit small delay from posedge clk.\n"
        "- After wait(out_valid), check the current transaction before advancing to another "
        "active clock edge; use a small delay or negedge observation in the same valid cycle.\n"
        "- Exercise back-to-back valid-ready transfers so stream buffers, joins, and "
        "accumulators cannot drop a sample between consecutive handshakes.\n"
        "- For streaming designs, check each output transaction against the expected "
        "sequence; do not only check the final output value.\n"
        "- Every wait loop must be bounded with a cycle counter and must print TEST_FAIL on timeout."
    )


def _functional_mismatch_repair_rules(diagnosis: dict[str, object]) -> str:
    if str(diagnosis.get("failure_type", "")) != "functional_mismatch":
        return ""
    return (
        "Functional mismatch repair rules:\n"
        "- Do not make the testbench pass by changing expected values to match the observed wrong output.\n"
        "- For functional mismatches, prefer fixing RTL behavior, handshake timing, state updates, or reset behavior.\n"
        "- For valid-ready stream mismatches, check for each lost or duplicated valid-ready transfer before changing tests.\n"
        "- Only change expected values when the diagnosis explicitly says the testbench expectation is wrong."
    )


def _unused_parameter_repair_rules(diagnosis: dict[str, object]) -> str:
    if "unusedparam" not in str(diagnosis.get("root_cause", "")).lower():
        return ""
    return (
        "Unused parameter repair rules:\n"
        "- If you remove an unused parameter, the module declaration and every instantiation must agree.\n"
        "- Either use the parameter in real RTL logic, or remove the parameter override from all instantiations.\n"
        "- Do not silence a lint warning by creating a new PINNOTFOUND or parameter mismatch error."
    )


def _rtl_contract_for_task(task_type: str) -> str:
    example_sources = MULTIMODULE_RTL_EXAMPLES.get(task_type)
    if example_sources is None:
        return (
            "Single-file RTL is allowed for this task. Put the synthesizable top module in "
            "rtl/top.v and list it in manifest.json sources."
        )
    return (
        "Generate a true multi-file RTL implementation. rtl/top.v must be an integration wrapper "
        "that instantiates task-specific submodules. Generate at least two additional Verilog "
        f"source files for this task. Recommended source list: {json.dumps(example_sources)}. "
        "List every RTL source in manifest.json sources and include every listed source in files."
    )


def _manifest_sources_example(task_type: str) -> str:
    return json.dumps(MULTIMODULE_RTL_EXAMPLES.get(task_type, ["rtl/top.v"]))


def _artifact_sources_example(system_his: dict[str, Any], task_type: str) -> list[str]:
    artifacts = system_his.get("artifacts")
    if isinstance(artifacts, dict):
        sources = artifacts.get("rtl_sources")
        if isinstance(sources, list) and all(isinstance(source, str) for source in sources):
            if "rtl/top.v" in sources:
                return sources
    return MULTIMODULE_RTL_EXAMPLES.get(task_type, ["rtl/top.v"])


def _additional_project_file_entries(task_type: str) -> str:
    return _additional_file_entries(MULTIMODULE_RTL_EXAMPLES.get(task_type, ["rtl/top.v"]))


def _additional_file_entries(sources: list[str]) -> str:
    extra_sources = [source for source in sources if source != "rtl/top.v"]
    if not extra_sources:
        return ""
    return "".join(f'    "{source}": "...",\n' for source in extra_sources)


def _repair_rtl_contract(files: dict[str, str], task_type: str | None) -> str:
    if task_type in MULTIMODULE_RTL_EXAMPLES:
        return (
            "Preserve the true multi-file RTL structure. Do not collapse submodules into rtl/top.v. "
            "rtl/top.v must remain an integration wrapper, and manifest.json sources must keep "
            "rtl/top.v plus at least two submodule .v files unless the failure specifically requires "
            "renaming a source."
        )
    try:
        manifest = json.loads(files.get("manifest.json", "{}"))
    except json.JSONDecodeError:
        manifest = {}
    sources = manifest.get("sources")
    rtl_sources = sources if isinstance(sources, list) else []
    if len([path for path in rtl_sources if isinstance(path, str) and path.endswith(".v")]) >= 3:
        return (
            "Preserve the existing multi-file RTL structure. Do not collapse submodules into rtl/top.v. "
            "Return all existing source files unless the repair requires adding or renaming one."
        )
    return "Preserve the existing RTL source structure unless the failure requires changing it."


def _repair_sources_example(files: dict[str, str], task_type: str | None) -> str:
    try:
        manifest = json.loads(files.get("manifest.json", "{}"))
    except json.JSONDecodeError:
        manifest = {}
    sources = manifest.get("sources")
    if isinstance(sources, list) and all(isinstance(path, str) for path in sources):
        return json.dumps(sources)
    if task_type in MULTIMODULE_RTL_EXAMPLES:
        return json.dumps(MULTIMODULE_RTL_EXAMPLES[task_type])
    return json.dumps(["rtl/top.v"])


def _additional_repair_file_entries(files: dict[str, str], task_type: str | None) -> str:
    try:
        sources = json.loads(_repair_sources_example(files, task_type))
    except json.JSONDecodeError:
        sources = ["rtl/top.v"]
    if not isinstance(sources, list) or not all(isinstance(source, str) for source in sources):
        sources = ["rtl/top.v"]
    return _additional_file_entries(sources)


def _repair_system_his_prompt(files: dict[str, str], project_name: str) -> str:
    if _project_system_his_schema(files) == SYSTEM_HIS_V12_SCHEMA:
        return (
            "The system_his.json file content must itself be JSON. Preserve the existing "
            "canonical System-HIS v1.2 contract unless the diagnosis explicitly names system_his.json. "
            "Keep schema_version system-his-v1.2 and do not change top, state, components, instances, "
            "data_flow, control_flow, or artifacts.\n"
            "Current canonical System-HIS v1.2 contract:\n"
            f"{files.get('system_his.json', '{}').strip()}"
        )
    return (
        "The system_his.json file content must itself be JSON and must follow this\n"
        "system-his-v1.1 structure-contract schema:\n"
        f"{_system_his_contract(project_name)}"
    )


def _system_his_contract(project_name: str) -> str:
    return (
        json.dumps(
            {
            "schema_version": "system-his-v1.1",
            "project_name": project_name,
            "project": {"name": project_name, "description": "short requirement summary", "top": "top"},
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [{"name": "rst_n", "polarity": "active_low", "kind": "sync"}],
            "system": {"description": "short black-box behavior summary"},
            "interface": {"top_module": "top", "ports": []},
            "architecture": {"top_module": "top", "topology": {"nodes": [], "edges": []}},
            "modules": [
                {
                    "name": "top",
                    "role": "top",
                    "source": "rtl/top.v",
                    "ports": [],
                    "parameters": {},
                    "params": [],
                    "clock": "clk",
                    "reset": "rst_n",
                    "intent": "integrates submodules and exposes the top interface",
                },
                {
                    "name": "submodule_name",
                    "role": "submodule",
                    "source": "rtl/submodule_name.v",
                    "ports": [],
                    "parameters": {"WIDTH": 8},
                    "params": [{"name": "WIDTH", "value": 8}],
                    "clock": "clk",
                    "reset": "rst_n",
                    "intent": "one-line module intent",
                },
            ],
            "connections": [
                {
                    "from": {"module": "top", "port": "input_or_signal"},
                    "to": {"module": "submodule_name", "port": "input_or_signal"},
                    "signal": "signal_name",
                    "protocol": "register",
                    "width": 1,
                    "cdc": False,
                }
            ],
            "top_ports": [],
            "platform": {"toolchain": "open_source"},
            "verification": {
                "testbench": "sim/tb_top.v",
                "checks": ["l0_contract", "l1_lint", "l2_self_checking_sim", "l3_synthesis"],
                "test_pass_means": "testbench prints TEST_PASS and no TEST_FAIL",
            },
            "qor_intent": {"resources": {"lut": 0, "ff": 0, "bram": 0, "dsp": 0}},
            },
            indent=2,
        )
        + "\n\n"
        + "Important System-HIS rules: role must be exactly top or submodule; use clock, not clock_domain; "
        + "parameters must be an object of RTL-declared parameter names to values; params must be a list "
        + "of {name, value} entries matching parameters exactly; omit undeclared RTL parameters; port widths "
        + "must match the parsed RTL exactly, including expressions like [WIDTH-1:0]; width strings must "
        + "match parsed RTL ranges exactly rather than simplified parameter names; connection protocol "
        + "must be one of register, valid_ready, axi_lite, axi_stream; every connection needs from/to "
        + "endpoint objects, signal, width, and boolean cdc; connection endpoint module values must use "
        + "System-HIS module names, not instance aliases such as sb0, join, acc, or stg; Do not use "
        + "Verilog reserved keywords as any RTL identifier, including instance, signal, register, array, "
        + "block, and parameter names; avoid fork, join, buf, begin, end, module, wire, input, output, and reg."
    )
