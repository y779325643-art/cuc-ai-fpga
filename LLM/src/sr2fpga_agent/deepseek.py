"""DeepSeek provider for SR2FPGA project generation."""

from __future__ import annotations

import difflib
import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, RepairResult
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12


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
}


@dataclass(frozen=True)
class DeepSeekConfig:
    """OpenAI-compatible DeepSeek API configuration."""

    api_key: str
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: int = 120


class DeepSeekClient:
    """Small stdlib HTTP client for DeepSeek chat completions."""

    def __init__(self, config: DeepSeekConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
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
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DeepSeek API request failed with HTTP {exc.code}: {body}") from exc
        except TimeoutError as exc:
            raise RuntimeError("DeepSeek API request timed out") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"DeepSeek API request failed: {exc.reason}") from exc

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("DeepSeek API response did not contain choices[0].message.content") from exc


def _default_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


class DeepSeekProjectGenerator:
    """Generate a project package by asking DeepSeek for required files."""

    def __init__(self, client: DeepSeekClient, max_attempts: int = 3) -> None:
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

    def __init__(self, client: DeepSeekClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> dict[str, Any]:
        messages = _system_his_v12_messages(request, platform)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                return parse_system_his_v12(content)
            except ValueError as exc:
                last_error = exc
                messages = _with_system_his_retry_feedback(messages, str(exc))
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek System-HIS generator did not run")


class DeepSeekHisProjectGenerator:
    """Generate a project package from a checked System-HIS v1.2 contract."""

    def __init__(self, client: DeepSeekClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def generate(
        self,
        request: ProjectRequest,
        platform: PlatformProfile,
        system_his: dict[str, Any],
    ) -> GeneratedProject:
        messages = _his_project_messages(request, platform, system_his)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(content, expected_task_type=request.task_type)
                try:
                    parse_system_his_v12(files["system_his.json"])
                except ValueError as exc:
                    raise ValueError(f"DeepSeek HIS2PROJECT system_his.json failed validation: {exc}") from exc
                return GeneratedProject(project_name=request.project_name, files=files)
            except ValueError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek HIS2PROJECT generator did not run")


class DeepSeekTwoStageProjectGenerator:
    """Generate a project through REQ2HIS followed by HIS2PROJECT."""

    def __init__(
        self,
        client: DeepSeekClient,
        max_attempts: int = 3,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.system_his_generator = DeepSeekSystemHisGenerator(client, max_attempts=max_attempts)
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

    def __init__(self, client: DeepSeekClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def repair(self, project: GeneratedProject, diagnosis: dict[str, object]) -> RepairResult:
        messages = _repair_messages(project, diagnosis)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(content, expected_task_type=_project_task_type(project.files))
                repaired_project = _minimize_repaired_project(
                    project,
                    GeneratedProject(project_name=project.project_name, files=files),
                    diagnosis,
                )
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
Generate a System-HIS v1.2 top-down architecture contract for SR2FPGA.

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

Return only System-HIS JSON with schema_version "system-his-v1.2-topdown".
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
- Record architectural state, not incidental RTL temporaries.
- Separate component definitions from concrete instances.
- Every instance must reference a component.
- Every data_flow endpoint must name top.<port> or <instance>.<port>.
- Separate data movement from control rules.
- control_flow rules should use kinds such as reset_rule, handshake_rule,
  enable_rule, stall_rule, counter_update, fsm_transition, or buffer_occupancy.
- Use width objects with expr and resolved when a parameterized width is useful.
- Keep verification as scenarios and pass_condition, not full testbench code.

{_system_his_v12_task_guidance(request.task_type)}

Return this JSON shape:
{{
  "schema_version": "system-his-v1.2-topdown",
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
  "data_flow": [],
  "control_flow": [],
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
) -> list[dict[str, str]]:
    return [
        *messages,
        {
            "role": "user",
            "content": (
                "Your previous System-HIS output failed validation. "
                "Return a corrected complete System-HIS JSON object only. "
                f"Validation error: {error}"
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
            "- control_flow entries must each include name, kind, condition, effects, related_state, and related_flows.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/skid_buffer.v, rtl/stream_join.v, "
            "rtl/accumulator_core.v, and rtl/stream_stage.v."
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


def _his_project_messages(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, Any],
) -> list[dict[str, str]]:
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    system_his_text = json.dumps(system_his, ensure_ascii=False, indent=2)
    sources = _artifact_sources_example(system_his, request.task_type)
    extra_entries = _additional_file_entries(sources)
    system = (
        "You generate complete FPGA RTL project packages from checked System-HIS architecture contracts. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Generate a complete SR2FPGA Verilog RTL project from this checked System-HIS.

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

Rules:
- Treat the System-HIS as the frozen architecture contract.
- Do not change component, instance, top port, data_flow, or control_flow names.
- Generate RTL that implements the top-down architecture contract.
- Do not use Verilog reserved keywords for any RTL identifier, including modules,
  instances, regs, wires, arrays, blocks, and parameters. Avoid names such as
  fork, join, buf, begin, end, module, wire, input, output, and reg.
- Keep rtl/top.v as the integration wrapper.
- Put reusable components in separate RTL files.
- Include the same System-HIS JSON as system_his.json unless only formatting changes are needed.
- Include a bounded self-checking testbench that prints TEST_PASS on success and TEST_FAIL on failure.

Required files:
{required_files}

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
{extra_entries}
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
  "sources": {json.dumps(sources)},
  "constraints": {{"timing": "constraints/timing.sdc"}},
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


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
    system_his_contract = _system_his_contract(project.project_name)
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

The system_his.json file content must itself be JSON and must follow this
system-his-v1.1 structure-contract schema:
{system_his_contract}

Make the smallest practical fix for the failing tool log. Preserve pure
Verilog RTL and ensure the testbench prints TEST_PASS on success.
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


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
