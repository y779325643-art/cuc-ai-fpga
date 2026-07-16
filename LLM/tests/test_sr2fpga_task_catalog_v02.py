import json
import unittest
from pathlib import Path

import pytest

from LLM.src.sr2fpga_agent import task_catalog
from LLM.src.sr2fpga_agent.task_families import TASK_FAMILY_IDS
from LLM.src.sr2fpga_agent.task_catalog import (
    TaskFamilySpec,
    load_task_family_specs,
    task_family_spec_for_alias,
)


CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "sr2fpga-task-catalog-v0.2.json"
)
EXPECTED_FAMILY_IDS = {
    "async_fifo_cdc",
    "baud_generator",
    "binary_bcd_counter",
    "button_debounce",
    "clock_divider",
    "collision_detector",
    "conv2d_core",
    "cpu_axi_soc_shell",
    "fft_ifft_simplified",
    "fir_filter",
    "font_text_renderer",
    "ga_fitness_eval",
    "ga_select_cross_mutate",
    "hdmi_tmds_basic",
    "i2c_master",
    "image_scale_norm",
    "line_frame_buffer",
    "mac_array",
    "matched_filter",
    "matrix_vector_mac",
    "memory_interrupt_controller",
    "p_fifo_ram_app",
    "p_fir_filter",
    "p_ga_accelerator",
    "p_led_breath_button",
    "p_ofdm_modem_subset",
    "p_pong_game",
    "p_pulse_radar_signal",
    "p_riscv_soc_shell",
    "p_rl_qlearning_accel",
    "p_sd_spi_controller",
    "p_sensor_fusion_obstacle",
    "p_seven_seg_stopwatch",
    "p_simple_cnn_pipeline",
    "p_stream_trigger_filter",
    "p_traffic_light",
    "p_uart_transceiver",
    "p_vga_simple_graphics",
    "p_vision_defect_core",
    "pattern_matcher",
    "peak_detector",
    "pixel_generator_basic",
    "pooling_activation",
    "population_eval_parallel",
    "pwm_generator",
    "qam_mapping_equalizer",
    "qtable_update_core",
    "rl_reward_policy_update",
    "sensor_fusion_arbiter",
    "seven_seg_scan",
    "simple_fsm",
    "single_dual_port_ram",
    "small_nn_accelerator",
    "sobel_threshold",
    "soc_top_wrapper",
    "spi_master",
    "sprite_object_mapper",
    "stream_fork_join",
    "sync_fifo",
    "uart_fifo_loopback",
    "uart_rx",
    "uart_tx",
    "valid_ready_stream_accumulator",
    "valid_ready_stream_stage",
    "vga_timing",
    "alu_control_unit",
    "crc_stream_checker",
    "t1_event_counter",
    "t8_replay_sample_shell",
    "t9_host_protocol_shell",
    "t12_replay_arbiter_shell",
}

