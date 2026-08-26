import json

import pytest

from sr2fpga_agent.generation.direct_project import DirectProjectGenerator
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.parsers import (
    PROJECT_PACKAGE_VERSION,
    check_project_package_l0,
    parse_project_files,
    resolve_project_manifest,
)
from sr2fpga_agent.repair import ProjectRepairer


def _canonical_manifest(
    *,
    top_module: str = "design_top",
    top_source: str = "src/design.sv",
    sources: list[str] | None = None,
    top_ports: list[dict[str, object]] | None = None,
    artifacts: list[dict[str, str]] | None = None,
    language: str = "systemverilog",
) -> str:
    source_paths = sources or [top_source]
    return json.dumps(
        {
            "contract_version": PROJECT_PACKAGE_VERSION,
            "project_name": "role_based_design",
            "top": {
                "module": top_module,
                "source": top_source,
                "interface": {"ports": top_ports if top_ports is not None else []},
            },
            "sources": [
                {"path": path, "role": "rtl_source", "language": language}
                for path in source_paths
            ],
            "artifacts": artifacts or [],
            "build": {
                "toolchain_id": "open_source",
                "language_standard": "systemverilog-2017",
            },
        }
    )


class _StaticChatClient:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def chat(self, messages: list[dict[str, str]]) -> str:
        del messages
        return self.payload


def test_canonical_package_accepts_nonstandard_top_without_optional_artifacts() -> None:
    payload = json.dumps(
        {
            "files": {
                "manifest.json": _canonical_manifest(),
                "src/design.sv": "module design_top; endmodule",
            }
        }
    )

    files = parse_project_files(payload, expected_task_type="composed_dual_stream_join")
    resolved = resolve_project_manifest(files)
    result = check_project_package_l0(
        GeneratedProject(project_name="role_based_design", files=files)
    )

    assert result.passed, result.errors
    assert resolved.contract_version == PROJECT_PACKAGE_VERSION
    assert resolved.top_module == "design_top"
    assert resolved.top_source == "src/design.sv"
    assert resolved.sources == ("src/design.sv",)
    assert resolved.artifact_paths_by_role == {}
    assert "system_his.json" not in files
    assert "sim/tb_top.v" not in files
    assert "reports/predicted_qor.json" not in files
    assert "constraints/timing.sdc" not in files


def test_legacy_direct_and_system_his_packages_remain_readable() -> None:
    direct_files = {
        "manifest.json": json.dumps(
            {
                "project_name": "legacy_direct",
                "top_module": "legacy_top",
                "sources": ["legacy/design.v"],
            }
        ),
        "legacy/design.v": "module legacy_top; endmodule\n",
    }
    direct = resolve_project_manifest(direct_files)
    assert direct.is_legacy
    assert direct.top_source == "legacy/design.v"
    assert check_project_package_l0(
        GeneratedProject(project_name="legacy_direct", files=direct_files)
    ).passed

    his_files = {**direct_files, "system_his.json": "{}\n"}
    his = resolve_project_manifest(his_files)
    assert his.artifact_paths_by_role["system_his"] == ("system_his.json",)
    assert check_project_package_l0(
        GeneratedProject(project_name="legacy_direct", files=his_files)
    ).passed


def test_canonical_package_requires_every_rtl_file_to_have_a_source_role() -> None:
    files = {
        "manifest.json": _canonical_manifest(),
        "src/design.sv": "module design_top; endmodule\n",
        "src/undeclared.sv": "module undeclared; endmodule\n",
    }

    with pytest.raises(ValueError, match="does not declare project files"):
        resolve_project_manifest(files)


def test_manifest_source_references_remain_path_safe_and_complete() -> None:
    unsafe_files = {
        "manifest.json": _canonical_manifest(top_source="../escape.sv"),
    }
    with pytest.raises(ValueError, match="unsafe project file path"):
        resolve_project_manifest(unsafe_files)

    missing_files = {"manifest.json": _canonical_manifest()}
    with pytest.raises(ValueError, match="missing source files: src/design.sv"):
        resolve_project_manifest(missing_files)


def test_canonical_reader_rejects_manifest_outside_the_registered_schema() -> None:
    manifest = json.loads(_canonical_manifest())
    manifest["sources"][0]["language"] = "verilog-2026"
    files = {
        "manifest.json": json.dumps(manifest),
        "src/design.sv": "module design_top; endmodule\n",
    }

    with pytest.raises(ValueError, match="does not satisfy project-package-v1"):
        resolve_project_manifest(files)


def test_common_l0_requires_the_declared_top_source_to_define_the_top() -> None:
    files = {
        "manifest.json": _canonical_manifest(
            top_source="src/wrapper.sv",
            sources=["src/wrapper.sv", "src/actual_top.sv"],
        ),
        "src/wrapper.sv": "module wrapper; endmodule\n",
        "src/actual_top.sv": "module design_top; endmodule\n",
    }

    result = check_project_package_l0(
        GeneratedProject(project_name="role_based_design", files=files)
    )

    assert not result.passed
    assert result.errors == [
        "top source 'src/wrapper.sv' does not declare top module 'design_top'"
    ]


