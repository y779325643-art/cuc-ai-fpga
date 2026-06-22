import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent import GeneratedProject, PlatformProfile, ProjectGenerator, ProjectRequest
from LLM.src.sr2fpga_agent.agent import DataGenerationAgent, RepairResult
from LLM.src.sr2fpga_agent.models import RepairResult as ModelRepairResult
from LLM.src.sr2fpga_agent.models import ToolResult
from LLM.src.sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder


class DatasetRecorderTest(unittest.TestCase):
    def test_records_attempt_final_outputs_and_training_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            requirement = "Design an 8-bit counter with enable and active-low reset."
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )

            sample_dir = recorder.start_sample("sample_000001", requirement, platform)
            attempt = AttemptRecord(
                attempt_id=0,
                generated_project=project,
                tool_results={
                    "lint": ToolResult(
                        stage="lint",
                        command=["verilator", "--lint-only", "rtl/top.v"],
                        status="failed",
                        exit_code=1,
                        stdout="",
                        stderr="Port rst_n of module top is not declared",
                        duration_seconds=0.1,
                    )
                },
                diagnosis={
                    "failure_type": "port_mismatch",
                    "root_cause": "The testbench and RTL disagree on the reset port.",
                    "affected_files": ["rtl/top.v", "sim/tb_top.v"],
                },
                patch_diff="diff --git a/sim/tb_top.v b/sim/tb_top.v\n",
            )
            recorder.write_attempt("sample_000001", attempt)
            labels = {
                "pass_level": "L3",
                "checks": {
                    "l0_complete": True,
                    "l1_lint_pass": True,
                    "l2_sim_pass": True,
                    "l3_synth_pass": True,
                    "l4_lite_timing_pass": False,
                },
                "final_attempt_id": 1,
                "failure_count": 1,
            }
            measured_qor = {"lut": 4, "ff": 8, "bram": 0, "dsp": 0}
            trajectory = {
                "sample_id": "sample_000001",
                "attempts": [
                    {
                        "attempt_id": 0,
                        "stage": "lint",
                        "status": "failed",
                        "failure_type": "port_mismatch",
                        "patch_path": "attempts/attempt_000/patch.diff",
                    }
                ],
            }
            recorder.write_final(
                "sample_000001",
                project,
                labels=labels,
                measured_qor=measured_qor,
                tool_versions={"verilator": "not-installed"},
                trajectory=trajectory,
            )
            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            self.assertEqual(sample_dir, root / "sample_000001")
            self.assertEqual((sample_dir / "requirement.txt").read_text(encoding="utf-8"), requirement + "\n")
            self.assertTrue((sample_dir / "platform_profile.json").exists())
            self.assertTrue((sample_dir / "attempts/attempt_000/generated_project/rtl/top.v").exists())
            self.assertIn(
                "rst_n",
                (sample_dir / "attempts/attempt_000/eval/lint.log").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))[
                    "failure_type"
                ],
                "port_mismatch",
            )
            self.assertTrue((sample_dir / "attempts/attempt_000/patch.diff").exists())
            self.assertTrue((sample_dir / "final/generated_project/manifest.json").exists())
            self.assertEqual(json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8")), labels)
            self.assertEqual(
                json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))["ff"],
                8,
            )
            self.assertTrue((sample_dir / "eval/trajectory.json").exists())

            requirement_rows = (export_dir / "requirement_to_his.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(requirement_rows), 1)
            requirement_row = json.loads(requirement_rows[0])
            self.assertEqual(requirement_row["sample_id"], "sample_000001")
            self.assertIn("system_his", requirement_row)

            patch_rows = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(patch_rows), 1)
            patch_row = json.loads(patch_rows[0])
            self.assertEqual(patch_row["diagnosis"]["failure_type"], "port_mismatch")
            self.assertIn("diff --git", patch_row["patch"])

            for export_name in (
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "failure_to_diagnosis.jsonl",
                "project_to_predicted_qor.jsonl",
                "project_to_measured_qor.jsonl",
            ):
                rows = (export_dir / export_name).read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(rows), 1, export_name)
                self.assertEqual(json.loads(rows[0])["sample_id"], "sample_000001")

    def test_agent_run_one_records_l3_sample_with_fake_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_000001",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_000001"
            self.assertEqual(result["pass_level"], "L3")
            self.assertTrue((sample_dir / "final/generated_project/rtl/top.v").exists())
            self.assertEqual(
                json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))["pass_level"],
                "L3",
            )
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            self.assertEqual(measured_qor["lut"], 5)
            self.assertEqual(measured_qor["ff"], 8)
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual([item["stage"] for item in trajectory["attempts"]], ["lint", "sim_compile", "sim_run", "synth"])
            self.assertEqual([call["stage"] for call in runner.calls], ["lint", "sim_compile", "sim_run", "synth"])

    def test_agent_records_project_from_injected_llm_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            llm_generator = FakeLLMProjectGenerator()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=llm_generator,
            )
            request = ProjectRequest(
                task_type="counter",
                width=8,
                project_name="llm_counter_8bit",
                description="Design a counter using an LLM-generated package.",
            )
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_llm_000001",
                requirement=request.description,
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_llm_000001"
            top_rtl = (sample_dir / "final/generated_project/rtl/top.v").read_text(encoding="utf-8")
            system_his = json.loads(
                (sample_dir / "final/generated_project/system_his.json").read_text(encoding="utf-8")
            )

            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(llm_generator.call_count, 1)
            self.assertIn("LLM_GENERATED_MARKER", top_rtl)
            self.assertEqual(system_his["system"]["description"], request.description)
            self.assertNotIn("count <= count +", top_rtl)

    def test_agent_records_failed_attempt_patch_and_repaired_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FailThenPassRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                repairer=FakeRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_000002",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_000002"
            self.assertEqual(result["pass_level"], "L3")
            self.assertTrue((sample_dir / "attempts/attempt_000/diagnosis.json").exists())
            self.assertIn(
                "fix reset port",
                (sample_dir / "attempts/attempt_000/patch.diff").read_text(encoding="utf-8"),
            )
            self.assertTrue((sample_dir / "attempts/attempt_001/generated_project/rtl/top.v").exists())
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            self.assertEqual(labels["final_attempt_id"], 1)
            self.assertEqual(labels["failure_count"], 1)
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(trajectory["attempts"][0]["attempt_id"], 0)
            self.assertEqual(trajectory["attempts"][0]["status"], "failed")
            self.assertEqual(trajectory["attempts"][-1]["attempt_id"], 1)
            self.assertEqual(trajectory["attempts"][-1]["stage"], "synth")

    def test_repair_result_is_shared_model_and_agent_compatible(self) -> None:
        self.assertIs(RepairResult, ModelRepairResult)


class FakeRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
        stdout_by_stage = {
            "lint": "",
            "sim_compile": "",
            "sim_run": "TEST_PASS\n",
            "synth": """
                Number of cells: 13
                  SB_LUT4 5
                  SB_DFF 8
            """,
        }
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout_by_stage[stage],
            stderr="",
            duration_seconds=0.01,
        )


class FakeLLMProjectGenerator:
    def __init__(self) -> None:
        self.call_count = 0

    def generate(self, request, platform):
        self.call_count += 1
        files = {
            "system_his.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "task_type": request.task_type,
                    "system": {"description": request.description},
                    "platform": {"name": platform.name},
                }
            )
            + "\n",
            "manifest.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "top_module": "top",
                    "sources": ["rtl/top.v"],
                    "constraints": ["constraints/timing.sdc"],
                    "simulation": {"testbench": "sim/tb_top.v"},
                    "reports": ["reports/predicted_qor.json"],
                }
            )
            + "\n",
            "rtl/top.v": "module top(input wire clk, output wire out); assign out = clk; endmodule // LLM_GENERATED_MARKER\n",
            "constraints/timing.sdc": "create_clock -name clk -period 10.000 [get_ports clk]\n",
            "sim/tb_top.v": "module tb_top; initial begin $display(\"TEST_PASS\"); $finish; end endmodule\n",
            "reports/predicted_qor.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "predicted": {"lut": 1, "ff": 0, "bram": 0, "dsp": 0},
                    "assumptions": {"generator": "fake_llm"},
                }
            )
            + "\n",
        }
        return GeneratedProject(project_name=request.project_name, files=files)


class FailThenPassRunner(FakeRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "lint" and not self.calls:
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            return ToolResult(
                stage=stage,
                command=list(command),
                status="failed",
                exit_code=1,
                stdout="",
                stderr="Port rst_n of module top is not declared",
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class FakeRepairer:
    def repair(self, project, diagnosis):
        return RepairResult(generated_project=project, patch_diff="diff --git a/rtl/top.v b/rtl/top.v\n# fix reset port\n")


if __name__ == "__main__":
    unittest.main()
