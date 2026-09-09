from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from dataclasses import replace

import pytest

from sr2fpga_agent.models import GeneratedProject, ToolResult
from sr2fpga_agent.public_evaluator import (
    DevelopmentPublicToolEvaluator,
    PublicEvaluatorInput,
)
from sr2fpga_agent.public_l2_harness import (
    DevelopmentTrustedPublicL2Harness,
    PublicL2HarnessError,
    TrustedPublicL2HarnessFile,
    load_development_public_l2_harness,
    candidate_simulation_violations,
)
from sr2fpga_agent.local_tools import resolve_executable


def _project() -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {"ports": []},
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [
            {
                "path": "sim/tb_top.v",
                "role": "candidate_testbench",
                "applicability": "advisory",
            }
        ],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/top.v": "module top; endmodule\n",
            "sim/tb_top.v": (
                "module malicious_candidate_tb; initial begin "
                "$display(\"TEST_PASS\"); $finish; end endmodule\n"
            ),
        },
    )


def _harness() -> DevelopmentTrustedPublicL2Harness:
    content = "module trusted_tb; top dut(); initial $finish; endmodule\n"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return DevelopmentTrustedPublicL2Harness(
        harness_id="trusted-counter8-v1",
        testbench_top="trusted_tb",
        language_standard="verilog-2005",
        files=(TrustedPublicL2HarnessFile("tb.v", content, digest),),
        timeout_seconds=20,
        manifest_sha256="a" * 64,
        bundle_sha256="b" * 64,
    )


class _ScriptedRunner:
    def __init__(self, *, failed_stage: str | None = None) -> None:
        self.failed_stage = failed_stage
        self.calls: list[tuple[list[str], Path, str, int]] = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        self.calls.append((list(command), Path(cwd), stage, timeout_seconds))
        failed = stage == self.failed_stage
        stdout = "PRIVATE TRUSTED HARNESS LOG"
        if stage == "public_l2_sim":
            trusted_text = "\n".join(path.read_text(encoding="utf-8") for path in (Path(cwd) / "__sr2fpga_trusted_public_l2").rglob("*.*"))
            stdout = "\n".join(re.findall(r"SR2FPGA_TRUSTED_COMPLETE_[0-9a-f]{32}", trusted_text)) + "\n"
        return ToolResult(
            stage=stage,
            command=list(command),
            status="failed" if failed else "passed",
            exit_code=1 if failed else 0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.01,
        )


def _input() -> PublicEvaluatorInput:
    return PublicEvaluatorInput(
        terminal_project=_project(),
        terminal_candidate_sha256="c" * 64,
        public_contract_sha256="d" * 64,
        public_profile_sha256="e" * 64,
        tool_environment_policy_sha256="f" * 64,
    )


