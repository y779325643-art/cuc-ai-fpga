import json

import pytest

from sr2fpga_agent import agent as agent_module
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
    ToolResult,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.system_his_checker import (
    L0CheckResult,
    check_common_project_l0,
    check_his_project_consistency,
    check_project_l0,
)


def _minimal_project(*, top_module: str = "design_top") -> GeneratedProject:
    return GeneratedProject(
        project_name="role_based_project",
        files={
            "manifest.json": json.dumps(
                {
                    "top_module": top_module,
                    "sources": ["src/design.v"],
                }
            )
            + "\n",
            "src/design.v": "module design_top(input wire clk); endmodule\n",
        },
    )


def test_common_project_l0_accepts_role_based_minimal_project() -> None:
    project = _minimal_project()

    result = check_common_project_l0(project)

    assert result.passed, result.errors
    assert "system_his.json" not in project.files
    assert "sim/tb_top.v" not in project.files
    assert "constraints/timing.sdc" not in project.files
    assert "reports/predicted_qor.json" not in project.files
    assert "rtl/top.v" not in project.files


def test_common_project_l0_accepts_canonical_object_source_records() -> None:
    project = GeneratedProject(
        project_name="canonical_project",
        files={
            "manifest.json": json.dumps(
                {
                    "contract_version": "project-package-v1",
                    "project_name": "canonical_project",
                    "top": {
                        "module": "design_top",
                        "source": "src/design.v",
                        "interface": {
                            "ports": [
                                {"name": "clk", "direction": "input", "width": 1}
                            ]
                        },
                    },
                    "sources": [
                        {
                            "path": "src/design.v",
                            "role": "rtl_source",
                            "language": "verilog",
                        }
                    ],
                    "artifacts": [],
                    "build": {
                        "toolchain_id": "open_source",
                        "language_standard": "verilog-2005",
                    },
                }
            )
            + "\n",
            "src/design.v": "module design_top(input wire clk); endmodule\n",
        },
    )

    result = check_common_project_l0(project)

    assert result.passed, result.errors


def test_common_project_l0_rejects_missing_manifest_source() -> None:
    project = _minimal_project()
    project = GeneratedProject(
        project_name=project.project_name,
        files={"manifest.json": project.files["manifest.json"]},
    )

    result = check_common_project_l0(project)

    assert not result.passed
    assert any("missing source files: src/design.v" in error for error in result.errors)


def test_common_project_l0_rejects_undeclared_manifest_top() -> None:
    result = check_common_project_l0(_minimal_project(top_module="missing_top"))

    assert not result.passed
    assert "top module 'missing_top' is not declared in manifest sources" in result.errors


def test_his_project_consistency_is_a_separate_applicable_check() -> None:
    project = _minimal_project()

    common = check_common_project_l0(project)
    consistency = check_his_project_consistency(project)

    assert common.passed
    assert not consistency.passed
    assert "system_his.json is required" in consistency.errors


def test_legacy_project_l0_entrypoint_retains_his_cross_check() -> None:
    result = check_project_l0(_minimal_project())

    assert not result.passed
    assert "system_his.json is required" in result.errors


@pytest.mark.parametrize("schema_version", ["system-his-v1.1", "system-his-v1.2"])
def test_his_consistency_accepts_canonical_manifest_projection(schema_version: str) -> None:
    request = ProjectRequest(task_type="counter", width=8, project_name="canonical_his")
    platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
    legacy_project = ProjectGenerator().generate(request, platform)
    files = dict(legacy_project.files)
    system_his = json.loads(files["system_his.json"])
    system_his["schema_version"] = schema_version
    files["system_his.json"] = json.dumps(system_his) + "\n"
    legacy_manifest = json.loads(files["manifest.json"])
    files["manifest.json"] = json.dumps(
        {
            "contract_version": "project-package-v1",
            "project_name": request.project_name,
            "top": {
                "module": legacy_manifest["top_module"],
                "source": legacy_manifest["sources"][0],
                "interface": {"ports": system_his["top_ports"]},
            },
            "sources": [
                {"path": path, "role": "rtl_source", "language": "verilog"}
                for path in legacy_manifest["sources"]
            ],
            "artifacts": [
                {
                    "path": "system_his.json",
                    "role": "system_his",
                    "applicability": "required",
                },
                {
                    "path": legacy_manifest["simulation"]["testbench"],
                    "role": "candidate_testbench",
                    "applicability": "required",
                },
                {
                    "path": legacy_manifest["constraints"]["timing"],
                    "role": "constraint",
                    "applicability": "required",
                },
                {
                    "path": legacy_manifest["reports"]["predicted_qor"],
                    "role": "predicted_qor",
                    "applicability": "advisory",
                },
            ],
            "build": {
                "toolchain_id": "open_source",
                "language_standard": "verilog-2005",
            },
        }
    ) + "\n"
    project = GeneratedProject(project_name=request.project_name, files=files)

    consistency = check_his_project_consistency(project)
    combined = check_project_l0(project)

    assert consistency.passed, consistency.errors
    assert combined.passed, combined.errors


def test_agent_runs_common_before_applicable_his_consistency(monkeypatch, tmp_path) -> None:
    request = ProjectRequest(task_type="counter", width=8, project_name="layered_l0")
    platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
    project = ProjectGenerator().generate(request, platform)
    calls: list[str] = []

    class Generator:
        def generate(self, request, platform):
            return project

    def common(candidate):
        calls.append("common_project_l0")
        return L0CheckResult(passed=True)

    def consistency(candidate):
        calls.append("his_project_consistency")
        return L0CheckResult(passed=False, errors=["forced HIS mismatch"])

    monkeypatch.setattr(agent_module, "check_common_project_l0", common)
    monkeypatch.setattr(agent_module, "check_his_project_consistency", consistency)
    agent = DataGenerationAgent(tmp_path / "dataset", project_generator=Generator())

    result = agent.run_one(
        "layered_his",
        "Design a counter.",
        request,
        platform,
        metadata={"method_condition": "M4"},
    )

    recorded = json.loads(
        (
            tmp_path
            / "dataset/layered_his/attempts/attempt_000/eval/l0_consistency.json"
        ).read_text(encoding="utf-8")
    )
    assert calls == ["common_project_l0", "his_project_consistency"]
    assert result["pass_level"] == "L0_FAIL"
    assert recorded["command"] == ["his_project_consistency"]


def test_agent_does_not_run_his_consistency_for_direct_method(monkeypatch, tmp_path) -> None:
    request = ProjectRequest(task_type="counter", width=8, project_name="direct_l0")
    platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
    calls: list[str] = []

    class Generator:
        def generate(self, request, platform):
            return _minimal_project()

    def common(candidate):
        calls.append("common_project_l0")
        return check_common_project_l0(candidate)

    def unexpected_consistency(candidate):
        raise AssertionError("Direct methods must not run HIS consistency")

    def stop_after_l0(self, project, project_dir, platform, **kwargs):
        return {
            "lint": ToolResult(
                stage="lint",
                command=["verilator"],
                status="passed",
                exit_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.0,
            )
        }

    monkeypatch.setattr(agent_module, "check_common_project_l0", common)
    monkeypatch.setattr(agent_module, "check_his_project_consistency", unexpected_consistency)
    monkeypatch.setattr(DataGenerationAgent, "_run_pipeline", stop_after_l0)
    agent = DataGenerationAgent(tmp_path / "dataset", project_generator=Generator())

    agent.run_one(
        "layered_direct",
        "Design a counter.",
        request,
        platform,
        metadata={"method_condition": "M0"},
    )

    assert calls == ["common_project_l0"]
