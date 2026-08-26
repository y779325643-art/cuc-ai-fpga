from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
)


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
        return ToolResult(
            stage=stage,
            command=list(command),
            status="failed" if failed else "passed",
            exit_code=1 if failed else 0,
            stdout="PRIVATE TRUSTED HARNESS LOG",
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
