"""High-level SR2FPGA data generation orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from LLM.src.sr2fpga_agent.log_parser import classify_failure, parse_yosys_stats
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, ToolResult
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder
from LLM.src.sr2fpga_agent.tool_runner import CommandRunner


class DataGenerationAgent:
    """Generate one dataset sample and run the lightweight tool pipeline."""

    def __init__(
        self,
        dataset_root: Path,
        command_runner: CommandRunner | None = None,
        project_generator: ProjectGenerator | None = None,
        repairer: object | None = None,
        max_attempts: int = 1,
    ) -> None:
        self.dataset_root = dataset_root
        self.recorder = DatasetRecorder(dataset_root)
        self.command_runner = command_runner or CommandRunner()
        self.project_generator = project_generator or ProjectGenerator()
        self.repairer = repairer
        self.max_attempts = max_attempts

    def run_one(
        self,
        sample_id: str,
        requirement: str,
        request: ProjectRequest,
        platform: PlatformProfile,
    ) -> dict[str, Any]:
        project = self.project_generator.generate(request, platform)
        sample_dir = self.recorder.start_sample(sample_id, requirement, platform)

        all_stage_entries: list[dict[str, Any]] = []
        failure_count = 0
        final_attempt_id = 0
        final_tool_results: dict[str, ToolResult] = {}
        final_project = project

        for attempt_id in range(self.max_attempts):
            final_attempt_id = attempt_id
            final_project = project
            project_dir = sample_dir / "attempts" / f"attempt_{attempt_id:03d}" / "generated_project"
            _write_project(project_dir, project)

            tool_results = self._run_pipeline(project_dir)
            final_tool_results = tool_results
            diagnosis = _diagnose_first_failure(tool_results)
            patch_diff = ""

            if diagnosis is not None:
                failure_count += 1
                if self.repairer is not None and attempt_id + 1 < self.max_attempts:
                    repair_result = self.repairer.repair(project, diagnosis)
                    project = repair_result.generated_project
                    patch_diff = repair_result.patch_diff

            all_stage_entries.extend(_stage_entries(attempt_id, tool_results, diagnosis, bool(patch_diff)))
            self.recorder.write_attempt(
                sample_id,
                AttemptRecord(
                    attempt_id=attempt_id,
                    generated_project=final_project,
                    tool_results=tool_results,
                    diagnosis=diagnosis,
                    patch_diff=patch_diff,
                ),
            )

            if diagnosis is None:
                break

        measured_qor = _measured_qor(final_tool_results)
        labels = _labels(final_tool_results, final_attempt_id=final_attempt_id, failure_count=failure_count)
        trajectory = _trajectory(sample_id, all_stage_entries)
        self.recorder.write_final(
            sample_id,
            final_project,
            labels=labels,
            measured_qor=measured_qor,
            tool_versions={"verilator": "unknown", "iverilog": "unknown", "yosys": "unknown"},
            trajectory=trajectory,
        )
        return {"sample_dir": str(sample_dir), "pass_level": labels["pass_level"]}

    def _run_pipeline(self, project_dir: Path) -> dict[str, ToolResult]:
        manifest = json.loads((project_dir / "manifest.json").read_text(encoding="utf-8"))
        sources = list(manifest["sources"])
        testbench = manifest["simulation"]["testbench"]
        top_module = manifest["top_module"]

        results: dict[str, ToolResult] = {}
        results["lint"] = self.command_runner.run(
            ["verilator", "--lint-only", "-Wall", *sources],
            cwd=project_dir,
            stage="lint",
        )
        if results["lint"].status != "passed":
            return results

        results["sim_compile"] = self.command_runner.run(
            ["iverilog", "-g2012", "-o", "sim.out", *sources, testbench],
            cwd=project_dir,
            stage="sim_compile",
        )
        if results["sim_compile"].status != "passed":
            return results

        results["sim_run"] = self.command_runner.run(
            ["vvp", "sim.out"],
            cwd=project_dir,
            stage="sim_run",
        )
        if results["sim_run"].status != "passed":
            return results

        yosys_script = f"read_verilog {' '.join(sources)}; synth -top {top_module}; stat"
        results["synth"] = self.command_runner.run(
            ["yosys", "-p", yosys_script],
            cwd=project_dir,
            stage="synth",
            timeout_seconds=60,
        )
        return results


def _write_project(project_dir: Path, project: GeneratedProject) -> None:
    for relative_path, content in project.files.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _diagnose_first_failure(tool_results: dict[str, ToolResult]) -> dict[str, Any] | None:
    for result in tool_results.values():
        if result.status != "passed":
            log_text = f"{result.stdout}\n{result.stderr}"
            return {
                "failure_type": classify_failure(log_text),
                "stage": result.stage,
                "root_cause": log_text.strip() or result.status,
                "affected_files": [],
            }
    return None


def _measured_qor(tool_results: dict[str, ToolResult]) -> dict[str, Any]:
    synth = tool_results.get("synth")
    if synth is None or synth.status != "passed":
        return {"lut": 0, "ff": 0, "bram": 0, "dsp": 0, "cell_count": 0, "cell_breakdown": {}}
    return parse_yosys_stats(f"{synth.stdout}\n{synth.stderr}")


@dataclass(frozen=True)
class RepairResult:
    """Project returned by a repairer plus the patch used to reach it."""

    generated_project: GeneratedProject
    patch_diff: str


def _labels(tool_results: dict[str, ToolResult], final_attempt_id: int, failure_count: int) -> dict[str, Any]:
    lint_pass = tool_results.get("lint") is not None and tool_results["lint"].status == "passed"
    sim_compile_pass = (
        tool_results.get("sim_compile") is not None and tool_results["sim_compile"].status == "passed"
    )
    sim_run_pass = tool_results.get("sim_run") is not None and tool_results["sim_run"].status == "passed"
    synth_pass = tool_results.get("synth") is not None and tool_results["synth"].status == "passed"

    pass_level = "L0"
    if lint_pass:
        pass_level = "L1"
    if lint_pass and sim_compile_pass and sim_run_pass:
        pass_level = "L2"
    if lint_pass and sim_compile_pass and sim_run_pass and synth_pass:
        pass_level = "L3"

    return {
        "pass_level": pass_level,
        "checks": {
            "l0_complete": True,
            "l1_lint_pass": lint_pass,
            "l2_sim_pass": lint_pass and sim_compile_pass and sim_run_pass,
            "l3_synth_pass": synth_pass,
            "l4_lite_timing_pass": False,
        },
        "final_attempt_id": final_attempt_id,
        "failure_count": failure_count,
    }


def _stage_entries(
    attempt_id: int,
    tool_results: dict[str, ToolResult],
    diagnosis: dict[str, Any] | None,
    has_patch: bool,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for result in tool_results.values():
        entry = {
            "attempt_id": attempt_id,
            "stage": result.stage,
            "status": result.status,
            "tool": result.command[0] if result.command else "",
            "exit_code": result.exit_code,
            "command": result.command,
        }
        if diagnosis is not None and diagnosis["stage"] == result.stage:
            entry["failure_type"] = diagnosis["failure_type"]
            entry["diagnosis_path"] = f"attempts/attempt_{attempt_id:03d}/diagnosis.json"
            if has_patch:
                entry["patch_path"] = f"attempts/attempt_{attempt_id:03d}/patch.diff"
        entries.append(entry)
    return entries


def _trajectory(sample_id: str, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "attempts": attempts,
    }
