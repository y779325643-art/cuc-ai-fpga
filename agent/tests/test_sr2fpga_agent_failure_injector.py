import json
import shutil
import unittest

from rtl_sim_support import compile_and_run, lint_with_verilator

from sr2fpga_agent.failure_injector import (
    FailureInjectingProjectGenerator,
    apply_failure_injectors,
    oracle_mutation_projects,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator


class FailureInjectorTest(unittest.TestCase):
    def test_rename_reset_port_injector_breaks_rtl_without_rewriting_testbench(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["rename_reset_port"])

        self.assertIn("reset_n", injected.files["rtl/top.v"])
        self.assertNotIn("input wire rst_n", injected.files["rtl/top.v"])
        self.assertIn(".rst_n(rst_n)", injected.files["sim/tb_top.v"])
        self.assertEqual(json.loads(injected.files["manifest.json"])["sources"], ["rtl/top.v"])

    def test_missing_manifest_source_injector_adds_absent_source_reference(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["missing_manifest_source"])

        manifest = json.loads(injected.files["manifest.json"])
        self.assertIn("rtl/missing_dependency.v", manifest["sources"])
        self.assertNotIn("rtl/missing_dependency.v", injected.files)

    def test_width_mismatch_injector_changes_top_port_width_only(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["width_mismatch"])

        self.assertIn("output reg [4:0] count", injected.files["rtl/top.v"])
        self.assertIn("wire [3:0] count", injected.files["sim/tb_top.v"])

    def test_width_mismatch_injector_handles_wider_counter(self) -> None:
        project = _counter_project(width=8)

        injected = apply_failure_injectors(project, ["width_mismatch"])

        self.assertIn("output reg [8:0] count", injected.files["rtl/top.v"])
        self.assertIn("wire [7:0] count", injected.files["sim/tb_top.v"])

    def test_testbench_expected_value_mismatch_changes_self_check(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["testbench_expected_value_mismatch"])

        self.assertIn("count !== 4'd5", injected.files["sim/tb_top.v"])
        self.assertIn(
            "TEST_FAIL signal=count cycle=4 expected=4 actual=%0d",
            injected.files["sim/tb_top.v"],
        )

    def test_constraint_missing_clock_injector_references_absent_clock(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["constraint_missing_clock"])

        self.assertEqual(injected.files["constraints/timing.sdc"], "create_clock -name missing_clk -period 10.000 [get_ports missing_clk]\n")

    def test_multimodule_connection_mismatch_changes_top_instantiation_only(self) -> None:
        project = _uart_tx_project()

        injected = apply_failure_injectors(project, ["multimodule_connection_mismatch"])

        self.assertIn("uart_tx_core_missing u_uart_tx_core", injected.files["rtl/top.v"])
        self.assertIn("module uart_tx_core", injected.files["rtl/uart_tx_core.v"])

    def test_failure_injecting_project_generator_wraps_base_generator(self) -> None:
        base = CountingGenerator()
        request = ProjectRequest(task_type="counter", width=4, project_name="counter_4bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = FailureInjectingProjectGenerator(base, ["wrong_top_module"]).generate(request, platform)

        self.assertEqual(base.call_count, 1)
        self.assertEqual(json.loads(project.files["manifest.json"])["top_module"], "missing_top")

    def test_failure_injecting_project_generator_forwards_his_provenance(self) -> None:
        base = CountingGenerator()
        base.his_source_used_for_generation = "oracle_fallback"

        wrapped = FailureInjectingProjectGenerator(base, [])

        self.assertEqual(wrapped.his_source_used_for_generation, "oracle_fallback")

    def test_oracle_mutations_change_only_dut_rtl_for_supported_families(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        for generator_task_type, oracle_task_type in (
            ("fifo", "fifo"),
            ("fifo", "sync_fifo"),
            ("streaming_valid_ready", "streaming_valid_ready"),
            ("fir_filter", "fir_filter"),
            ("matrix_vector_mac", "matrix_vector_mac"),
            ("uart_tx", "uart_tx"),
            ("spi_master", "spi_master"),
        ):
            with self.subTest(task_type=oracle_task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=generator_task_type, width=8, project_name=generator_task_type),
                    platform,
                )

                mutations = oracle_mutation_projects(project, oracle_task_type)

                self.assertTrue(mutations)
                implemented = [mutation for mutation in mutations.values() if mutation is not None]
                self.assertTrue(implemented)
                for mutation in implemented:
                    self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                    self.assertNotEqual(mutation.files, project.files)

    def test_protocol_core_catalog_mutation_suites_are_fully_implemented(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        for task_type in ("fifo", "streaming_valid_ready", "uart_tx", "spi_master"):
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=task_type),
                    platform,
                )

                mutations = oracle_mutation_projects(project, task_type)

                self.assertTrue(mutations)
                self.assertNotIn(None, mutations.values())

    def test_phase_b_uart_catalog_mutations_change_only_dut_rtl(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = (
            (
                "uart_rx",
                ("wrong_sampling_point", "ignore_start_bit", "wrong_shift_direction"),
            ),
            (
                "uart_fifo_loopback",
                ("fifo_drop_byte", "wrong_uart_bit_order", "fifo_order_swap"),
            ),
        )

        for task_type, expected_mutations in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}"),
                    platform,
                )
                mutations = oracle_mutation_projects(project, task_type)

                self.assertEqual(tuple(mutations), expected_mutations)
                for mutation_name, mutation in mutations.items():
                    with self.subTest(task_type=task_type, mutation=mutation_name):
                        self.assertIsNotNone(mutation)
                        changed_paths = {
                            path
                            for path, source in mutation.files.items()
                            if source != project.files[path]
                        }
                        self.assertTrue(changed_paths)
                        self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                        self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_uart_rx_declared_mutations_are_killed_by_unchanged_black_box_oracle(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_rx", width=8, project_name="phase_b_uart_rx_mutations"),
            platform,
        )
        mutations = oracle_mutation_projects(project, "uart_rx")

        self.assertIn("TEST_PASS", _run_generated_testbench(project))
        for mutation_name, mutation in mutations.items():
            with self.subTest(mutation=mutation_name):
                self.assertIsNotNone(mutation)
                assert mutation is not None
                self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                output = _run_generated_testbench(mutation)
                self.assertNotIn("TEST_PASS", output)
                self.assertIn("TEST_FAIL", output)

    def test_fir_catalog_mutation_suite_is_fully_implemented(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="fir_filter", width=8, project_name="fir_filter"),
            platform,
        )

        mutations = oracle_mutation_projects(project, "fir_filter")

        self.assertEqual(
            tuple(mutations),
            (
                "wrong_coeff_order",
                "truncate_accumulator",
                "remove_signed_cast",
                "missing_stall",
                "off_by_one_latency",
            ),
        )
        self.assertNotIn(None, mutations.values())

    def test_matrix_vector_mac_catalog_mutation_suite_is_fully_implemented(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="matrix_vector_mac", width=8, project_name="matrix_vector_mac"),
            platform,
        )

        mutations = oracle_mutation_projects(project, "matrix_vector_mac")

        self.assertEqual(
            tuple(mutations),
            ("wrong_index_order", "truncate_accumulator", "wrong_lane_reduction", "missing_stall"),
        )
        self.assertNotIn(None, mutations.values())

    def test_phase_b_signal_catalog_mutations_change_only_dut_rtl_and_are_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = (
            ("matched_filter", ("reversed_template", "truncate_correlation", "wrong_latency", "missing_stall")),
            ("peak_detector", ("wrong_threshold", "off_by_one_peak", "wrong_tie_break")),
            (
                "pulse_radar_signal",
                (
                    "reversed_template",
                    "wrong_threshold",
                    "off_by_one_peak",
                    "top_in_ready_stuck_high",
                    "history_updates_while_stalled",
                ),
            ),
        )

        for task_type, expected_mutations in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_{task_type}_mutations"),
                    platform,
                )
                mutations = oracle_mutation_projects(project, task_type)
                self.assertEqual(tuple(mutations), expected_mutations)
                self.assertIn("TEST_PASS", _run_generated_testbench(project))
                for mutation_name, mutation in mutations.items():
                    with self.subTest(task_type=task_type, mutation=mutation_name):
                        self.assertIsNotNone(mutation)
                        assert mutation is not None
                        changed_paths = {
                            path
                            for path, source in mutation.files.items()
                            if source != project.files[path]
                        }
                        self.assertTrue(changed_paths)
                        self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                        self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                        if mutation_name == "top_in_ready_stuck_high":
                            self.assertEqual(changed_paths, {"rtl/top.v"})
                            continue
                        if mutation_name == "history_updates_while_stalled":
                            self.assertEqual(changed_paths, {"rtl/matched_filter_core.v"})
                            continue
                        output = _run_generated_testbench(mutation)
                        self.assertNotIn("TEST_PASS", output)
                        self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_2a_matched_filter_mutations_are_dut_only_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="matched_filter", width=8, project_name="phase_b_2a_matched_filter"),
            platform,
        )
        mutations = oracle_mutation_projects(project, "matched_filter")

        self.assertEqual(
            tuple(mutations),
            ("reversed_template", "truncate_correlation", "wrong_latency", "missing_stall"),
        )
        self.assertIn("TEST_PASS", _run_generated_testbench(project))
        for mutation_name, mutation in mutations.items():
            with self.subTest(mutation=mutation_name):
                self.assertIsNotNone(mutation)
                assert mutation is not None
                changed_paths = {
                    path for path, source in mutation.files.items() if source != project.files[path]
                }
                self.assertTrue(changed_paths)
                self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                output = _run_generated_testbench(mutation)
                self.assertNotIn("TEST_PASS", output)
                self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_2b_peak_detector_mutations_are_dut_only_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="peak_detector", width=8, project_name="phase_b_2b_peak_detector"),
            platform,
        )
        mutations = oracle_mutation_projects(project, "peak_detector")

        self.assertEqual(
            tuple(mutations),
            ("wrong_threshold", "off_by_one_peak", "wrong_tie_break"),
        )
        self.assertIn("TEST_PASS", _run_generated_testbench(project))
        for mutation_name, mutation in mutations.items():
            with self.subTest(mutation=mutation_name):
                self.assertIsNotNone(mutation)
                assert mutation is not None
                changed_paths = {
                    path for path, source in mutation.files.items() if source != project.files[path]
                }
                self.assertTrue(changed_paths)
                self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                output = _run_generated_testbench(mutation)
                self.assertNotIn("TEST_PASS", output)
                self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_2c_pulse_radar_mutations_are_dut_only_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="pulse_radar_signal", width=8, project_name="phase_b_2c_pulse_radar"),
            platform,
        )
        mutations = oracle_mutation_projects(project, "pulse_radar_signal")

        self.assertEqual(
            tuple(mutations),
            (
                "reversed_template",
                "wrong_threshold",
                "off_by_one_peak",
                "top_in_ready_stuck_high",
                "history_updates_while_stalled",
            ),
        )
        self.assertIn("TEST_PASS", _run_generated_testbench(project))
        for mutation_name, mutation in mutations.items():
            with self.subTest(mutation=mutation_name):
                self.assertIsNotNone(mutation)
                assert mutation is not None
                changed_paths = {
                    path for path, source in mutation.files.items() if source != project.files[path]
                }
                self.assertTrue(changed_paths)
                self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                if mutation_name == "top_in_ready_stuck_high":
                    self.assertEqual(changed_paths, {"rtl/top.v"})
                    continue
                if mutation_name == "history_updates_while_stalled":
                    self.assertEqual(changed_paths, {"rtl/matched_filter_core.v"})
                    continue
                output = _run_generated_testbench(mutation)
                self.assertNotIn("TEST_PASS", output)
                self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_3a_sobel_mutations_are_dut_only_byte_identical_tb_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="sobel_threshold", width=8, project_name="phase_b_3a_sobel_mutations"),
            platform,
        )
        mutations = oracle_mutation_projects(project, "sobel_threshold")

        self.assertEqual(
            tuple(mutations),
            (
                "swap_x_y_gradient",
                "wrong_border_policy",
                "wrong_threshold",
                "accumulator_truncation",
                "input_backpressure_error",
                "ignore_in_last",
                "ignore_subsequent_reset",
            ),
        )
        self.assertIn("TEST_PASS", _run_generated_testbench(project))
        for mutation_name, mutation in mutations.items():
            with self.subTest(mutation=mutation_name):
                self.assertIsNotNone(mutation)
                assert mutation is not None
                changed_paths = {
                    path for path, source in mutation.files.items() if source != project.files[path]
                }
                self.assertTrue(changed_paths)
                self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                output = _run_generated_testbench(mutation)
                self.assertNotIn("TEST_PASS", output)
                self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_3b_vision_defect_mutations_are_dut_only_byte_identical_tb_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="vision_defect_core", width=8, project_name="phase_b_3b_vision_mutations"),
            platform,
        )
        mutations = oracle_mutation_projects(project, "vision_defect_core")

        self.assertEqual(
            tuple(mutations),
            (
                "wrong_line_order",
                "wrong_threshold",
                "missing_defect",
                "wrong_bbox",
                "hardcoded_first_coordinate",
                "input_backpressure_error",
                "ignore_in_last",
                "ignore_subsequent_reset",
            ),
        )
        self.assertIn("TEST_PASS", _run_generated_testbench(project))
        for mutation_name, mutation in mutations.items():
            with self.subTest(mutation=mutation_name):
                self.assertIsNotNone(mutation)
                assert mutation is not None
                changed_paths = {path for path, source in mutation.files.items() if source != project.files[path]}
                self.assertTrue(changed_paths)
                self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                if mutation_name in {"hardcoded_first_coordinate", "ignore_in_last"}:
                    # These reviewer mutants target the independent C3 operation-record scenarios.
                    continue
                output = _run_generated_testbench(mutation)
                self.assertNotIn("TEST_PASS", output)
                self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_phase_b_4_pattern_matcher_and_trigger_filter_mutations_are_dut_only_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        expected_mutations = {
            "pattern_matcher": ("wrong_pattern_order", "false_positive", "miss_overlap", "missing_stall"),
            "stream_trigger_filter": ("wrong_pattern_order", "false_trigger", "missing_backpressure", "drop_transaction"),
        }

        for task_type, mutation_names in expected_mutations.items():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_b_4_{task_type}_mutations"),
                    platform,
                )
                mutations = oracle_mutation_projects(project, task_type)
                self.assertEqual(tuple(mutations), mutation_names)
                self.assertIn("TEST_PASS", _run_generated_testbench(project))
                for mutation_name, mutation in mutations.items():
                    with self.subTest(task_type=task_type, mutation=mutation_name):
                        self.assertIsNotNone(mutation)
                        assert mutation is not None
                        changed_paths = {path for path, source in mutation.files.items() if source != project.files[path]}
                        self.assertTrue(changed_paths)
                        self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                        self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                        output = _run_generated_testbench(mutation)
                        self.assertNotIn("TEST_PASS", output)
                        self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(
        shutil.which("iverilog") and shutil.which("vvp") and shutil.which("verilator"),
        "iverilog, vvp, and verilator are not installed",
    )
    def test_phase_b_core_closure_reference_and_declared_mutations_are_scoreable(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = {
            "matched_filter": (),
            "uart_rx": ("wrong_sampling_point",),
            "uart_fifo_loopback": ("fifo_drop_byte",),
            "vision_defect_core": ("missing_defect",),
            "pattern_matcher": ("missing_stall",),
            "stream_trigger_filter": ("drop_transaction", "missing_backpressure"),
        }

        for task_type, mutation_names in cases.items():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"line_a_{task_type}"),
                    platform,
                )
                self.assertIn("TEST_PASS", _run_generated_testbench(project))
                mutations = oracle_mutation_projects(project, task_type)
                for mutation_name in mutation_names:
                    with self.subTest(task_type=task_type, mutation=mutation_name):
                        mutation = mutations[mutation_name]
                        self.assertIsNotNone(mutation)
                        assert mutation is not None
                        _run_verilator_lint(mutation)
                        output = _run_generated_testbench(mutation)
                        self.assertNotIn("TEST_PASS", output)
                        self.assertIn("TEST_FAIL", output)

    @unittest.skipUnless(
        shutil.which("verilator") and shutil.which("iverilog") and shutil.which("vvp"),
        "Verilator and iverilog/vvp are required",
    )
    def test_remaining_paper1_core_mutation_suites_are_dut_only_lint_clean_and_killed(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = {
            "ram_read_write": (
                "single_dual_port_ram",
                (
                    "async_read_in_sync_bram_family",
                    "wrong_read_during_write",
                    "wrong_address_width",
                ),
            ),
            "composed_stream_accumulator": (
                "valid_ready_stream_accumulator",
                (
                    "payload_changes_under_stall",
                    "valid_drops_under_stall",
                    "drop_transaction",
                    "wrong_accumulation",
                ),
            ),
            "composed_dual_stream_join": (
                "stream_fork_join",
                (
                    "drop_one_branch",
                    "duplicate_transaction",
                    "wrong_join_order",
                    "missing_backpressure",
                ),
            ),
            "composed_vector_mac_pipeline": (
                "mac_array",
                (
                    "remove_signed_cast",
                    "truncate_accumulator",
                    "wrong_latency",
                    "wrong_operand_order",
                ),
            ),
        }

        for task_type, (family_id, mutation_names) in cases.items():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"phase_c_{family_id}"),
                    platform,
                )
                self.assertIn("TEST_PASS", _run_generated_testbench(project))
                mutations = oracle_mutation_projects(project, task_type)
                self.assertEqual(tuple(mutations), mutation_names)
                if family_id == "valid_ready_stream_accumulator":
                    payload_mutant = mutations["payload_changes_under_stall"]
                    valid_mutant = mutations["valid_drops_under_stall"]
                    assert payload_mutant is not None
                    assert valid_mutant is not None
                    self.assertIn(
                        "else if (valid_r && !out_ready)",
                        payload_mutant.files["rtl/skid_buffer.v"],
                    )
                    self.assertIn(
                        "else if (valid_r && !out_ready)",
                        valid_mutant.files["rtl/skid_buffer.v"],
                    )
                for mutation_name, mutation in mutations.items():
                    with self.subTest(task_type=task_type, mutation=mutation_name):
                        self.assertIsNotNone(mutation)
                        assert mutation is not None
                        changed_paths = {
                            path for path, source in mutation.files.items() if source != project.files[path]
                        }
                        self.assertTrue(changed_paths)
                        self.assertTrue(all(path.startswith("rtl/") for path in changed_paths))
                        self.assertEqual(mutation.files["sim/tb_top.v"], project.files["sim/tb_top.v"])
                        _run_verilator_lint(mutation)
                        output = _run_generated_testbench(mutation)
                        self.assertIn("TEST_FAIL", output)
                        self.assertNotIn("TEST_PASS", output)

    def test_oracle_mutations_reject_conflicting_requested_family(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        ram = ProjectGenerator().generate(
            ProjectRequest(task_type="ram_read_write", width=8, project_name="ram"),
            platform,
        )

        self.assertEqual(oracle_mutation_projects(ram, "mac_array"), {})

    def test_oracle_mutations_reject_unknown_requested_family(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        ram = ProjectGenerator().generate(
            ProjectRequest(task_type="ram_read_write", width=8, project_name="ram"),
            platform,
        )

        self.assertEqual(oracle_mutation_projects(ram, "not_a_real_family"), {})

    def test_oracle_mutations_reject_unreadable_or_untyped_system_his(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        ram = ProjectGenerator().generate(
            ProjectRequest(task_type="ram_read_write", width=8, project_name="ram"),
            platform,
        )
        unreadable = GeneratedProject(
            project_name=ram.project_name,
            files={**ram.files, "system_his.json": "{"},
        )
        untyped_payload = json.loads(ram.files["system_his.json"])
        del untyped_payload["task_type"]
        untyped = GeneratedProject(
            project_name=ram.project_name,
            files={**ram.files, "system_his.json": json.dumps(untyped_payload)},
        )

        self.assertEqual(oracle_mutation_projects(unreadable, "ram_read_write"), {})
        self.assertEqual(oracle_mutation_projects(untyped, "ram_read_write"), {})


def _counter_project(width: int = 4) -> GeneratedProject:
    request = ProjectRequest(task_type="counter", width=width, project_name=f"counter_{width}bit")
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    return ProjectGenerator().generate(request, platform)


def _uart_tx_project() -> GeneratedProject:
    request = ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit")
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    return ProjectGenerator().generate(request, platform)


def _run_generated_testbench(project: GeneratedProject) -> str:
    return compile_and_run(project)


def _run_verilator_lint(project: GeneratedProject) -> None:
    lint_with_verilator(project)


class CountingGenerator:
    def __init__(self) -> None:
        self.call_count = 0
        self.base = ProjectGenerator()

    def generate(self, request, platform):
        self.call_count += 1
        return self.base.generate(request, platform)


if __name__ == "__main__":
    unittest.main()
