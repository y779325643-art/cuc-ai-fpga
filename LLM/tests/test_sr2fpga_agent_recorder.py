import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent import GeneratedProject, PlatformProfile, ProjectGenerator, ProjectRequest
from LLM.src.sr2fpga_agent.agent import DataGenerationAgent, RepairResult
from LLM.src.sr2fpga_agent.models import RepairResult as ModelRepairResult
from LLM.src.sr2fpga_agent.models import ToolResult
from LLM.src.sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0


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

            metadata = {
                "source": "deepseek",
                "generator_provider": "deepseek",
                "failure_origin": "natural_llm",
                "difficulty_tier": "T2",
                "measurement_point": "a_first_attempt_no_tools",
                "repair_provider": "none",
                "failure_injectors": [],
                "system_his_schema_version": "system-his-v1.1",
            }
            sample_dir = recorder.start_sample("sample_000001", requirement, platform, metadata=metadata)
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
            self.assertEqual(json.loads((sample_dir / "metadata.json").read_text(encoding="utf-8")), metadata)

            requirement_rows = (export_dir / "requirement_to_his.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(requirement_rows), 1)
            requirement_row = json.loads(requirement_rows[0])
            self.assertEqual(requirement_row["sample_id"], "sample_000001")
            self.assertIn("system_his", requirement_row)
            self.assertEqual(requirement_row["metadata"]["failure_origin"], "natural_llm")

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
                self.assertEqual(json.loads(rows[0])["metadata"]["difficulty_tier"], "T2")

    def test_l0_checker_rejects_manifest_that_violates_system_his_contract(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            platform,
        )
        broken_files = dict(project.files)
        manifest = json.loads(broken_files["manifest.json"])
        manifest["top_module"] = "missing_top"
        broken_files["manifest.json"] = json.dumps(manifest) + "\n"
        broken_project = GeneratedProject(project_name=project.project_name, files=broken_files)

        result = check_project_l0(broken_project)

        self.assertFalse(result.passed)
        self.assertIn("manifest.top_module 'missing_top' does not match System-HIS top_module 'top'", result.errors)

    def test_l0_checker_accepts_system_his_v12_topdown_contract(self) -> None:
        system_his = json.loads(
            Path("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json").read_text(encoding="utf-8")
        )
        files = {
            "system_his.json": json.dumps(system_his) + "\n",
            "manifest.json": json.dumps(
                {
                    "project_name": "join_8bit",
                    "top_module": "top",
                    "sources": system_his["artifacts"]["rtl_sources"],
                    "constraints": {"timing": "constraints/timing.sdc"},
                    "simulation": {"testbench": "sim/tb_top.v"},
                    "reports": ["reports/predicted_qor.json"],
                }
            )
            + "\n",
            "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
            "sim/tb_top.v": "module tb_top; initial $display(\"TEST_PASS\"); endmodule\n",
            "reports/predicted_qor.json": "{}\n",
        }
        for source in system_his["artifacts"]["rtl_sources"]:
            module_name = Path(source).stem if source != "rtl/top.v" else "top"
            files[source] = f"module {module_name}; endmodule\n"

        result = check_project_l0(GeneratedProject(project_name="join_8bit", files=files))

        self.assertTrue(result.passed, result.errors)

    def test_l0_checker_rejects_system_his_module_source_outside_manifest(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["modules"][0]["source"] = "rtl/not_in_manifest.v"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' source 'rtl/not_in_manifest.v' is not in manifest.sources", result.errors)

    def test_l0_checker_rejects_connection_to_unknown_module(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["to"]["module"] = "missing_core"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS connection[0].to.module 'missing_core' is not declared", result.errors)

    def test_l0_checker_rejects_connection_to_unknown_port(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["to"]["port"] = "missing_port"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn(
            "System-HIS connection[0].to.port 'missing_port' is not declared on module 'baud_tick_gen'",
            result.errors,
        )

    def test_l0_checker_rejects_unknown_module_parameter(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="composed_stream_accumulator", width=8, project_name="stream_accum_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        for module in system_his["modules"]:
            if module["name"] == "accumulator_core":
                module["parameters"]["BAD_PARAM"] = 1
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'accumulator_core' parameter 'BAD_PARAM' is not declared in RTL", result.errors)

    def test_l0_checker_rejects_system_his_port_direction_mismatch(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        for port in system_his["modules"][0]["ports"]:
            if port["name"] == "count":
                port["direction"] = "input"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' port 'count' direction 'input' does not match RTL 'output'", result.errors)

    def test_l0_checker_rejects_system_his_port_width_mismatch(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        for port in system_his["modules"][0]["ports"]:
            if port["name"] == "count":
                port["width"] = 7
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' port 'count' width 7 does not match RTL 8", result.errors)

    def test_l0_checker_accepts_numeric_range_width_equivalent_to_integer_width(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        files = dict(project.files)
        system_his = json.loads(files["system_his.json"])
        for collection in (system_his["top_ports"], system_his["modules"][0]["ports"]):
            for port in collection:
                if port["name"] == "count":
                    port["width"] = "[7:0]"
        files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=files))

        self.assertTrue(result.passed, result.errors)

    def test_l0_checker_rejects_testbench_that_instantiates_wrong_top(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        broken_files["sim/tb_top.v"] = broken_files["sim/tb_top.v"].replace("top dut", "missing_top dut")

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("manifest testbench 'sim/tb_top.v' does not instantiate top module 'top'", result.errors)

    def test_l0_checker_rejects_timing_constraint_that_references_unknown_port(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        broken_files["constraints/timing.sdc"] = "create_clock -name clk -period 10.000 [get_ports missing_clk]\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("manifest timing constraint 'constraints/timing.sdc' references unknown top port 'missing_clk'", result.errors)

    def test_l0_checker_rejects_system_his_top_ports_that_do_not_match_rtl(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["top_ports"] = [{"name": "missing", "direction": "input", "width": 1}]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.top_ports does not match top module RTL ports", result.errors)

    def test_l0_checker_rejects_module_missing_intent(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        del system_his["modules"][0]["intent"]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' intent is required", result.errors)

    def test_l0_checker_rejects_verification_missing_test_pass_means(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        del system_his["verification"]["test_pass_means"]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.verification.test_pass_means is required", result.errors)

    def test_l0_checker_rejects_clock_without_positive_target_fmax(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["clocks"][0]["target_fmax_mhz"] = 0
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.clocks[0].target_fmax_mhz must be positive", result.errors)

    def test_l0_checker_rejects_reset_with_invalid_polarity(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["resets"][0]["polarity"] = "lowish"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.resets[0].polarity is invalid", result.errors)

    def test_l0_checker_rejects_qor_intent_missing_resource_field(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        del system_his["qor_intent"]["resources"]["lut"]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.qor_intent.resources.lut is required", result.errors)

    def test_l0_checker_rejects_connection_with_invalid_protocol(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["protocol"] = "mystery_bus"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS connection[0].protocol is invalid", result.errors)

    def test_l0_checker_rejects_connection_with_invalid_width_or_cdc(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["width"] = 0
        system_his["connections"][0]["cdc"] = "false"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS connection[0].width must be positive", result.errors)
        self.assertIn("System-HIS connection[0].cdc must be boolean", result.errors)

    def test_agent_stops_before_tools_when_l0_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=BrokenManifestGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="broken_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_l0_fail",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_l0_fail"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L0")
            self.assertFalse(labels["checks"]["l0_complete"])
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "l0_consistency")
            self.assertEqual(runner.calls, [])

    def test_agent_stops_before_verilator_when_rtl_identifier_is_reserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=ReservedIdentifierGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="reserved_identifier_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_reserved_identifier",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_reserved_identifier"
            self.assertEqual(result["pass_level"], "L0")
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertTrue(labels["checks"]["l0_complete"])
            self.assertFalse(labels["checks"]["l1_lint_pass"])
            self.assertEqual(diagnosis["stage"], "rtl_identifier_check")
            self.assertEqual(diagnosis["failure_type"], "rtl_reserved_identifier")
            self.assertIn("rtl/top.v", diagnosis["root_cause"])
            self.assertIn("'buf'", diagnosis["root_cause"])
            self.assertEqual([item["stage"] for item in trajectory["attempts"]], ["rtl_identifier_check"])
            self.assertEqual(runner.calls, [])

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
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "sim_compile", "sim_run", "synth"],
            )
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
            first_failed = next(item for item in trajectory["attempts"] if item["status"] == "failed")
            self.assertEqual(first_failed["attempt_id"], 0)
            self.assertEqual(first_failed["stage"], "lint")
            self.assertEqual(trajectory["attempts"][-1]["attempt_id"], 1)
            self.assertEqual(trajectory["attempts"][-1]["stage"], "synth")

            export_dir = Path(tmp) / "exports"
            DatasetRecorder(root).export_training_views(export_dir)
            patch_rows = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(patch_rows), 1)
            patch_row = json.loads(patch_rows[0])
            self.assertEqual(patch_row["sample_id"], "sample_000002")
            self.assertEqual(patch_row["diagnosis"]["failure_type"], "port_mismatch")
            self.assertIn("fix reset port", patch_row["patch"])

    def test_agent_treats_test_fail_output_as_failed_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = SemanticFailRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_000003",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_000003"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis_path = sample_dir / "attempts/attempt_000/diagnosis.json"
            self.assertTrue(diagnosis_path.exists())
            diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L1")
            self.assertFalse(labels["checks"]["l2_sim_pass"])
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "sim_run")
            self.assertIn("TEST_FAIL", diagnosis["root_cause"])
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "sim_compile", "sim_run"],
            )

    def test_repair_result_is_shared_model_and_agent_compatible(self) -> None:
        self.assertIs(RepairResult, ModelRepairResult)

    def test_export_training_views_ignores_hidden_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            requirement = "Design an 8-bit counter with enable and active-low reset."
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )
            recorder.start_sample("sample_000001", requirement, platform)
            recorder.write_final(
                "sample_000001",
                project,
                labels={"pass_level": "L3"},
                measured_qor={"lut": 1, "ff": 8, "bram": 0, "dsp": 0},
                tool_versions={"yosys": "unknown"},
                trajectory={"sample_id": "sample_000001", "attempts": []},
            )
            hidden_file = root / "sample_000001" / "final" / "generated_project" / ".DS_Store"
            hidden_file.write_bytes(b"\x00\x80binary finder metadata")

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            rows = (export_dir / "requirement_to_project.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 1)
            exported_paths = [item["path"] for item in json.loads(rows[0])["files"]]
            self.assertNotIn(".DS_Store", exported_paths)


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
                    "schema_version": "system-his-v1.1",
                    "project": {"name": request.project_name, "description": request.description, "top": "top"},
                    "clocks": [{"name": "clk", "target_fmax_mhz": 100.0}],
                    "resets": [{"name": "rst_n", "polarity": "active_low", "kind": "async"}],
                    "project_name": request.project_name,
                    "task_type": request.task_type,
                    "system": {"description": request.description},
                    "interface": {"clock": "clk", "reset": "rst_n", "ports": []},
                    "architecture": {"top_module": "top", "submodules": []},
                    "modules": [
                        {
                            "name": "top",
                            "role": "top",
                            "source": "rtl/top.v",
                            "clock": "clk",
                            "reset": "rst_n",
                            "parameters": {},
                            "params": [],
                            "ports": [
                                {"name": "clk", "direction": "input", "width": 1},
                                {"name": "out", "direction": "output", "width": 1},
                            ],
                            "intent": "top-level integration wrapper for a fake LLM project",
                        }
                    ],
                    "connections": [],
                    "top_ports": [
                        {"name": "clk", "direction": "input", "width": 1},
                        {"name": "out", "direction": "output", "width": 1},
                    ],
                    "platform": {"name": platform.name},
                    "verification": {
                        "testbench": "sim/tb_top.v",
                        "checks": ["l0_contract", "l1_lint", "l2_self_checking_sim", "l3_synthesis"],
                        "test_pass_means": "Self-checking testbench prints TEST_PASS only when out follows clk.",
                    },
                    "qor_intent": {"resources": {"lut": 1, "ff": 0, "bram": 0, "dsp": 0}},
                }
            )
            + "\n",
            "manifest.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "top_module": "top",
                    "sources": ["rtl/top.v"],
                    "constraints": {"timing": "constraints/timing.sdc"},
                    "simulation": {"testbench": "sim/tb_top.v"},
                    "reports": {"predicted_qor": "reports/predicted_qor.json"},
                }
            )
            + "\n",
            "rtl/top.v": "module top(input wire clk, output wire out); assign out = clk; endmodule // LLM_GENERATED_MARKER\n",
            "constraints/timing.sdc": "create_clock -name clk -period 10.000 [get_ports clk]\n",
            "sim/tb_top.v": (
                "module tb_top; reg clk; wire out; top dut(.clk(clk), .out(out)); "
                "initial begin clk = 1'b0; $display(\"TEST_PASS\"); $finish; end endmodule\n"
            ),
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


class SemanticFailRunner(FakeRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "sim_run":
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            return ToolResult(
                stage=stage,
                command=list(command),
                status="passed",
                exit_code=0,
                stdout="TEST_FAIL semantic mismatch\n",
                stderr="",
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class FakeRepairer:
    def repair(self, project, diagnosis):
        return RepairResult(generated_project=project, patch_diff="diff --git a/rtl/top.v b/rtl/top.v\n# fix reset port\n")


class BrokenManifestGenerator:
    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        manifest = json.loads(files["manifest.json"])
        manifest["top_module"] = "missing_top"
        files["manifest.json"] = json.dumps(manifest) + "\n"
        return GeneratedProject(project_name=project.project_name, files=files)


class ReservedIdentifierGenerator:
    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        files["rtl/top.v"] = files["rtl/top.v"].replace(");\n\n  always", ");\n\n  reg [7:0] buf;\n\n  always")
        return GeneratedProject(project_name=project.project_name, files=files)


if __name__ == "__main__":
    unittest.main()