def test_harness_loader_validates_schema_files_and_hashes(tmp_path: Path) -> None:
    harness_source = tmp_path / "trusted_tb.v"
    content = "module trusted_tb; initial $finish; endmodule\n"
    harness_source.write_text(content, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    manifest = {
        "contract_version": "development-public-l2-harness-v1",
        "harness_id": "trusted-counter8-v1",
        "evaluation_scope": "development_excluded_public_l2",
        "testbench_top": "trusted_tb",
        "language_standard": "verilog-2005",
        "files": [{"path": "trusted_tb.v", "sha256": digest}],
        "timeout_seconds": 20,
        "pass_rule": "simulator_exit_zero",
        "official_authority": False,
        "g4b_authorized": False,
    }
    manifest_path = tmp_path / "harness.json"
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    loaded = load_development_public_l2_harness(manifest_path)

    assert loaded.harness_id == "trusted-counter8-v1"
    assert loaded.files[0].content == content
    assert len(loaded.manifest_sha256) == 64
    assert len(loaded.bundle_sha256) == 64

    harness_source.write_text("tampered\n", encoding="utf-8", newline="\n")
    with pytest.raises(PublicL2HarnessError, match="hash mismatch"):
        load_development_public_l2_harness(manifest_path)


def test_trusted_public_l2_ignores_candidate_tb_and_runs_fixed_compile_and_sim(
    tmp_path: Path,
) -> None:
    runner = _ScriptedRunner()
    result = DevelopmentPublicToolEvaluator(
        tmp_path / "workspaces",
        command_runner=runner,
        trusted_public_l2_harness=_harness(),
    )(_input(), "evaluation-pass")

    assert result.stage_outcomes["public_l2"] == {"status": "pass", "reason": None}
    assert result.public_l2_harness == _harness().public_evidence()
    assert [call[2] for call in runner.calls] == [
        "public_l1_lint",
        "public_l2_compile",
        "public_l2_sim",
        "public_l3_synth",
    ]
    compile_command = runner.calls[1][0]
    assert "rtl/top.v" in compile_command
    assert "sim/tb_top.v" not in compile_command
    assert "__sr2fpga_trusted_public_l2/tb.v" in compile_command
    assert runner.calls[1][3] == 20
    assert runner.calls[2][3] == 20


def test_trusted_public_l2_failure_is_public_failure_and_l3_still_runs(
    tmp_path: Path,
) -> None:
    runner = _ScriptedRunner(failed_stage="public_l2_sim")
    result = DevelopmentPublicToolEvaluator(
        tmp_path / "workspaces",
        command_runner=runner,
        trusted_public_l2_harness=_harness(),
    )(_input(), "evaluation-fail")

    assert result.execution_status == "completed"
    assert result.stage_outcomes["public_l2"] == {
        "status": "fail",
        "reason": "public_l2_failed",
    }
    assert result.stage_outcomes["l3"] == {"status": "pass", "reason": None}
    assert "public_l2_failed" in result.diagnostic_codes
    assert runner.calls[-1][2] == "public_l3_synth"


def test_trusted_public_l2_rejects_candidate_collision_with_reserved_workspace(
    tmp_path: Path,
) -> None:
    project = _project()
    manifest = json.loads(project.files["manifest.json"])
    manifest["sources"].append(
        {
            "path": "__sr2fpga_trusted_public_l2/tb.v",
            "role": "rtl_source",
            "language": "verilog",
        }
    )
    files = dict(project.files)
    files["manifest.json"] = json.dumps(manifest, sort_keys=True) + "\n"
    files["__sr2fpga_trusted_public_l2/tb.v"] = (
        "module candidate_reserved_collision; endmodule\n"
    )
    runner = _ScriptedRunner()

    result = DevelopmentPublicToolEvaluator(
        tmp_path / "workspaces",
        command_runner=runner,
        trusted_public_l2_harness=_harness(),
    )(
        PublicEvaluatorInput(
            terminal_project=GeneratedProject(project.project_name, files),
            terminal_candidate_sha256="c" * 64,
            public_contract_sha256="d" * 64,
            public_profile_sha256="e" * 64,
            tool_environment_policy_sha256="f" * 64,
        ),
        "evaluation-collision",
    )

    assert result.stage_outcomes["l0"] == {
        "status": "fail",
        "reason": "public_l0_failed",
    }
    assert "public_l2_reserved_path_collision" in result.diagnostic_codes
    assert runner.calls == []


@pytest.mark.parametrize("body", [
    "initial $finish;", "initial $stop;", "initial $finish_and_return(0);",
    '`define EXIT $fi``nish\ninitial `EXIT;',
    'initial $display("SR2FPGA_TRUSTED_COMPLETE_fake");',
    "initial trusted_tb.finish_test();", "initial other_block.finish_test();",
    '`include "sim/tb_top.v"', '`include "../../private.vh"',
])
def test_candidate_cannot_control_or_forge_trusted_completion(tmp_path: Path, body: str) -> None:
    original = _input()
    project = GeneratedProject("counter8", {**original.terminal_project.files, "rtl/top.v": f"module top;\n{body}\nendmodule\n"})
    runner = _ScriptedRunner()
    result = DevelopmentPublicToolEvaluator(tmp_path, command_runner=runner, trusted_public_l2_harness=_harness())(
        replace(original, terminal_project=project), "blocked"
    )
    assert result.stage_outcomes["l0"]["status"] == "fail"
    assert result.stage_outcomes["public_l2"]["status"] == "not_run"
    assert runner.calls == []


def test_candidate_guard_ignores_comments_and_strings_but_follows_headers() -> None:
    files = {"rtl/top.v": '`include "rtl/params.vh"\nmodule top; /* $finish; */ parameter MSG="$finish"; endmodule',
             "rtl/params.vh": "localparam N = $clog2(8);"}
    assert candidate_simulation_violations(files, ["rtl/top.v"], []) == ()
    files["rtl/params.vh"] = "initial $finish;"
    assert candidate_simulation_violations(files, ["rtl/top.v"], [])
    assert candidate_simulation_violations(
        {"top.v": "module top; initial finish_test(); endmodule"}, ["top.v"],
        ["module trusted_tb; task automatic finish_test; $finish; endtask endmodule"],
    )


@pytest.mark.parametrize(("statement", "expected"), [
    ("#1; $finish;", "pass"),
    ('#1; $fatal(1, "required check failed");', "fail"),
    ("if (0) $finish;", "fail"),
    ("forever #1;", "not_run"),
])
def test_real_tools_require_reachable_trusted_completion(tmp_path: Path, statement: str, expected: str) -> None:
    if any(resolve_executable(tool) is None for tool in ("verilator", "iverilog", "vvp", "yosys")):
        pytest.skip("local HDL tools unavailable")
    content = f"module trusted_tb; top dut(); initial begin {statement} end endmodule\n"
    harness = replace(_harness(), files=(TrustedPublicL2HarnessFile("tb.v", content, hashlib.sha256(content.encode()).hexdigest()),), timeout_seconds=1)
    result = DevelopmentPublicToolEvaluator(tmp_path, trusted_public_l2_harness=harness)(_input(), "real-tools")
    assert result.stage_outcomes["public_l2"]["status"] == expected


def test_real_tools_isolate_candidate_macros_and_select_manifest_top(tmp_path: Path) -> None:
    if any(resolve_executable(tool) is None for tool in ("verilator", "iverilog", "vvp", "yosys")):
        pytest.skip("local HDL tools unavailable")
    files = dict(_project().files)
    files["rtl/top.v"] = "`define SKIP_CHECKS\nmodule top; endmodule\n"
    files["rtl/helper.v"] = "module helper; endmodule\n"
    manifest = json.loads(files["manifest.json"])
    manifest["sources"].append({"path": "rtl/helper.v", "role": "rtl_source", "language": "verilog"})
    files["manifest.json"] = json.dumps(manifest)
    content = 'module trusted_tb; top dut(); initial begin\n`ifdef SKIP_CHECKS\n$finish;\n`else\n$fatal(1, "required check");\n`endif\nend endmodule\n'
    harness = replace(_harness(), files=(TrustedPublicL2HarnessFile("tb.v", content, hashlib.sha256(content.encode()).hexdigest()),))
    result = DevelopmentPublicToolEvaluator(tmp_path, trusted_public_l2_harness=harness)(replace(_input(), terminal_project=GeneratedProject("counter8", files)), "macros")
    assert result.stage_outcomes["l1"]["status"] == "pass"
    assert result.stage_outcomes["public_l2"]["status"] == "fail"
