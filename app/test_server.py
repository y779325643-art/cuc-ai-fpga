from __future__ import annotations

import sys
import threading
import json
import re
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest


APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from server import DemoRequestHandler, _stage_statuses, _validate_audit_request, _validate_request, audit_requirement, infer_demo_task_type, task_registry_payload


@pytest.fixture
def demo_server() -> tuple[str, int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(server_address: tuple[str, int], method: str, path: str) -> tuple[int, bytes]:
    connection = HTTPConnection(*server_address, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def _post_json(server_address: tuple[str, int], path: str, payload: object) -> tuple[int, bytes]:
    connection = HTTPConnection(*server_address, timeout=5)
    try:
        body = json.dumps(payload).encode("utf-8")
        connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


@pytest.mark.parametrize("path", ("/", "/index.html", "/app.js", "/styles.css"))
@pytest.mark.parametrize("method", ("GET", "HEAD"))
def test_static_server_only_serves_public_ui_files(
    demo_server: tuple[str, int], method: str, path: str
) -> None:
    status, _ = _request(demo_server, method, path)
    assert status == 200


@pytest.mark.parametrize(
    "path",
    ("/server.py", "/test_server.py", "/README.md", "/__pycache__/", "/../.env"),
)
@pytest.mark.parametrize("method", ("GET", "HEAD"))
def test_static_server_blocks_non_public_files(
    demo_server: tuple[str, int], method: str, path: str
) -> None:
    status, _ = _request(demo_server, method, path)
    assert status == 404


def test_internal_error_does_not_expose_exception_details(
    demo_server: tuple[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_generation(*args: object, **kwargs: object) -> None:
        raise RuntimeError("C:/private/secret-token.txt")

    monkeypatch.setattr("server.generate_demo", fail_generation)
    status, body = _post_json(demo_server, "/api/generate", {"project_name": "demo"})

    assert status == 500
    assert "secret-token" not in body.decode("utf-8")
    assert json.loads(body) == {"error": "执行失败，请检查服务端日志"}


def test_validate_request_accepts_supported_demo_input() -> None:
    assert _validate_request(
        {
            "project_name": "sync_fifo_demo",
            "task_type": "fifo",
            "width": 8,
            "requirement": "Generate an 8-bit synchronous FIFO.",
        }
    ) == (
        "sync_fifo_demo",
        "fifo",
        8,
        "Generate an 8-bit synchronous FIFO.",
    )


def test_validate_request_infers_task_type_from_requirement() -> None:
    assert _validate_request(
        {
            "project_name": "sync_fifo_demo",
            "task_type": "auto",
            "width": 8,
            "requirement": "Generate an 8-bit synchronous FIFO.",
        }
    ) == (
        "sync_fifo_demo",
        "fifo",
        8,
        "Generate an 8-bit synchronous FIFO.",
    )


def test_infer_demo_task_type_returns_none_for_unknown_requirement() -> None:
    assert infer_demo_task_type("Generate a custom accelerator.") is None


def test_infer_demo_task_type_uses_registry_task_names() -> None:
    assert infer_demo_task_type("Generate an SPI master controller.") == "spi_master"


def test_task_registry_payload_comes_from_backend_supported_tasks() -> None:
    payload = task_registry_payload()
    task_ids = {task["id"] for task in payload["tasks"]}

    assert payload["source"] == "sr2fpga_agent.task_families+task-catalog-v0.2"
    assert payload["task_count"] == len(task_ids)
    assert payload["family_count"] == len({task["family_id"] for task in payload["tasks"]})
    assert {"fifo", "spi_master", "matrix_vector_mac"}.issubset(task_ids)


def test_task_registry_uses_public_labels_without_internal_t_numbers() -> None:
    payload = task_registry_payload()
    labels = {task["id"]: task["label"] for task in payload["tasks"]}

    assert labels["composed_event_counter"] == "Event counter topology"
    assert labels["composed_stream_fork"] == "数据流分叉（stream fork）"
    assert labels["composed_dual_stream_join"] == "双流汇合（dual-stream join）"
    assert labels["composed_batch_rl_accelerator_shell"] == "双通道批量 Q-Learning 加速器"
    assert all("composed_" not in label for label in labels.values())
    assert all(re.search(r"\bt(?:[1-9]|1[0-2])(?:_|\b)", label, re.I) is None for label in labels.values())


def test_audit_requirement_asks_for_task_family_when_auto_inference_fails() -> None:
    result = audit_requirement(
        {
            "project_name": "custom_demo",
            "task_type": "auto",
            "width": 8,
            "requirement": "Generate a custom accelerator.",
        }
    )

    assert result["disposition"] == "needs_clarification"
    assert result["clarification_fact_ids"] == ["task_family"]
    assert result["inferred_task_type"] is None


def test_audit_requirement_returns_boundary_payload() -> None:
    result = audit_requirement(
        {
            "project_name": "sync_fifo_demo",
            "task_type": "fifo",
            "width": 8,
            "requirement": "Generate an 8-bit synchronous FIFO with reset and testbench.",
        }
    )

    assert result["project_name"] == "sync_fifo_demo"
    assert result["task_type"] == "fifo"
    assert result["inferred_task_type"] == "fifo"
    assert result["disposition"] in {"ready", "needs_clarification", "capability_gap"}
    assert "clarification_questions" in result
    assert "boundary" in result


def test_audit_requirement_requires_ui_engineering_context_clock() -> None:
    result = audit_requirement(
        {
            "project_name": "sync_fifo_demo",
            "task_type": "auto",
            "width": 8,
            "requirement": "Generate a FIFO.",
            "engineering_context": {
                "top_module": "sync_fifo_top",
                "clock_mhz": "",
                "reset_polarity": "active_low",
                "interface_spec": "wr_rd_enable",
                "io_spec": "clk, rst_n, wr_en, rd_en, din[7:0], dout[7:0], full, empty",
                "target_platform": "generic Verilog",
                "verification_intent": "self_checking_tb",
                "deliverables": ["RTL", "Testbench", "Constraints", "README"],
            },
        }
    )

    assert result["task_type"] == "fifo"
    assert result["disposition"] == "needs_clarification"
    assert "系统时钟频率" in result["clarification_fact_ids"]


def test_audit_request_accepts_free_mode_without_supported_task_family() -> None:
    assert _validate_audit_request(
        {
            "generation_mode": "free",
            "project_name": "custom_project",
            "task_type": "freeform",
            "width": 16,
            "requirement": "Generate a custom FPGA data path with reset and testbench.",
        }
    ) == (
        "custom_project",
        "freeform",
        16,
        "Generate a custom FPGA data path with reset and testbench.",
    )


def test_audit_requirement_endpoint_returns_json(demo_server: tuple[str, int]) -> None:
    status, body = _post_json(
        demo_server,
        "/api/audit-requirement",
        {
            "project_name": "sync_fifo_demo",
            "task_type": "fifo",
            "width": 8,
            "requirement": "Generate an 8-bit synchronous FIFO with reset and testbench.",
        },
    )

    assert status == 200
    assert json.loads(body)["task_type"] == "fifo"


def test_tasks_endpoint_returns_registry_tasks(demo_server: tuple[str, int]) -> None:
    status, body = _request(demo_server, "GET", "/api/tasks")
    payload = json.loads(body)
    task_ids = {task["id"] for task in payload["tasks"]}

    assert status == 200
    assert payload["source"] == "sr2fpga_agent.task_families+task-catalog-v0.2"
    assert "spi_master" in task_ids


@pytest.mark.parametrize(
    ("field", "value"),
    (("project_name", "../escape"), ("width", 0)),
)
def test_validate_request_rejects_invalid_input(field: str, value: object) -> None:
    payload = {
        "project_name": "sync_fifo_demo",
        "task_type": "fifo",
        "width": 8,
        "requirement": "Generate a FIFO.",
    }
    payload[field] = value
    with pytest.raises(ValueError):
        _validate_request(payload)


def test_stage_statuses_preserve_not_run_reason() -> None:
    stages = _stage_statuses(
        {
            "h0_status": "pass",
            "h1_status": "pass",
            "h2_status": "pass",
            "h3_status": "pass",
            "l2_sim_status": "not_run",
            "l2_sim_skip_reason": "needs_oracle",
            "l4_open_status": "not_run",
            "l4_open_skip_reason": "disabled_by_config",
            "checks": {"l0_complete": True, "l1_lint_pass": True, "l3_synth_pass": True},
        }
    )

    assert stages["H0"]["status"] == "pass"
    assert stages["L2"] == {"status": "not_run", "reason": "needs_oracle"}
    assert stages["L4"] == {"status": "not_run", "reason": "disabled_by_config"}


def test_stage_statuses_do_not_turn_capability_gap_into_l0_failure() -> None:
    stages = _stage_statuses(
        {
            "pass_level": "GEN_FAIL",
            "failure_type": "capability_gap",
            "checks": {"generation_complete": False, "l0_complete": False},
        }
    )

    assert stages["L0"] == {"status": "not_run", "reason": "capability_gap"}
    assert stages["L3"] == {"status": "not_run", "reason": "capability_gap"}