CURRENT_DETERMINISTIC_ALIASES = {
    "counter": ("binary_bcd_counter", "T0"),
    "simple_fsm": ("simple_fsm", "T0"),
    "ram_read_write": ("single_dual_port_ram", "T0"),
    "fifo": ("sync_fifo", "T0"),
    "uart_tx": ("uart_tx", "T0"),
    "uart_rx": ("uart_rx", "T1"),
    "uart_fifo_loopback": ("uart_fifo_loopback", "T1"),
    "spi_master": ("spi_master", "T1"),
    "pwm_controller": ("pwm_generator", "T0"),
    "fir_filter": ("fir_filter", "T3"),
    "matched_filter": ("matched_filter", "T3"),
    "peak_detector": ("peak_detector", "T3"),
    "pulse_radar_signal": ("p_pulse_radar_signal", "T3"),
    "sobel_threshold": ("sobel_threshold", "T3"),
    "vision_defect_core": ("p_vision_defect_core", "T3"),
    "pattern_matcher": ("pattern_matcher", "T2"),
    "stream_trigger_filter": ("p_stream_trigger_filter", "T3"),
    "streaming_valid_ready": ("valid_ready_stream_stage", "T2"),
    "matrix_vector_mac": ("matrix_vector_mac", "T3"),
    "alu_control_unit": ("alu_control_unit", "T1"),
    "crc_stream_checker": ("crc_stream_checker", "T2"),
    "t1_event_counter": ("t1_event_counter", "T1"),
    "t2_stream_accumulator": ("valid_ready_stream_accumulator", "T2"),
    "t3_stream_fork": ("stream_fork_join", "T2"),
    "t4_dual_stream_join": ("stream_fork_join", "T2"),
    "t5_vector_mac_pipeline": ("mac_array", "T3"),
    "t6_td_update_core": ("qtable_update_core", "T3"),
    "t7_policy_value_shell": ("rl_reward_policy_update", "T4"),
    "t8_replay_sample_shell": ("t8_replay_sample_shell", "T3"),
    "t9_host_protocol_shell": ("t9_host_protocol_shell", "T4"),
    "t10_rl_accelerator_shell": ("p_rl_qlearning_accel", "T4"),
    "t11_batch_rl_accelerator_shell": ("p_rl_qlearning_accel", "T4"),
    "t12_replay_arbiter_shell": ("t12_replay_arbiter_shell", "T4"),
}

OMITTED_CURRENT_FAMILY_IDS = {
    "alu_control_unit",
    "crc_stream_checker",
    "t1_event_counter",
    "t8_replay_sample_shell",
    "t9_host_protocol_shell",
    "t12_replay_arbiter_shell",
}


def _load_catalog():
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_task_catalog_v02_has_stable_family_metadata_and_l4_policy():
    catalog = _load_catalog()
    families = catalog["task_families"]
    allowed_enums = catalog["allowed_enums"]
    module_difficulties = {"M1", "M2", "M3", "M4", "M5"}
    project_difficulties = {"P1", "P2", "P3", "P4", "P5"}
    sr2fpga_tiers = {"T0", "T1", "T2", "T3", "T4"}
    official_l_levels = {"L3", "L4", "L5"}
    required_fields = {
        "family_id",
        "task_kind",
        "category",
        "module_difficulty",
        "project_difficulty",
        "sr2fpga_tier",
        "system_his_profile",
        "skeleton_level",
        "oracle_kind",
        "target_l_level",
        "mutation_suite",
        "mutation_score_threshold",
        "benchmark_role",
    }

    family_ids = [family.get("family_id") for family in families]
    assert family_ids
    assert all(isinstance(family_id, str) and family_id.strip() == family_id for family_id in family_ids)
    assert set(family_ids) == EXPECTED_FAMILY_IDS
    assert len(family_ids) == len(set(family_ids))

    for family in families:
        task_kind = family["task_kind"]
        assert required_fields <= family.keys(), family.get("family_id")
        assert task_kind in allowed_enums["task_kind"], family["family_id"]
        assert family["category"] in allowed_enums["category"], family["family_id"]
        assert family["sr2fpga_tier"] in sr2fpga_tiers, family["family_id"]
        assert family["system_his_profile"] in allowed_enums["system_his_profile"], family["family_id"]
        assert family["skeleton_level"] in allowed_enums["skeleton_level"], family["family_id"]
        assert family["benchmark_role"] in allowed_enums["benchmark_role"], family["family_id"]
        if task_kind == "module_family":
            assert family["module_difficulty"] in module_difficulties, family["family_id"]
            assert family["project_difficulty"] is None, family["family_id"]
        elif task_kind == "project_family":
            assert family["module_difficulty"] is None, family["family_id"]
            assert family["project_difficulty"] in project_difficulties, family["family_id"]
        assert isinstance(family["target_l_level"], dict)
        target_l_level = family["target_l_level"]
        assert target_l_level.get("official") in official_l_levels, family["family_id"]
        assert target_l_level.get("l4_open_policy") in allowed_enums["l4_open_policy"], family["family_id"]
        assert target_l_level.get("l4_commercial_policy") in allowed_enums["l4_commercial_policy"], family["family_id"]
        assert target_l_level.get("l5_policy") in allowed_enums["l5_policy"], family["family_id"]
        assert isinstance(family["oracle_kind"], list) and family["oracle_kind"], family["family_id"]
        assert set(family["oracle_kind"]) <= set(allowed_enums["oracle_kind"]), family["family_id"]
        assert isinstance(family["mutation_suite"], list) and family["mutation_suite"], family["family_id"]
        assert isinstance(family["mutation_score_threshold"], (int, float)), family["family_id"]
        assert 0.0 <= family["mutation_score_threshold"] <= 1.0, family["family_id"]
        assert all(
            isinstance(mutation, str) and mutation.strip() == mutation and mutation
            for mutation in family["mutation_suite"]
        ), family["family_id"]


