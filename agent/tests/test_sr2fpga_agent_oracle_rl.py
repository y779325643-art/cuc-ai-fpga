from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from sr2fpga_agent.failure_injector import oracle_mutation_projects
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.oracle_runner import run_oracle_scenarios
from sr2fpga_agent.oracles import REFERENCE_BUILDERS
from sr2fpga_agent.oracles.rl import (
    FIXED_SHIFT,
    RLConfig,
    argmax_first,
    build_qtable_update_bundle,
    build_rl_accelerator_bundle,
    rl_accelerator_step,
    saturate_signed,
    td_update,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.tool_runner import CommandRunner


SCENARIO_CLASSES = {
    "public_smoke",
    "hidden_deterministic",
    "randomized_fixed_seed",
    "stress",
}


def test_td_update_matches_declared_fixed_point_examples() -> None:
    assert FIXED_SHIFT == 4
    assert td_update(reward=4, value=10, next_value=20, gamma=8, alpha=4, width=8) == (4, 11)
    assert td_update(reward=2, value=6, next_value=16, gamma=8, alpha=8, width=8) == (4, 8)


def test_td_update_uses_signed_arithmetic_shift_and_width_saturation() -> None:
    assert td_update(reward=-8, value=4, next_value=-3, gamma=8, alpha=8, width=8) == (-14, -3)
    assert td_update(reward=127, value=-128, next_value=127, gamma=16, alpha=16, width=8) == (127, -1)
    assert td_update(reward=-128, value=127, next_value=-128, gamma=16, alpha=16, width=8) == (-128, -1)
    assert saturate_signed(200, 8) == 127
    assert saturate_signed(-200, 8) == -128


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reward": 128, "value": 0, "next_value": 0, "gamma": 0, "alpha": 0, "width": 8},
        {"reward": 0, "value": 0, "next_value": 0, "gamma": -1, "alpha": 0, "width": 8},
        {"reward": 0, "value": 0, "next_value": 0, "gamma": 0, "alpha": 256, "width": 8},
        {"reward": 0, "value": 0, "next_value": 0, "gamma": 0, "alpha": 0, "width": 1},
    ],
)
def test_td_update_rejects_values_outside_declared_width(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        td_update(**kwargs)


def test_argmax_tie_chooses_first_action() -> None:
    assert argmax_first((9, 9)) == 0
    assert argmax_first((3, 7)) == 1
    with pytest.raises(ValueError):
        argmax_first(())


def test_rl_shell_examples_and_unsigned_width_limits() -> None:
    config = RLConfig(weight0=2, bias0=1, weight1=3, bias1=0, alpha=4, enable=True)
    assert rl_accelerator_step(
        config,
        obs0=4,
        obs1=2,
        reward=1,
        next_value=8,
        done=False,
        width=8,
    ) == (0, 7, 7, False, False)
    assert rl_accelerator_step(
        config,
        obs0=1,
        obs1=5,
        reward=2,
        next_value=15,
        done=True,
        width=8,
    ) == (1, 9, 11, True, True)

    saturated = RLConfig(weight0=255, bias0=255, weight1=255, bias1=255, alpha=255, enable=True)
    assert rl_accelerator_step(
        saturated,
        obs0=255,
        obs1=255,
        reward=255,
        next_value=255,
        done=False,
        width=8,
    ) == (0, 255, 254, False, False)


def test_rl_config_register_map_is_fixed_zero_through_five() -> None:
    config = RLConfig()
    values = (2, 1, 3, 0, 4, 1)
    for address, value in enumerate(values):
        config = config.write(address, value, width=8)
    assert config == RLConfig(weight0=2, bias0=1, weight1=3, bias1=0, alpha=4, enable=True)
    assert config.write(5, 0, width=8).enable is False
    with pytest.raises(ValueError):
        config.write(6, 1, width=8)


@pytest.mark.parametrize(
    ("family_id", "builder", "input_width", "expected_width"),
    [
        ("qtable_update_core", build_qtable_update_bundle, 43, 16),
        ("p_rl_qlearning_accel", build_rl_accelerator_bundle, 48, 20),
    ],
)
def test_rl_bundle_has_four_nonempty_classes_and_exact_record_widths(
    tmp_path: Path,
    family_id: str,
    builder,
    input_width: int,
    expected_width: int,
) -> None:
    bundle = builder(8, tmp_path / family_id)

    assert bundle.family_id == family_id
    assert bundle.reference_model == "python_rl_reference"
    assert {scenario.scenario_class for scenario in bundle.scenarios} == SCENARIO_CLASSES
    assert len(bundle.scenarios) == 4
    assert REFERENCE_BUILDERS[family_id] is builder
    for scenario in bundle.scenarios:
        assert scenario.transaction_count > 0
        assert scenario.input_record_width_bits == input_width
        assert scenario.expected_record_width_bits == expected_width
        assert len(_read_memh(bundle.root / scenario.input_path)) == scenario.transaction_count
        assert len(_read_memh(bundle.root / scenario.expected_path)) == scenario.transaction_count


def test_td_bundle_layout_reset_stall_and_signed_expected_records(tmp_path: Path) -> None:
    bundle = build_qtable_update_bundle(8, tmp_path / "td")
    scenario = next(item for item in bundle.scenarios if item.scenario_class == "stress")
    inputs = _read_memh(bundle.root / scenario.input_path)
    expected = _read_memh(bundle.root / scenario.expected_path)

    assert [(field.name, field.msb, field.lsb, field.signed) for field in scenario.input_fields] == [
        ("reward", 7, 0, True),
        ("value", 15, 8, True),
        ("next_value", 23, 16, True),
        ("gamma", 31, 24, False),
        ("alpha", 39, 32, False),
        ("reset_before", 40, 40, False),
        ("stall_cycles", 42, 41, False),
    ]
    assert [(field.name, field.msb, field.lsb, field.signed) for field in scenario.expected_fields] == [
        ("td_error", 7, 0, True),
        ("updated_value", 15, 8, True),
    ]
    assert any((record >> 40) & 1 for record in inputs)
    assert any((record >> 41) & 0b11 for record in inputs)
    assert any(_signed(record & 0xFF, 8) < 0 for record in expected)
    assert scenario.seed.bit_length() >= 120


def test_rl_accelerator_bundle_encodes_reset_config_sample_done_irq_and_stall(tmp_path: Path) -> None:
    bundle = build_rl_accelerator_bundle(8, tmp_path / "shell")
    stress = next(item for item in bundle.scenarios if item.scenario_class == "stress")
    inputs = _read_memh(bundle.root / stress.input_path)
    expected = _read_memh(bundle.root / stress.expected_path)

    assert [(field.name, field.msb, field.lsb, field.signed) for field in stress.input_fields] == [
        ("operation", 1, 0, False),
        ("cfg_addr", 4, 2, False),
        ("cfg_data", 12, 5, False),
        ("obs0", 20, 13, False),
        ("obs1", 28, 21, False),
        ("reward", 36, 29, False),
        ("next_value", 44, 37, False),
        ("done", 45, 45, False),
        ("stall_cycles", 47, 46, False),
    ]
    assert [(field.name, field.msb, field.lsb, field.signed) for field in stress.expected_fields] == [
        ("expect_output", 0, 0, False),
        ("selected_action", 1, 1, False),
        ("value_estimate", 9, 2, False),
        ("updated_value", 17, 10, False),
        ("episode_done", 18, 18, False),
        ("irq", 19, 19, False),
    ]
    assert {record & 0b11 for record in inputs} == {0, 1, 2}
    cfg_addresses = {(record >> 2) & 0b111 for record in inputs if (record & 0b11) == 1}
    assert cfg_addresses == set(range(6))
    assert any(((record >> 45) & 1) for record in inputs if (record & 0b11) == 2)
    assert any(((record >> 46) & 0b11) for record in inputs)
    assert any((record >> 18) & 1 for record in expected)
    assert any((record >> 19) & 1 for record in expected)
    assert stress.seed.bit_length() >= 120


@pytest.mark.parametrize(
    ("builder", "family_id"),
    [
        (build_qtable_update_bundle, "qtable_update_core"),
        (build_rl_accelerator_bundle, "p_rl_qlearning_accel"),
    ],
)
def test_rl_bundles_are_deterministic(builder, family_id: str, tmp_path: Path) -> None:
    first = builder(8, tmp_path / "first")
    second = builder(8, tmp_path / "second")
    assert first.bundle_sha256 == second.bundle_sha256
    assert first.manifest == second.manifest
    assert first.family_id == family_id


def test_generated_rl_testbenches_keep_legacy_and_add_oracle_mode() -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    for task_type in ("composed_td_update_core", "composed_rl_accelerator_shell"):
        project = ProjectGenerator().generate(
            ProjectRequest(task_type=task_type, width=8, project_name=task_type),
            platform,
        )
        testbench = project.files["sim/tb_top.v"]
        assert '$value$plusargs("ORACLE_INPUT=%s"' in testbench
        assert "$readmemh(oracle_input_path" in testbench
        assert "ORACLE_EXPECTED" in testbench
        assert "ORACLE_TRANSACTION_COUNT" in testbench
        assert "SR2FPGA_MISMATCH" in testbench
        assert "output changed under stall" in testbench
        assert '$display("TEST_PASS")' in testbench


def test_missing_saturation_mutation_bypasses_overflow_clamp() -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(task_type="composed_td_update_core", width=8, project_name="qtable_update_core"),
        platform,
    )

    mutation = oracle_mutation_projects(reference, "qtable_update_core")["missing_saturation"]

    assert mutation is not None
    assert (
        "assign updated_value =\n"
        "    updated_value_full[DATA_WIDTH] ?\n"
        "      updated_value_full[DATA_WIDTH-1:0] :\n"
        "      updated_value_full[DATA_WIDTH-1:0];"
    ) in mutation.files[
        "rtl/td_update_core.v"
    ]


