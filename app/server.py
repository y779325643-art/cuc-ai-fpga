"""Local HTTP bridge between the SR2FPGA demo UI and the Agent runtime."""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
import threading
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = Path(__file__).resolve().parent
AGENT_SOURCE_ROOT = REPOSITORY_ROOT / "agent" / "src"
DEFAULT_OUTPUT_ROOT = REPOSITORY_ROOT / "artifacts" / "agent" / "ui-demo"
LOGGER = logging.getLogger(__name__)

if str(AGENT_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_SOURCE_ROOT))

from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.requirement_boundary import (
    evaluate_requirement_boundary,
)
from sr2fpga_agent.rtl_introspect import declared_module_ports
from sr2fpga_agent.task_families import (
    SUPPORTED_TASK_TYPES,
    TASK_FAMILY_IDS,
)

PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
TASK_INFERENCE_PATTERNS = (
    ("uart_fifo_loopback", re.compile(r"\buart\b|串口|回环|loopback", re.IGNORECASE)),
    ("composed_event_counter", re.compile(r"事件|event|门控|gated?", re.IGNORECASE)),
    ("pwm_controller", re.compile(r"\bpwm\b|脉宽|占空比|duty", re.IGNORECASE)),
    ("fifo", re.compile(r"\bfifo\b|队列|缓存|缓冲|先进先出", re.IGNORECASE)),
    ("counter", re.compile(r"计数器|计数|counter", re.IGNORECASE)),
)
ENGINEERING_CONTEXT_REQUIRED_FIELDS = (
    ("top_module", "顶层模块名称"),
    ("clock_mhz", "系统时钟频率"),
    ("reset_polarity", "复位策略"),
    ("interface_spec", "接口协议"),
    ("io_spec", "端口与信号摘要"),
    ("target_platform", "目标平台或约束说明"),
    ("verification_intent", "验证策略"),
)
TASK_LABEL_OVERRIDES = {
    "composed_stream_fork": "数据流分叉（stream fork）",
    "composed_dual_stream_join": "双流汇合（dual-stream join）",
    "composed_rl_accelerator_shell": "集成式 Q-Learning 加速器",
    "composed_batch_rl_accelerator_shell": "双通道批量 Q-Learning 加速器",
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return payload


def _validate_identity_fields(payload: object) -> tuple[dict, str, str]:
    """Apply the project-name and requirement rules shared by both endpoints.

    Both callers check these before task type and width, so keeping the split
    here preserves which message an invalid request reports first.
    """

    if not isinstance(payload, dict):
        raise TypeError("请求正文必须是 JSON 对象")

    project_name = str(payload.get("project_name", "")).strip()
    if not PROJECT_NAME_PATTERN.fullmatch(project_name):
        raise ValueError("项目名称需以字母开头，且只包含字母、数字、下划线或连字符")

    requirement = str(payload.get("requirement", "")).strip()
    if not requirement:
        raise ValueError("系统级需求不能为空")
    if len(requirement) > 12_000:
        raise ValueError("系统级需求不能超过 12000 个字符")

    return payload, project_name, requirement


def _validate_width(payload: dict) -> int:
    width = payload.get("width", 8)
    if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= 64:
        raise ValueError("数据位宽必须是 1 到 64 之间的整数")
    return width


def _validate_request(payload: object) -> tuple[str, str, int, str]:
    payload, project_name, requirement = _validate_identity_fields(payload)

    task_type = _resolve_task_type(payload, requirement=requirement)
    if task_type not in SUPPORTED_TASK_TYPES:
        raise ValueError(f"当前确定性后端不支持任务类型：{task_type or '(empty)'}")

    width = _validate_width(payload)

    missing_context = _missing_engineering_context(payload)
    if missing_context:
        raise ValueError(f"工程上下文不完整，请补充：{', '.join(missing_context)}")

    return project_name, task_type, width, requirement


def _validate_audit_request(payload: object) -> tuple[str, str, int, str]:
    payload, project_name, requirement = _validate_identity_fields(payload)

    # Reading the mode raises nothing, so it stays outside the shared rules.
    mode = str(payload.get("generation_mode", "template")).strip()

    task_type = (
        "freeform"
        if mode == "free"
        else _resolve_task_type(payload, requirement=requirement, allow_unclassified=True)
    )
    if mode != "free" and task_type not in SUPPORTED_TASK_TYPES and task_type != "unclassified":
        raise ValueError(f"当前确定性后端不支持任务类型：{task_type or '(empty)'}")

    width = _validate_width(payload)

    return project_name, task_type, width, requirement


def infer_demo_task_type(requirement: str) -> str | None:
    """Infer one supported registered task family from requirement text."""

    for task_type, pattern in TASK_INFERENCE_PATTERNS:
        if pattern.search(requirement):
            return task_type
    normalized = _normalize_for_task_match(requirement)
    for task_type in sorted(SUPPORTED_TASK_TYPES, key=len, reverse=True):
        if _task_type_matches_requirement(task_type, normalized):
            return task_type
    return None


def _normalize_for_task_match(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _task_type_matches_requirement(task_type: str, normalized_requirement: str) -> bool:
    candidates = {task_type, task_type.replace("_", " ")}
    family_id = TASK_FAMILY_IDS.get(task_type)
    if family_id is not None:
        candidates.add(family_id)
        candidates.add(family_id.replace("_", " "))
    return any(_normalize_for_task_match(candidate) in normalized_requirement for candidate in candidates)


def task_registry_payload() -> dict[str, Any]:
    display_names = _catalog_display_names()
    tasks = [
        {
            "id": task_type,
            "label": _task_label(task_type, display_names),
            "family_id": TASK_FAMILY_IDS[task_type],
            "width": 8,
            "engineering_context": _template_context(task_type, 8),
        }
        for task_type in sorted(TASK_FAMILY_IDS)
    ]
    return {
        "tasks": tasks,
        "task_count": len(tasks),
        "family_count": len({task["family_id"] for task in tasks}),
        "source": "sr2fpga_agent.task_families+task-catalog-v0.2",
    }


def _catalog_display_names() -> dict[str, str]:
    catalog = _read_json(REPOSITORY_ROOT / "contracts" / "task-catalog" / "sr2fpga-task-catalog-v0.2.json")
    return {
        family["family_id"]: family["display_name"]
        for family in catalog.get("task_families", [])
        if isinstance(family, dict)
        and isinstance(family.get("family_id"), str)
        and isinstance(family.get("display_name"), str)
    }


def _task_label(task_type: str, display_names: dict[str, str]) -> str:
    if task_type in TASK_LABEL_OVERRIDES:
        return TASK_LABEL_OVERRIDES[task_type]
    return display_names.get(TASK_FAMILY_IDS[task_type], task_type.replace("_", " "))


def _missing_engineering_context(payload: dict[str, Any]) -> list[str]:
    """Return missing UI engineering facts when the UI sends structured context."""

    if "engineering_context" not in payload:
        return []
    context = payload.get("engineering_context")
    if not isinstance(context, dict):
        return ["工程上下文"]

    missing: list[str] = []
    for field, label in ENGINEERING_CONTEXT_REQUIRED_FIELDS:
        value = context.get(field)
        if value is None or str(value).strip() == "":
            missing.append(label)

    clock = context.get("clock_mhz")
    if clock is not None and str(clock).strip():
        try:
            clock_value = float(str(clock))
        except ValueError:
            if "系统时钟频率" not in missing:
                missing.append("系统时钟频率")
        else:
            if (not math.isfinite(clock_value * 1_000_000) or clock_value < 0.000001) and "系统时钟频率" not in missing:
                missing.append("系统时钟频率")

    deliverables = context.get("deliverables")
    if not isinstance(deliverables, list) or not deliverables or not all(isinstance(item, str) for item in deliverables):
        missing.append("交付范围")
    return missing


def _template_context(task_type: str, width: int) -> dict[str, Any]:
    project = ProjectGenerator().generate(
        ProjectRequest(task_type, width, "template_preview"),
        PlatformProfile("generic_verilog", "generic", "open_source"),
    )
    manifest = json.loads(project.files["manifest.json"])
    ports = declared_module_ports(project.files, manifest["sources"])["top"]
    if {"wr_en", "rd_en"} <= ports.keys():
        interface = "wr_rd_enable"
    elif task_type.startswith("uart"):
        interface = "uart_stream"
    elif any(name.endswith("valid") for name in ports) and any(name.endswith("ready") for name in ports):
        interface = "valid_ready"
    else:
        interface = "simple_gpio"
    port_labels = []
    for name, port in ports.items():
        bits = port["width"]
        suffix = "" if bits == 1 else f"[{bits - 1}:0]" if isinstance(bits, int) else str(bits)
        port_labels.append(name + suffix)
    return {
        "top_module": "top", "clock_mhz": "100", "reset_polarity": "active_low",
        "interface_spec": interface,
        "io_spec": ", ".join(port_labels),
        "target_platform": "generic Verilog", "verification_intent": "self_checking_tb",
        "deliverables": ["RTL", "Testbench", "Constraints", "README"],
    }


def _demo_inputs(
    payload: dict[str, Any], task_type: str, width: int, project_name: str, requirement: str,
) -> tuple[ProjectRequest, PlatformProfile]:
    context = payload.get("engineering_context", {})
    clock_hz = round(float(context.get("clock_mhz", 100)) * 1_000_000)
    platform = PlatformProfile(
        str(context.get("target_platform", "generic_verilog")) if task_type == "freeform" else "generic_verilog",
        "generic", "open_source", clock_hz=clock_hz,
        reset_polarity=str(context.get("reset_polarity", "active_low")),
    )
    request = ProjectRequest(task_type, width, project_name, requirement)
    return request, platform


def _context_gaps(payload: dict[str, Any], task_type: str, width: int) -> list[str]:
    context = payload.get("engineering_context")
    if not isinstance(context, dict) or task_type not in SUPPORTED_TASK_TYPES:
        return []
    supported = _template_context(task_type, width)
    gaps = []
    for key in ("top_module", "reset_polarity", "interface_spec", "target_platform", "verification_intent", "deliverables", "io_spec"):
        value = context.get(key)
        expected = supported[key]
        if key == "io_spec":
            value = {re.sub(r"\s+", "", port) for port in str(value).split(",")}
            expected = {re.sub(r"\s+", "", port) for port in expected.split(",")}
        elif key == "deliverables":
            value, expected = sorted(value), sorted(expected)
        if value != expected:
            gaps.append(key)
    return gaps


class _DemoProjectGenerator(ProjectGenerator):
    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        project = super().generate(request, platform)
        context = _template_context(request.task_type, request.width)
        context["clock_mhz"] = platform.clock_hz / 1_000_000
        readme = f"# {request.project_name}\n\nDeterministic reference project.\n\n" + json.dumps(context, ensure_ascii=False, indent=2) + "\n"
        return GeneratedProject(project.project_name, {**project.files, "README.md": readme})


def _engineering_context_clarification(
    *,
    project_name: str,
    task_type: str,
    missing_context: list[str],
) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "task_type": task_type,
        "inferred_task_type": None if task_type in {"freeform", "unclassified"} else task_type,
        "disposition": "needs_clarification",
        "reason_codes": [f"critical_fact_missing:{item}" for item in missing_context],
        "clarification_questions": [f"请补充工程生成所需的{item}。" for item in missing_context],
        "clarification_fact_ids": missing_context,
        "capability_gap_ids": [],
        "boundary": {
            "disposition": "needs_clarification",
            "reason_codes": [f"critical_fact_missing:{item}" for item in missing_context],
        },
    }


def _resolve_task_type(
    payload: dict[str, Any],
    *,
    requirement: str,
    allow_unclassified: bool = False,
) -> str:
    task_type = str(payload.get("task_type", "")).strip()
    if task_type in SUPPORTED_TASK_TYPES and task_type != "auto":
        return task_type
    inferred = infer_demo_task_type(requirement)
    if inferred is None:
        if allow_unclassified:
            return "unclassified"
        raise ValueError("无法从需求自动识别当前后端注册的任务族，请补充目标功能或使用自由需求模式")
    return inferred


def _file_role(path: str) -> str:
    if path.startswith("rtl/"):
        return "rtl"
    if path.startswith("sim/"):
        return "verification"
    if path.startswith("constraints/"):
        return "constraints"
    if path.endswith(".md"):
        return "documentation"
    if path == "system_his.json":
        return "system_his"
    return "project"


def _project_files(project_dir: Path) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    if not project_dir.is_dir():
        return files
    for path in sorted(item for item in project_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(project_dir).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files.append({"path": relative, "role": _file_role(relative), "content": content})
    return files


def _stage_statuses(labels: dict[str, Any]) -> dict[str, dict[str, str | None]]:
    checks = labels.get("checks") if isinstance(labels.get("checks"), dict) else {}
    stopped_before_project = labels.get("pass_level") == "GEN_FAIL"
    pre_project_reason = str(labels.get("failure_type") or "generation_failed")
    return {
        "H0": {"status": str(labels.get("h0_status", "not_applicable")), "reason": None},
        "H1": {"status": str(labels.get("h1_status", "not_applicable")), "reason": None},
        "H2": {"status": str(labels.get("h2_status", "not_applicable")), "reason": None},
        "H3": {"status": str(labels.get("h3_status", "not_applicable")), "reason": None},
        "L0": {
            "status": (
                "not_run"
                if stopped_before_project
                else ("pass" if checks.get("l0_complete") else "fail")
            ),
            "reason": pre_project_reason if stopped_before_project else None,
        },
        "L1": {
            "status": (
                "not_run"
                if stopped_before_project
                else (
                    "pass"
                    if checks.get("l1_lint_pass")
                    else str(checks.get("l1_lint_status", labels.get("l1_lint_status", "not_run")))
                )
            ),
            "reason": (
                pre_project_reason
                if stopped_before_project
                else checks.get("l1_lint_skip_reason") or labels.get("l1_lint_skip_reason")
            ),
        },
        "L2": {
            "status": (
                "not_run"
                if stopped_before_project
                else (
                    "pass"
                    if checks.get("l2_sim_pass")
                    else str(checks.get("l2_sim_status", "not_run"))
                )
            ),
            "reason": (
                pre_project_reason
                if stopped_before_project
                else checks.get("l2_sim_skip_reason") or labels.get("l2_sim_skip_reason")
            ),
        },
        "L3": {
            "status": (
                "not_run"
                if stopped_before_project
                else (
                    "pass"
                    if checks.get("l3_synth_pass")
                    else str(checks.get("l3_synth_status", labels.get("l3_synth_status", "not_run")))
                )
            ),
            "reason": (
                pre_project_reason
                if stopped_before_project
                else checks.get("l3_synth_skip_reason") or labels.get("l3_synth_skip_reason")
            ),
        },
        "L4": {
            "status": (
                "pass"
                if checks.get("l4_open_pass")
                else str(labels.get("l4_open_status", "not_run"))
            ),
            "reason": labels.get("l4_open_skip_reason"),
        },
    }


def generate_demo(payload: object, *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    """Run one deterministic sample through the real Agent and return UI-safe data."""

    project_name, task_type, width, requirement = _validate_request(payload)
    audit = audit_requirement(payload)
    if audit["disposition"] != "ready":
        reason = audit["disposition"]
        return {
            "sample_id": None, "artifact_path": "", "project_name": project_name,
            "task_type": task_type, "method_condition": "reference_deterministic",
            "pass_level": "GEN_FAIL", "failure_type": reason, "boundary": audit["boundary"],
            "stages": _stage_statuses({"pass_level": "GEN_FAIL", "failure_type": reason}),
            "counts": {}, "files": [], "questions": audit["clarification_questions"],
            "capability_gaps": audit["capability_gap_ids"],
        }
    sample_id = f"ui-{uuid.uuid4().hex[:12]}"
    request, platform = _demo_inputs(payload, task_type, width, project_name, requirement)
    boundary = evaluate_requirement_boundary(request, platform)
    metadata = {
        "analysis_population": "development",
        "method_condition": "reference_deterministic",
        "requirement_boundary": boundary.to_dict(),
        "model_call_budget": {"ceiling": 0, "used": 0, "remaining": 0, "calls": []},
        "ui_demo": True,
        "engineering_context": payload.get("engineering_context"),
    }
    result = DataGenerationAgent(output_root, project_generator=_DemoProjectGenerator()).run_one(
        sample_id=sample_id,
        requirement=requirement,
        request=request,
        platform=platform,
        metadata=metadata,
    )

    sample_dir = output_root / sample_id
    labels = _read_json(sample_dir / "eval" / "labels.json")
    files = _project_files(sample_dir / "final" / "generated_project")
    role_counts: dict[str, int] = {}
    for item in files:
        role_counts[item["role"]] = role_counts.get(item["role"], 0) + 1

    response: dict[str, Any] = {
        "sample_id": sample_id,
        "artifact_path": sample_dir.relative_to(REPOSITORY_ROOT if sample_dir.is_relative_to(REPOSITORY_ROOT) else output_root).as_posix(),
        "project_name": project_name,
        "task_type": task_type,
        "method_condition": "reference_deterministic",
        "pass_level": result["pass_level"],
        "boundary": boundary.to_dict(),
        "stages": _stage_statuses(labels),
        "counts": role_counts,
        "files": files,
    }
    for key in ("failure_type", "failed_h_stage", "questions", "capability_gaps"):
        if key in result:
            response[key] = result[key]
    return response


def audit_requirement(payload: object) -> dict[str, Any]:
    """Classify requirement readiness without generating project files."""

    project_name, task_type, width, requirement = _validate_audit_request(payload)
    if isinstance(payload, dict):
        missing_context = _missing_engineering_context(payload)
        if "engineering_context" in payload and task_type == "unclassified" and "目标任务族" not in missing_context:
            missing_context.insert(0, "目标任务族")
        if missing_context:
            return _engineering_context_clarification(
                project_name=project_name,
                task_type=task_type,
                missing_context=missing_context,
            )
    if task_type == "unclassified":
        return {
            "project_name": project_name,
            "task_type": task_type,
            "inferred_task_type": None,
            "disposition": "needs_clarification",
            "reason_codes": ["critical_fact_missing:task_family"],
            "clarification_questions": [
                "请说明目标工程属于哪类功能，例如 FIFO、计数器、事件门控计数器、PWM 控制器或 UART 回环。"
            ],
            "clarification_fact_ids": ["task_family"],
            "capability_gap_ids": [],
            "boundary": {
                "disposition": "needs_clarification",
                "reason_codes": ["critical_fact_missing:task_family"],
            },
        }
    gaps = _context_gaps(payload, task_type, width)
    if gaps:
        reasons = [f"unsupported_engineering_context:{key}" for key in gaps]
        supported = _template_context(task_type, width)
        labels = {**dict(ENGINEERING_CONTEXT_REQUIRED_FIELDS), "deliverables": "交付范围"}
        return {
            "project_name": project_name, "task_type": task_type, "inferred_task_type": task_type,
            "disposition": "capability_gap", "reason_codes": reasons,
            "clarification_questions": [], "clarification_fact_ids": [], "capability_gap_ids": gaps,
            "supported_engineering_context": supported,
            "capability_gap_messages": [f"{labels[key]}与当前模板不一致；可使用“填入示例”恢复支持的设置。" for key in gaps],
            "boundary": {"disposition": "capability_gap", "reason_codes": reasons, "capability_gap_ids": gaps},
        }
    request, platform = _demo_inputs(payload, task_type, width, project_name, requirement)
    boundary = evaluate_requirement_boundary(request, platform).to_dict()
    if "engineering_context" in payload:
        explicit = boundary["envelope"]["explicit_facts"]
        conflicts = []
        if explicit.get("data_width_bits", width) != width:
            conflicts.append("数据位宽")
        if explicit.get("clock_frequencies_hz", [platform.clock_hz]) != [platform.clock_hz]:
            conflicts.append("系统时钟频率")
        if explicit.get("reset_polarity", platform.reset_polarity) != platform.reset_polarity:
            conflicts.append("复位策略")
        if conflicts:
            response = _engineering_context_clarification(project_name=project_name, task_type=task_type, missing_context=conflicts)
            response["clarification_questions"] = [f"需求文字与工程上下文中的{field}冲突，请统一后重试。" for field in conflicts]
            return response
    return {
        "project_name": project_name,
        "task_type": task_type,
        "inferred_task_type": None if task_type == "freeform" else task_type,
        "disposition": boundary["disposition"],
        "reason_codes": boundary["reason_codes"],
        "clarification_questions": boundary["clarification_questions"],
        "clarification_fact_ids": boundary["clarification_fact_ids"],
        "capability_gap_ids": boundary["capability_gap_ids"],
        "boundary": boundary,
    }


class DemoRequestHandler(SimpleHTTPRequestHandler):
    """Serve the static UI and its small local JSON API."""

    output_root = DEFAULT_OUTPUT_ROOT
    generation_lock = threading.Lock()
    public_files: ClassVar[dict[str, str]] = {
        "/": "/index.html",
        "/index.html": "/index.html",
        "/app.js": "/app.js",
        "/styles.css": "/styles.css",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(APP_ROOT), **kwargs)

    def do_GET(self) -> None:
        request_path = urlsplit(self.path).path
        if request_path == "/api/health":
            self._send_json(
                {
                    "status": "ok",
                    "mode": "deterministic",
                    "task_count": len(TASK_FAMILY_IDS),
                    "family_count": len(set(TASK_FAMILY_IDS.values())),
                }
            )
            return
        if request_path == "/api/tasks":
            self._send_json(task_registry_payload())
            return
        public_path = self.public_files.get(request_path)
        if public_path is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.path = public_path
        super().do_GET()

    def do_HEAD(self) -> None:
        request_path = urlsplit(self.path).path
        public_path = self.public_files.get(request_path)
        if public_path is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.path = public_path
        super().do_HEAD()

    def do_POST(self) -> None:
        if self.path not in {"/api/generate", "/api/audit-requirement"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 128_000:
                raise ValueError("请求正文为空或过大")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if not isinstance(payload, dict):
                self._send_json({"error": "请求正文必须是 JSON 对象"}, status=HTTPStatus.BAD_REQUEST)
                return
            if self.path == "/api/audit-requirement":
                response = audit_requirement(payload)
            else:
                with self.generation_lock:
                    response = generate_demo(payload, output_root=self.output_root)
            self._send_json(response)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception:  # keep the local demo process alive
            LOGGER.exception("generation failed")
            self._send_json({"error": "执行失败，请检查服务端日志"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _send_json(self, payload: object, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the local SR2FPGA UI demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), DemoRequestHandler)
    print(f"SR2FPGA UI demo: http://{args.host}:{args.port}")
    print(f"Artifacts: {DEFAULT_OUTPUT_ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