def test_task_catalog_v02_current_generator_aliases_have_unique_owners():
    families = _load_catalog()["task_families"]
    alias_owners = {}

    for family in families:
        aliases = family.get("current_generator_aliases", [])
        assert isinstance(aliases, list), family["family_id"]
        assert len(aliases) == len(set(aliases)), family["family_id"]
        for alias in aliases:
            assert isinstance(alias, str) and alias.strip() == alias and alias
            assert alias not in alias_owners, (alias, alias_owners.get(alias), family["family_id"])
            alias_owners[alias] = family["family_id"]


def test_current_task_family_registry_uses_catalog_family_ids_where_implemented():
    expected_catalog_families = {
        "counter": "binary_bcd_counter",
        "simple_fsm": "simple_fsm",
        "ram_read_write": "single_dual_port_ram",
        "pwm_controller": "pwm_generator",
        "fir_filter": "fir_filter",
        "matrix_vector_mac": "matrix_vector_mac",
        "fifo": "sync_fifo",
        "uart_tx": "uart_tx",
        "uart_rx": "uart_rx",
        "uart_fifo_loopback": "uart_fifo_loopback",
        "spi_master": "spi_master",
        "streaming_valid_ready": "valid_ready_stream_stage",
        "composed_stream_accumulator": "valid_ready_stream_accumulator",
        "composed_stream_fork": "stream_fork_join",
        "composed_dual_stream_join": "stream_fork_join",
        "composed_vector_mac_pipeline": "mac_array",
        "composed_td_update_core": "qtable_update_core",
        "composed_policy_value_shell": "rl_reward_policy_update",
        "composed_rl_accelerator_shell": "p_rl_qlearning_accel",
        "composed_batch_rl_accelerator_shell": "p_rl_qlearning_accel",
    }

    for task_type, family_id in expected_catalog_families.items():
        assert TASK_FAMILY_IDS[task_type] == family_id


def test_task_catalog_runtime_resolves_all_current_deterministic_aliases_and_tiers():
    specs = load_task_family_specs()

    assert isinstance(specs, tuple)
    assert all(isinstance(spec, TaskFamilySpec) for spec in specs)

    aliases = {
        alias
        for spec in specs
        for alias in spec.current_generator_aliases
    }
    assert aliases == set(CURRENT_DETERMINISTIC_ALIASES)

    for alias, (family_id, sr2fpga_tier) in CURRENT_DETERMINISTIC_ALIASES.items():
        spec = task_family_spec_for_alias(alias)
        assert spec.family_id == family_id
        assert spec.sr2fpga_tier == sr2fpga_tier


def test_task_catalog_runtime_exposes_l4_open_target_policy():
    assert task_family_spec_for_alias("counter").l4_open_policy == "none"
    assert task_family_spec_for_alias("fir_filter").l4_open_policy == "representative_subset"
    assert task_family_spec_for_alias("t10_rl_accelerator_shell").l4_open_policy == "required_for_flagship"


def test_task_catalog_runtime_exposes_l4_commercial_target_policy():
    assert task_family_spec_for_alias("counter").l4_commercial_policy == "none"
    assert task_family_spec_for_alias("fir_filter").l4_commercial_policy == "tcad_subset"
    assert task_family_spec_for_alias("matrix_vector_mac").l4_commercial_policy == "tcad_subset"


