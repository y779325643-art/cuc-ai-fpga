"""Public projection, source policy and backend qualification boundaries."""
import json
import sys
from types import SimpleNamespace

import pytest

from sr2fpga_agent.execution.isolation import (
    CandidateBoundaryError, DockerBackend, IsolationUnavailable,
    LocalDevelopmentBackend, ToolLimits, public_task_projection,
    validate_candidate_sources,
)


def test_public_projection_excludes_private_fields_and_original_host_paths():
    task = SimpleNamespace(requirements={
        "contract_version": "development-public-context-v2", "analysis_population": "development",
        "requirement_id": "task", "revision_id": "v1", "public_text": "public",
        "boundary": {}, "fact_records": [], "public_assets": [
            {"id": "weights", "path": "assets/public.json", "sha256": "a" * 64, "size_bytes": 2}],
        "private_ref": "PRIVATE_CANARY", "oracle": "PRIVATE_CANARY",
    }, target={"target_id": "public-target"}, capability={"limits": {}}, asset_bytes={"weights": b"{}"},
        sources=SimpleNamespace(path="PRIVATE_CANARY"))
    projection = public_task_projection(task)
    assert "PRIVATE_CANARY" not in json.dumps(projection)
    assert "path" not in projection["public_assets"][0]
    assert projection["public_assets"][0]["content_utf8"] == "{}"
    projection["boundary"]["changed"] = True
    assert task.requirements["boundary"] == {}


def _files(source):
    return {"manifest.json": "{}", "rtl/top.sv": source}


@pytest.mark.parametrize("source", [
    'module T; initial $readmemh("private.bin",memory); endmodule',
    'module T; initial $display("TRACE_END 100"); endmodule',
    'module T; initial $finish; endmodule',
    '`include "private.sv"\nmodule T; endmodule',
    'module T; wire q=trusted_tb.expected[0]; endmodule',
    'module T; bind trusted_tb spy(); endmodule',
    'module T; force q=1; endmodule',
    'module T; wire \\escaped ; endmodule',
])
def test_candidate_cannot_access_files_or_control_its_own_score(source):
    with pytest.raises(CandidateBoundaryError):
        validate_candidate_sources(_files(source))


def test_candidate_policy_allows_ordinary_named_ports_math_and_comments():
    validate_candidate_sources(_files("""// $display and tb.secret in a comment are inert.
module T(input logic a,output logic b);
wire [3:0] q=4'd1;
Child c(.a(a),.b(b));
function integer f(input integer x); begin f=$signed(x);end endfunction
endmodule
module Child(input a,output b);assign b=a;endmodule
"""))


@pytest.mark.parametrize("path", ["oracle/model.py", "sim/tb.sv", "run.sh", "../escape.sv", "rtl/C:escape.sv"])
def test_candidate_files_are_confined_to_declared_model_owned_surface(path):
    files = _files("module T;endmodule")
    files[path] = "secret"
    with pytest.raises(ValueError):
        validate_candidate_sources(files)


def test_candidate_casefold_path_collision_is_rejected():
    files = _files("module T;endmodule")
    files["rtl/Top.sv"] = "module U;endmodule"
    with pytest.raises(CandidateBoundaryError, match="collision"):
        validate_candidate_sources(files)


@pytest.mark.parametrize("damage", [{"memory_bytes": 0}, {"cpu_seconds": True}, {"timeout_seconds": float("inf")}, {"pids_limit": -1}])
def test_tool_limits_require_real_positive_resource_bounds(damage):
    with pytest.raises(ValueError):
        ToolLimits(**damage)


def test_development_backend_drops_secret_environment_without_claiming_os_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("SR2FPGA_PRIVATE_CANARY", "DO_NOT_FORWARD")
    backend = LocalDevelopmentBackend()
    result = backend.run([sys.executable, "-c", "import os;print(os.getenv('SR2FPGA_PRIVATE_CANARY','ABSENT'))"],
                         tmp_path, "environment", ToolLimits(timeout_seconds=5))
    assert result.status == "passed"
    assert result.stdout.strip() == "ABSENT"
    assert backend.isolation_qualified is False
    assert backend.policy()["cpu_memory_enforced"] is False


def test_local_output_ceiling_never_marks_a_truncated_output_as_pass(tmp_path):
    result = LocalDevelopmentBackend().run([sys.executable, "-c", "print('x'*100)"], tmp_path,
                                          "bounded", ToolLimits(timeout_seconds=5, max_output_bytes=16))
    assert result.status == "output_limit_exceeded"
    assert len(result.stdout.encode()) <= 16
    assert (tmp_path / "bounded.stdout.log").stat().st_size > 16


def test_docker_command_has_pinned_image_explicit_confinement_and_one_work_mount(tmp_path):
    image = "example/toolchain@sha256:" + "a" * 64
    backend = DockerBackend(image)
    command = backend.command(["yosys", "-V"], tmp_path, ToolLimits(memory_bytes=123456789), name="probe")
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--pull") + 1] == "never"
    assert "--read-only" in command and "--privileged" not in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--memory") + 1] == "123456789"
    assert command[command.index("--memory-swap") + 1] == "123456789"
    assert command.count("--mount") == 1
    assert str(tmp_path.resolve()) in command[command.index("--mount") + 1]
    assert "no-new-privileges=true" in command
    assert backend.isolation_qualified is False


@pytest.mark.parametrize("image,user", [("example/toolchain:latest", "1000:1000"),
                                       ("example/toolchain@sha256:" + "a" * 64, "0:0")])
def test_docker_rejects_mutable_image_tags_and_root_user(image, user):
    with pytest.raises(ValueError):
        DockerBackend(image, user=user)


def test_unavailable_docker_is_fail_closed_and_never_becomes_qualified(tmp_path, monkeypatch):
    backend = DockerBackend("example/toolchain@sha256:" + "b" * 64)
    monkeypatch.setattr(backend, "available", lambda: False)
    with pytest.raises(IsolationUnavailable):
        backend.qualify(tmp_path / "probe")
    with pytest.raises(IsolationUnavailable):
        backend.run(["yosys", "-V"], tmp_path, "parser", ToolLimits())
    assert backend.isolation_qualified is False


def test_docker_worker_rejects_non_tool_programs_even_after_a_qualification_claim(tmp_path):
    backend = DockerBackend("example/toolchain@sha256:" + "c" * 64)
    backend.isolation_qualified = True
    with pytest.raises(CandidateBoundaryError, match="allowlist"):
        backend.run(["/bin/sh", "-c", "anything"], tmp_path, "parser", ToolLimits())


@pytest.mark.parametrize("endpoint", ["tcp://remote:2375", "ssh://worker", "https://worker"])
def test_docker_worker_never_implicitly_transmits_sources_to_a_remote_daemon(endpoint):
    with pytest.raises(ValueError, match="local Docker"):
        DockerBackend("example/toolchain@sha256:" + "d" * 64, endpoint=endpoint)