def test_common_l0_rejects_a_self_reported_top_interface_mismatch() -> None:
    files = {
        "manifest.json": _canonical_manifest(
            top_ports=[{"name": "clk", "direction": "output", "width": 1}],
        ),
        "src/design.sv": "module design_top(input wire clk); endmodule\n",
    }

    result = check_project_package_l0(
        GeneratedProject(project_name="role_based_design", files=files)
    )

    assert not result.passed
    assert result.errors == [
        "top port 'clk' direction 'input' does not match manifest direction 'output'"
    ]


def test_declared_optional_artifact_must_exist_but_is_not_universally_required() -> None:
    files = {
        "manifest.json": _canonical_manifest(
            artifacts=[
                {
                    "path": "sim/smoke_tb.sv",
                    "role": "candidate_testbench",
                    "applicability": "advisory",
                }
            ]
        ),
        "src/design.sv": "module design_top; endmodule\n",
    }

    with pytest.raises(ValueError, match="missing artifact files: sim/smoke_tb.sv"):
        resolve_project_manifest(files)


@pytest.mark.parametrize("role", ["candidate_testbench", "board_wrapper"])
def test_only_explicit_non_design_rtl_artifact_roles_are_source_exempt(role: str) -> None:
    artifact_path = "sim/smoke_tb.sv" if role == "candidate_testbench" else "board/shell.sv"
    files = {
        "manifest.json": _canonical_manifest(
            artifacts=[
                {
                    "path": artifact_path,
                    "role": role,
                    "applicability": "advisory",
                }
            ]
        ),
        "src/design.sv": "module design_top; endmodule\n",
        artifact_path: "module artifact_shell; endmodule\n",
    }

    resolved = resolve_project_manifest(files)

    assert resolved.sources == ("src/design.sv",)


def test_helper_rtl_must_be_declared_as_a_design_source() -> None:
    files = {
        "manifest.json": _canonical_manifest(
            artifacts=[
                {
                    "path": "support/helper.sv",
                    "role": "helper",
                    "applicability": "advisory",
                }
            ]
        ),
        "src/design.sv": "module design_top; endmodule\n",
        "support/helper.sv": "module helper; endmodule\n",
    }

    with pytest.raises(
        ValueError,
        match="manifest.sources does not declare all RTL files: support/helper.sv",
    ):
        resolve_project_manifest(files)


def test_common_l0_fails_closed_for_non_ansi_top_ports() -> None:
    files = {
        "manifest.json": _canonical_manifest(
            top_ports=[
                {"name": "clk", "direction": "input", "width": 1},
                {"name": "done", "direction": "output", "width": 1},
            ]
        ),
        "src/design.sv": (
            "module design_top(clk, done);\n"
            "  input clk;\n"
            "  output done;\n"
            "endmodule\n"
        ),
    }

    result = check_project_package_l0(
        GeneratedProject(project_name="role_based_design", files=files)
    )

    assert not result.passed
    assert result.errors == [
        "top interface validation does not support non-ANSI port declarations"
    ]


def test_common_l0_leaves_vhdl_to_backend_capability_routing() -> None:
    files = {
        "manifest.json": _canonical_manifest(
            top_source="src/design_top.vhd",
            language="vhdl",
            top_ports=[{"name": "clk", "direction": "input", "width": 1}],
        ),
        "src/design_top.vhd": "entity design_top is end entity;\n",
    }

    result = check_project_package_l0(
        GeneratedProject(project_name="role_based_design", files=files)
    )

    assert result.passed, result.errors


def test_direct_generation_requires_canonical_manifest() -> None:
    legacy_files = {
        "manifest.json": json.dumps(
            {"project_name": "legacy", "top_module": "top", "sources": ["rtl/top.v"]}
        ),
        "rtl/top.v": "module top; endmodule\n",
    }
    generator = DirectProjectGenerator(
        _StaticChatClient(json.dumps({"files": legacy_files})),
        max_attempts=1,
    )

    with pytest.raises(ValueError, match="must use canonical project-package-v1"):
        generator.generate(
            ProjectRequest(task_type="counter", width=8, project_name="direct"),
            PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
        )


@pytest.mark.parametrize(
    ("original_manifest", "repair_manifest", "error"),
    [
        (
            _canonical_manifest(
                top_module="top",
                top_source="rtl/top.v",
                top_ports=[],
                language="verilog",
            ),
            json.dumps({"project_name": "legacy", "top_module": "top", "sources": ["rtl/top.v"]}),
            "must use canonical project-package-v1",
        ),
        (
            json.dumps({"project_name": "legacy", "top_module": "top", "sources": ["rtl/top.v"]}),
            _canonical_manifest(
                top_module="top",
                top_source="rtl/top.v",
                top_ports=[],
                language="verilog",
            ),
            "must preserve the legacy manifest generation",
        ),
    ],
)
def test_repair_preserves_manifest_generation(
    original_manifest: str,
    repair_manifest: str,
    error: str,
) -> None:
    original = GeneratedProject(
        project_name="repair_generation",
        files={
            "manifest.json": original_manifest,
            "rtl/top.v": "module top; endmodule\n",
        },
    )
    repairer = ProjectRepairer(
        _StaticChatClient(
            json.dumps(
                {
                    "files": {
                        "manifest.json": repair_manifest,
                        "rtl/top.v": "module top; endmodule\n",
                    }
                }
            )
        ),
        max_attempts=1,
    )

    with pytest.raises(ValueError, match=error):
        repairer.repair(
            original,
            {"stage": "lint", "root_cause": "syntax error", "affected_files": ["rtl/top.v"]},
        )