def test_task_catalog_runtime_exposes_generation_and_oracle_contract():
    spec = task_family_spec_for_alias("fir_filter")

    assert spec.system_his_profile == "streaming_datapath"
    assert spec.skeleton_level == "S2_protocol_skeleton"
    assert spec.oracle_kind == ("python_numpy_golden", "transaction_scoreboard")
    assert spec.mutation_suite == (
        "wrong_coeff_order",
        "truncate_accumulator",
        "remove_signed_cast",
        "missing_stall",
        "off_by_one_latency",
    )
    assert spec.mutation_score_threshold == 0.85
    assert spec.benchmark_role == "paper1_core"


def test_task_catalog_runtime_represents_each_previously_omitted_current_family():
    family_ids = {spec.family_id for spec in load_task_family_specs()}

    assert OMITTED_CURRENT_FAMILY_IDS <= family_ids


def test_task_catalog_runtime_rejects_duplicate_aliases(tmp_path, monkeypatch):
    catalog = _load_catalog()
    duplicate = json.loads(json.dumps(catalog))
    duplicate["task_families"][0]["current_generator_aliases"] = ["counter"]
    duplicate["task_families"][1]["current_generator_aliases"] = ["counter"]
    catalog_path = tmp_path / "duplicate-aliases.json"
    catalog_path.write_text(json.dumps(duplicate), encoding="utf-8")
    monkeypatch.setattr(task_catalog, "CATALOG_PATH", catalog_path)

    with pytest.raises(ValueError, match="duplicate task catalog alias: counter"):
        load_task_family_specs()


def test_task_catalog_runtime_rejects_unknown_alias_clearly():
    with pytest.raises(KeyError, match="unknown task catalog alias: not_a_task"):
        task_family_spec_for_alias("not_a_task")


class PhaseBUartCatalogTest(unittest.TestCase):
    def test_phase_b_uart_families_have_exact_current_generator_ownership(self) -> None:
        expected = {
            "uart_rx": ("uart_rx", "implemented_current"),
            "uart_fifo_loopback": ("uart_fifo_loopback", "implemented_current"),
        }
        families = {family["family_id"]: family for family in _load_catalog()["task_families"]}

        for family_id, (task_type, implementation_status) in expected.items():
            with self.subTest(family_id=family_id):
                family = families[family_id]
                self.assertEqual(family["current_generator_aliases"], [task_type])
                self.assertEqual(family["implementation_status"], implementation_status)


class PhaseBSignalCatalogTest(unittest.TestCase):
    def test_phase_b_signal_families_have_exact_current_generator_ownership(self) -> None:
        expected = {
            "matched_filter": "matched_filter",
            "peak_detector": "peak_detector",
            "p_pulse_radar_signal": "pulse_radar_signal",
        }
        families = {family["family_id"]: family for family in _load_catalog()["task_families"]}

        for family_id, task_type in expected.items():
            with self.subTest(family_id=family_id):
                family = families[family_id]
                self.assertEqual(family["current_generator_aliases"], [task_type])
                self.assertEqual(family["implementation_status"], "implemented_current")


class PhaseBMatchedFilterCatalogTest(unittest.TestCase):
    def test_phase_b_2a_matched_filter_has_current_generator_ownership(self) -> None:
        families = {family["family_id"]: family for family in _load_catalog()["task_families"]}
        family = families["matched_filter"]

        self.assertEqual(family["current_generator_aliases"], ["matched_filter"])
        self.assertEqual(family["implementation_status"], "implemented_current")


class PhaseBPeakDetectorCatalogTest(unittest.TestCase):
    def test_phase_b_2b_peak_detector_has_current_generator_ownership(self) -> None:
        families = {family["family_id"]: family for family in _load_catalog()["task_families"]}
        family = families["peak_detector"]

        self.assertEqual(family["current_generator_aliases"], ["peak_detector"])
        self.assertEqual(family["implementation_status"], "implemented_current")
        self.assertEqual(family["core_modules"], ["peak_detector_core"])