def test_rl_catalog_coverage_matches_declared_core_and_host_stream_contracts() -> None:
    catalog_path = Path(__file__).resolve().parents[2] / "docs" / "sr2fpga-task-catalog-v0.2.json"
    families = {
        family["family_id"]: family
        for family in json.loads(catalog_path.read_text(encoding="utf-8"))["task_families"]
    }

    assert families["qtable_update_core"]["coverage_targets"] == [
        "reset_sequence",
        "boundary_values",
        "timeout",
        "random_stalls",
        "back_to_back_transactions",
        "reset_during_transaction",
        "signed_unsigned_cases",
        "overflow_truncation_cases",
        "latency_alignment",
        "max_reward",
    ]
    assert families["p_rl_qlearning_accel"]["coverage_targets"] == [
        "reset_sequence",
        "boundary_values",
        "timeout",
        "random_stalls",
        "back_to_back_transactions",
        "reset_during_transaction",
        "register_map_access",
        "sample_valid",
        "episode_done",
        "irq",
        "host_signature",
        "terminal_state",
        "equal_q_values",
        "back_to_back_commands",
    ]


@pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp"),
    reason="iverilog/vvp are not installed",
)
@pytest.mark.parametrize(
    ("task_type", "family_id", "builder", "expected_mutations"),
    [
        (
            "composed_td_update_core",
            "qtable_update_core",
            build_qtable_update_bundle,
            (
                "wrong_td_formula",
                "accumulator_truncation",
                "wrong_signed_shift",
                "missing_saturation",
            ),
        ),
        (
            "composed_rl_accelerator_shell",
            "p_rl_qlearning_accel",
            build_rl_accelerator_bundle,
            (
                "wrong_td_formula",
                "wrong_argmax_tie_break",
                "accumulator_truncation",
                "missing_done",
                "wrong_register_offset",
            ),
        ),
    ],
)
def test_rl_reference_and_all_declared_mutations_are_scoreable(
    tmp_path: Path,
    task_type: str,
    family_id: str,
    builder,
    expected_mutations: tuple[str, ...],
) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(task_type=task_type, width=8, project_name=task_type),
        platform,
    )
    bundle = builder(8, tmp_path / "oracle" / family_id)

    reference_compile, reference_evidence = _compile_and_run(
        reference,
        tmp_path / "reference" / family_id,
        bundle,
    )
    assert reference_compile == "passed"
    assert reference_evidence == "passed"

    mutations = oracle_mutation_projects(reference, family_id)
    assert tuple(mutations) == expected_mutations
    for mutation_name, mutation in mutations.items():
        assert mutation is not None, mutation_name
        assert _lint_project(
            mutation,
            tmp_path / "lint" / family_id / mutation_name,
        ) == "passed", mutation_name
        compile_status, evidence_status = _compile_and_run(
            mutation,
            tmp_path / "mutations" / family_id / mutation_name,
            bundle,
        )
        assert compile_status == "passed", mutation_name
        assert evidence_status == "failed", mutation_name


def _read_memh(path: Path) -> list[int]:
    return [int(line, 16) for line in path.read_text(encoding="ascii").splitlines()]


def _signed(value: int, width: int) -> int:
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def _compile_and_run(
    project: GeneratedProject,
    project_dir: Path,
    bundle,
) -> tuple[str, str]:
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, source in project.files.items():
        destination = project_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")
    manifest = json.loads(project.files["manifest.json"])
    runner = CommandRunner()
    compile_result = runner.run(
        [
            "iverilog",
            "-g2012",
            "-o",
            "sim.out",
            *manifest["sources"],
            manifest["simulation"]["testbench"],
        ],
        cwd=project_dir,
        stage="sim_compile",
    )
    if compile_result.status != "passed":
        return compile_result.status, "not_run"
    evidence, _ = run_oracle_scenarios(runner, project_dir, bundle)
    return compile_result.status, evidence.status


def _lint_project(project: GeneratedProject, project_dir: Path) -> str:
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, source in project.files.items():
        destination = project_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")
    manifest = json.loads(project.files["manifest.json"])
    result = CommandRunner().run(
        ["verilator", "--lint-only", "-Wall", *manifest["sources"]],
        cwd=project_dir,
        stage="lint",
    )
    return result.status