class PhaseBPulseRadarCatalogTest(unittest.TestCase):
    def test_phase_b_2c_pulse_radar_has_current_generator_ownership(self) -> None:
        families = {family["family_id"]: family for family in _load_catalog()["task_families"]}
        family = families["p_pulse_radar_signal"]

        self.assertEqual(family["implementation_status"], "implemented_current")
        self.assertEqual(family["current_generator_aliases"], ["pulse_radar_signal"])
        self.assertEqual(
            family["core_modules"],
            ["matched_filter_core", "matched_filter_mac", "threshold_comparator", "peak_detector_core"],
        )


class PhaseBSobelCatalogTest(unittest.TestCase):
    def test_phase_b_3a_sobel_has_exact_current_generator_ownership_and_axis_contract(self) -> None:
        family = {family["family_id"]: family for family in _load_catalog()["task_families"]}["sobel_threshold"]

        self.assertEqual(family["implementation_status"], "implemented_current")
        self.assertEqual(family["current_generator_aliases"], ["sobel_threshold"])
        self.assertEqual(
            family["core_modules"],
            ["sobel_line_buffer", "sobel_window", "sobel_threshold_core", "io_control"],
        )
        self.assertIn("edge_axis_semantics", family["architecture_obligations"])
        self.assertIn("axis_sensitive_edges", family["coverage_targets"])
        self.assertEqual(
            family["mutation_suite"],
            [
                "swap_x_y_gradient",
                "wrong_border_policy",
                "wrong_threshold",
                "accumulator_truncation",
                "input_backpressure_error",
                "ignore_in_last",
                "ignore_subsequent_reset",
            ],
        )


class PhaseBVisionDefectCatalogTest(unittest.TestCase):
    def test_phase_b_3b_vision_defect_has_bounded_current_generator_ownership(self) -> None:
        family = {family["family_id"]: family for family in _load_catalog()["task_families"]}["p_vision_defect_core"]

        self.assertEqual(family["implementation_status"], "implemented_current")
        self.assertEqual(family["current_generator_aliases"], ["vision_defect_core"])
        self.assertEqual(
            family["core_modules"],
            ["sobel_line_buffer", "sobel_window", "sobel_threshold_core", "vision_defect_accumulator", "vision_io_control"],
        )
        self.assertIn("first_defect_coordinate", family["architecture_obligations"])
        self.assertNotIn("bounding_box_optional", family["architecture_obligations"])
        self.assertEqual(
            family["mutation_suite"],
            [
                "wrong_line_order",
                "wrong_threshold",
                "missing_defect",
                "wrong_bbox",
                "hardcoded_first_coordinate",
                "input_backpressure_error",
                "ignore_in_last",
                "ignore_subsequent_reset",
            ],
        )


class PhaseBPatternTriggerCatalogTest(unittest.TestCase):
    def test_phase_b_4_pattern_and_trigger_have_current_generator_ownership(self) -> None:
        families = {family["family_id"]: family for family in _load_catalog()["task_families"]}

        matcher = families["pattern_matcher"]
        self.assertEqual(matcher["implementation_status"], "implemented_current")
        self.assertEqual(matcher["current_generator_aliases"], ["pattern_matcher"])
        self.assertEqual(matcher["core_modules"], ["pattern_matcher"])
        self.assertIn("accepted_token_match_index", matcher["architecture_obligations"])
        self.assertEqual(matcher["mutation_suite"], ["wrong_pattern_order", "false_positive", "miss_overlap", "missing_stall"])

        trigger = families["p_stream_trigger_filter"]
        self.assertEqual(trigger["implementation_status"], "implemented_current")
        self.assertEqual(trigger["current_generator_aliases"], ["stream_trigger_filter"])
        self.assertEqual(trigger["core_modules"], ["pattern_matcher", "trigger_fsm", "stream_packer"])
        self.assertIn("match_index_packet", trigger["architecture_obligations"])
        self.assertEqual(trigger["mutation_suite"], ["wrong_pattern_order", "false_trigger", "missing_backpressure", "drop_transaction"])
