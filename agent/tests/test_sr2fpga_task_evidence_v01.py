import json
import shutil
import unittest
from dataclasses import replace
from pathlib import Path

import pytest

from sr2fpga_agent import task_evidence
from sr2fpga_agent.task_evidence import (
    EVIDENCE_PATH,
    IndependentOracleEvidence,
    MutationEvidence,
    TaskFamilyEvidence,
    audit_local_run_artifacts,
    load_task_family_evidence,
    main,
    render_task_evidence_markdown,
)
from sr2fpga_agent.task_families import TASK_FAMILY_IDS
from sr2fpga_agent.oracle_runner import write_oracle_run_evidence
from sr2fpga_agent.oracles.bundle import sanitize_oracle_profile, write_oracle_bundle
from sr2fpga_agent.oracles.types import (
    OracleField,
    OracleRunEvidence,
    OracleScenarioResult,
    OracleScenarioSpec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_catalog(tmp_path, family_ids, aliases=()):
    catalog = {
        "task_families": [
            {
                "family_id": family_id,
                "current_generator_aliases": list(aliases if family_id == family_ids[0] else ()),
            }
            for family_id in family_ids
        ]
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    return path


def _entry(family_id, **overrides):
    entry = {
        "family_id": family_id,
        "generator_status": "not_implemented",
        "testbench_status": "not_implemented",
        "golden_model_status": "none",
        "mutation_evidence": {
            "status": "not_run",
            "score": None,
            "run_id": "",
        },
        "highest_verified_level": "not_run",
        "l4_open_status": "not_run",
        "l4_commercial_status": "not_run",
        "l5_status": "not_run",
        "last_verified_run": "",
        "evidence_refs": [],
    }
    entry.update(overrides)
    return entry


def _write_evidence(tmp_path, entries, **overrides):
    document = {
        "schema_version": "sr2fpga-task-evidence-v0.1",
        "source_catalog": "docs/sr2fpga-task-catalog-v0.2.json",
        "task_families": entries,
    }
    document.update(overrides)
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _qualified_audit_fixture(
    tmp_path,
    *,
    trajectory_family="family",
    summary_sample_id=None,
    summary_bucket="success_l3",
    pass_level="L3",
    highest_official_level="L3",
):
    run_id = "line-a-qualified"
    sample_id = "sample_line_a_family"
    run_root = tmp_path / "runs"
    summary = run_root / run_id / "summary.json"
    summary.parent.mkdir(parents=True)
    summary.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "buckets": {
                    "success_l3": [summary_sample_id or sample_id] if summary_bucket == "success_l3" else [],
                    "repair_trajectory": [summary_sample_id or sample_id] if summary_bucket == "repair_trajectory" else [],
                    "rejected": [summary_sample_id or sample_id] if summary_bucket == "rejected" else [],
                },
            }
        ),
        encoding="utf-8",
    )
    sample_dir = tmp_path / "dataset" / sample_id
    trajectory = sample_dir / "eval" / "trajectory.json"
    mutations = sample_dir / "oracle_mutations"
    trajectory.parent.mkdir(parents=True)
    for name in ("wrong_data", "missing_stall"):
        mutation_eval = mutations / name / "eval"
        mutation_eval.mkdir(parents=True)
        (mutation_eval / "sim_compile.json").write_text(
            json.dumps({"stage": "sim_compile", "status": "passed", "exit_code": 0}),
            encoding="utf-8",
        )
        (mutation_eval / "sim_run.json").write_text(
            json.dumps(
                {
                    "stage": "sim_run",
                    "status": "failed",
                    "exit_code": 0,
                    "stdout": "TEST_FAIL injected mutation detected",
                    "stderr": "Simulation reported TEST_FAIL",
                }
            ),
            encoding="utf-8",
        )
    (sample_dir / "metadata.json").write_text(
        json.dumps({"family_id": "family", "task_type": "family_alias"}),
        encoding="utf-8",
    )
    (sample_dir / "eval" / "labels.json").write_text(
        json.dumps(
            {
                "pass_level": pass_level,
                "highest_official_level": highest_official_level,
            }
        ),
        encoding="utf-8",
    )
    trajectory.write_text(
        json.dumps(
            {
                "sample_id": sample_id,
                "oracle_strength": {
                    "task_family": trajectory_family,
                    "reference_pass": True,
                    "mutation_cases": 2,
                    "killed": 2,
                    "mutation_score": 1.0,
                    "surviving_mutations": [],
                    "non_scoreable_mutations": [],
                    "mutation_details": {
                        "wrong_data": {"outcome": "killed", "artifact_dir": "oracle_mutations/wrong_data"},
                        "missing_stall": {"outcome": "killed", "artifact_dir": "oracle_mutations/missing_stall"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    entry = TaskFamilyEvidence(
        family_id="family",
        generator_status="implemented",
        testbench_status="implemented",
        golden_model_status="embedded_sv",
        mutation_evidence=MutationEvidence(status="qualified", score=1.0, run_id=run_id),
        highest_verified_level="L3",
        l4_open_status="not_run",
        l4_commercial_status="not_run",
        l5_status="not_run",
        last_verified_run=run_id,
        evidence_refs=(str(summary), str(trajectory), str(mutations)),
    )
    return entry, run_root, trajectory, mutations


def _qualified_independent_oracle_audit_fixture(tmp_path):
    entry, run_root, trajectory, mutations = _qualified_audit_fixture(tmp_path)
    sample_dir = trajectory.parent.parent
    oracle_root = sample_dir / "attempts" / "attempt_000" / "eval" / "oracle"
    field = OracleField(name="value", msb=0, lsb=0, signed=False)
    classes = (
        "public_smoke",
        "hidden_deterministic",
        "randomized_fixed_seed",
        "stress",
    )
    bundle = write_oracle_bundle(
        root=oracle_root,
        family_id="family",
        reference_model="test.reference",
        reference_version="1",
        task_parameters={},
        scenarios=tuple(
            OracleScenarioSpec(
                scenario_id=f"scenario_{index}",
                scenario_class=scenario_class,
                seed=index,
                input_record_width_bits=1,
                expected_record_width_bits=1,
                input_fields=(field,),
                expected_fields=(field,),
                input_records=(index % 2,),
                expected_records=(index % 2,),
            )
            for index, scenario_class in enumerate(classes)
        ),
    )
    results = tuple(
        OracleScenarioResult(
            scenario_id=scenario.scenario_id,
            scenario_class=scenario.scenario_class,
            status="passed",
            failure_origin=None,
            failure_type=None,
            command=("vvp", "sim.out"),
            exit_code=0,
            stdout="TEST_PASS",
            stderr="",
            duration_seconds=0.0,
        )
        for scenario in bundle.scenarios
    )
    write_oracle_run_evidence(
        oracle_root / "evidence.json",
        OracleRunEvidence.from_results(bundle, results),
    )
    payload = json.loads(trajectory.read_text(encoding="utf-8"))
    payload["oracle_profile"] = sanitize_oracle_profile(bundle)
    payload["oracle_profile"].update(
        {
            "status": "pass",
            "class_status": {scenario_class: "pass" for scenario_class in classes},
        }
    )
    trajectory.write_text(json.dumps(payload), encoding="utf-8")
    return (
        replace(
            entry,
            golden_model_status="python_reference",
            independent_oracle_evidence=IndependentOracleEvidence(
                status="qualified",
                run_id="line-a-qualified",
                bundle_sha256=bundle.bundle_sha256,
                scenario_classes=classes,
                hidden_vectors_exported=False,
            ),
        ),
        run_root,
        trajectory,
        oracle_root,
    )


def test_evidence_requires_one_entry_per_catalog_family(tmp_path):
    catalog = _write_catalog(tmp_path, ["a", "b"])
    evidence = _write_evidence(tmp_path, [_entry("a")])

    with pytest.raises(ValueError, match="missing evidence family_ids: b"):
        load_task_family_evidence(evidence, catalog_path=catalog)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"schema_version": "wrong"}, "invalid evidence schema_version"),
        ({"source_catalog": "wrong"}, "invalid evidence source_catalog"),
    ],
)
def test_evidence_rejects_invalid_document_identity(tmp_path, overrides, message):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [_entry("a")], **overrides)

    with pytest.raises(ValueError, match=message):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_evidence_rejects_duplicate_family_ids(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [_entry("a"), _entry("a")])

    with pytest.raises(ValueError, match="duplicate evidence family_ids"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_evidence_rejects_unexpected_family_ids(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [_entry("a"), _entry("b")])

    with pytest.raises(ValueError, match="unexpected evidence family_ids: b"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_implemented_generator_requires_catalog_alias(tmp_path):
    catalog = _write_catalog(tmp_path, ["planned"], aliases=[])
    evidence = _write_evidence(
        tmp_path,
        [_entry("planned", generator_status="implemented")],
    )

    with pytest.raises(ValueError, match="implemented generator has no catalog alias"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_l4_requires_implemented_generator_and_testbench(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(
        tmp_path,
        [_entry("a", highest_verified_level="L4", l4_open_status="pass")],
    )

    with pytest.raises(
        ValueError,
        match="L4 evidence requires implemented generator and testbench",
    ):
        load_task_family_evidence(evidence, catalog_path=catalog)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("generator_status", "unknown", "invalid generator_status"),
        ("testbench_status", "unknown", "invalid testbench_status"),
        ("golden_model_status", "unknown", "invalid golden_model_status"),
        ("highest_verified_level", "L2", "invalid highest_verified_level"),
        ("l4_open_status", "unknown", "invalid l4_open_status"),
        ("l4_commercial_status", "unknown", "invalid l4_commercial_status"),
        ("l5_status", "unknown", "invalid l5_status"),
    ],
)
def test_evidence_rejects_unknown_status_values(tmp_path, field, value, message):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [_entry("a", **{field: value})])

    with pytest.raises(ValueError, match=message):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_evidence_rejects_unknown_mutation_status(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(
        tmp_path,
        [_entry("a", mutation_evidence={"status": "unknown", "score": None, "run_id": ""})],
    )

    with pytest.raises(ValueError, match="invalid mutation status"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_implemented_testbench_requires_implemented_generator(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(tmp_path, [_entry("a", testbench_status="implemented")])

    with pytest.raises(
        ValueError,
        match="implemented testbench requires implemented generator",
    ):
        load_task_family_evidence(evidence, catalog_path=catalog)


@pytest.mark.parametrize("level", ["L3", "L4", "L5"])
def test_verified_level_requires_implemented_generator_and_testbench(tmp_path, level):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(tmp_path, [_entry("a", highest_verified_level=level)])

    with pytest.raises(
        ValueError,
        match=f"{level} evidence requires implemented generator and testbench",
    ):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_l4_pass_requires_l4_or_l5_level(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(
        tmp_path,
        [
            _entry(
                "a",
                generator_status="implemented",
                testbench_status="implemented",
                highest_verified_level="L3",
                l4_open_status="pass",
            )
        ],
    )

    with pytest.raises(ValueError, match="L4 pass requires highest level L4 or L5"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_l4_commercial_pass_requires_l4_or_l5_level(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(
        tmp_path,
        [
            _entry(
                "a",
                generator_status="implemented",
                testbench_status="implemented",
                highest_verified_level="L3",
                l4_commercial_status="pass",
            )
        ],
    )

    with pytest.raises(ValueError, match="L4 pass requires highest level L4 or L5"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_l5_pass_requires_l5_level(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(
        tmp_path,
        [
            _entry(
                "a",
                generator_status="implemented",
                testbench_status="implemented",
                highest_verified_level="L4",
                l5_status="pass",
            )
        ],
    )

    with pytest.raises(ValueError, match="L5 pass requires highest level L5"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_qualified_mutation_requires_bounded_score_and_run_id(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(
        tmp_path,
        [
            _entry(
                "a",
                mutation_evidence={"status": "qualified", "score": 1.1, "run_id": ""},
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match=r"qualified mutation requires score in \[0,1\] and non-empty run_id",
    ):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_not_run_mutation_requires_null_score_and_empty_run_id(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(
        tmp_path,
        [
            _entry(
                "a",
                mutation_evidence={"status": "not_run", "score": 0.0, "run_id": "run"},
            )
        ],
    )

    with pytest.raises(ValueError, match="not_run mutation requires null score and empty run_id"):
        load_task_family_evidence(evidence, catalog_path=catalog)


@pytest.mark.parametrize(
    ("oracle", "message"),
    [
        (
            {
                "status": "qualified",
                "run_id": "run",
                "bundle_sha256": "a" * 64,
                "scenario_classes": ["public_smoke"],
                "hidden_vectors_exported": False,
            },
            "qualified independent oracle requires all scenario classes",
        ),
        (
            {
                "status": "qualified",
                "run_id": "",
                "bundle_sha256": "a" * 64,
                "scenario_classes": [
                    "public_smoke",
                    "hidden_deterministic",
                    "randomized_fixed_seed",
                    "stress",
                ],
                "hidden_vectors_exported": False,
            },
            "qualified independent oracle requires non-empty run_id and bundle_sha256",
        ),
    ],
)
def test_qualified_independent_oracle_requires_complete_python_reference_provenance(
    tmp_path, oracle, message
):
    catalog = _write_catalog(tmp_path, ["a"], aliases=["a_task"])
    evidence = _write_evidence(
        tmp_path,
        [
            _entry(
                "a",
                generator_status="implemented",
                testbench_status="implemented",
                golden_model_status="python_reference",
                highest_verified_level="L3",
                independent_oracle_evidence=oracle,
            )
        ],
    )

    with pytest.raises(ValueError, match=message):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_provenance_strings_must_be_trimmed(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(
        tmp_path,
        [_entry("a", evidence_refs=[" docs/current-status.md"])],
    )

    with pytest.raises(ValueError, match="provenance strings must be trimmed"):
        load_task_family_evidence(evidence, catalog_path=catalog)


@pytest.mark.parametrize(
    "entry",
    [
        _entry("a", last_verified_run=" run"),
        _entry(
            "a",
            mutation_evidence={"status": "unqualified", "score": 0.0, "run_id": " run"},
        ),
        _entry("a", evidence_refs=["docs/current-status.md", " evidence.md"]),
    ],
)
def test_each_provenance_field_must_be_trimmed(tmp_path, entry):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [entry])

    with pytest.raises(ValueError, match="provenance strings must be trimmed"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_evidence_rejects_unhashable_status_values(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [_entry("a", generator_status=[])])

    with pytest.raises(ValueError, match="invalid generator_status"):
        load_task_family_evidence(evidence, catalog_path=catalog)


def test_direct_evidence_construction_copies_reference_sequence():
    references = ["docs/current-status.md"]
    entry = TaskFamilyEvidence(
        family_id="a",
        generator_status="not_implemented",
        testbench_status="not_implemented",
        golden_model_status="none",
        mutation_evidence=MutationEvidence(status="not_run", score=None, run_id=""),
        highest_verified_level="not_run",
        l4_open_status="not_run",
        l4_commercial_status="not_run",
        l5_status="not_run",
        last_verified_run="",
        evidence_refs=references,
    )
    references.append("docs/other.md")

    assert entry.evidence_refs == ("docs/current-status.md",)


def test_direct_evidence_construction_rejects_mutable_reference_members():
    with pytest.raises(TypeError, match="evidence_refs must contain strings"):
        TaskFamilyEvidence(
            family_id="a",
            generator_status="not_implemented",
            testbench_status="not_implemented",
            golden_model_status="none",
            mutation_evidence=MutationEvidence(status="not_run", score=None, run_id=""),
            highest_verified_level="not_run",
            l4_open_status="not_run",
            l4_commercial_status="not_run",
            l5_status="not_run",
            last_verified_run="",
            evidence_refs=[[]],
        )


def test_loads_immutable_evidence_types(tmp_path):
    catalog = _write_catalog(tmp_path, ["a"])
    evidence = _write_evidence(tmp_path, [_entry("a")])

    (entry,) = load_task_family_evidence(evidence, catalog_path=catalog)

    assert isinstance(entry, TaskFamilyEvidence)
    assert isinstance(entry.independent_oracle_evidence, IndependentOracleEvidence)
    assert isinstance(entry.mutation_evidence, MutationEvidence)
    assert entry.independent_oracle_evidence.status == "not_run"
    assert entry.evidence_refs == ()
    with pytest.raises(AttributeError):
        entry.family_id = "other"


def test_repository_ledger_covers_all_catalog_families():
    entries = load_task_family_evidence()

    assert len(entries) == 71
    assert len({entry.family_id for entry in entries}) == 71


def test_implemented_evidence_matches_current_generator_owners():
    entries = load_task_family_evidence()

    expected = set(TASK_FAMILY_IDS.values())
    actual = {
        entry.family_id
        for entry in entries
        if entry.generator_status == "implemented"
    }
    assert actual == expected


def test_only_proven_open_l4_families_are_marked_pass():
    entries = load_task_family_evidence()

    actual = {entry.family_id for entry in entries if entry.l4_open_status == "pass"}
    assert actual == {"fir_filter", "matrix_vector_mac"}


def test_qualified_mutation_evidence_matches_the_proven_twenty_one_family_set():
    entries = load_task_family_evidence()
    expected = {
        "sync_fifo",
        "uart_tx",
        "spi_master",
        "valid_ready_stream_stage",
        "fir_filter",
        "matrix_vector_mac",
        "uart_rx",
        "uart_fifo_loopback",
        "matched_filter",
        "peak_detector",
        "p_pulse_radar_signal",
        "sobel_threshold",
        "p_vision_defect_core",
        "pattern_matcher",
        "p_stream_trigger_filter",
        "qtable_update_core",
        "p_rl_qlearning_accel",
        "single_dual_port_ram",
        "valid_ready_stream_accumulator",
        "stream_fork_join",
        "mac_array",
    }
    qualified = {
        entry.family_id
        for entry in entries
        if entry.mutation_evidence.status == "qualified"
    }

    assert qualified == expected
    phase_c_independent_oracle = {
        "fir_filter",
        "matrix_vector_mac",
        "matched_filter",
        "peak_detector",
        "p_pulse_radar_signal",
        "sobel_threshold",
        "p_vision_defect_core",
        "qtable_update_core",
        "p_rl_qlearning_accel",
    }
    phase_b_core_closure = {
        "uart_rx",
        "uart_fifo_loopback",
        "pattern_matcher",
        "p_stream_trigger_filter",
    }
    phase_c_core_mutation_closure = {
        "single_dual_port_ram",
        "valid_ready_stream_accumulator",
        "stream_fork_join",
        "mac_array",
    }
    for entry in entries:
        if entry.family_id in expected:
            assert entry.mutation_evidence.score == 1.0
            if entry.family_id in phase_c_independent_oracle:
                expected_run = "phase-c-independent-oracle-20260716-v2"
            elif entry.family_id in phase_c_core_mutation_closure:
                expected_run = "phase-c-core-mutation-closure-20260716-v2"
            elif entry.family_id in phase_b_core_closure:
                expected_run = "phase-b-core-closure-20260713-v4"
            else:
                expected_run = "line-a-oracle-evidence-20260713-v2"
            assert entry.mutation_evidence.run_id == expected_run


def test_l4_pass_evidence_matches_the_proven_openxc7_family_set():
    entries = load_task_family_evidence()
    expected = {"fir_filter", "matrix_vector_mac"}
    l4_pass = {
        entry.family_id
        for entry in entries
        if entry.l4_open_status == "pass" or entry.l4_commercial_status == "pass"
    }

    assert l4_pass == expected
    for entry in entries:
        if entry.family_id in expected:
            assert entry.l4_open_status == "pass"
            assert entry.l4_commercial_status == "not_run"
            assert entry.highest_verified_level == "L4"
            assert entry.last_verified_run == "phase-c-independent-oracle-20260716-v2"
            assert entry.independent_oracle_evidence.status == "qualified"
            assert any(
                reference.endswith(
                    "/runs/line-a-l4-dual-tool-20260713-v2/summary.json"
                )
                for reference in entry.evidence_refs
            )
            assert any(
                "reports/evidence/legacy-runs/"
                "line-a-l4-dual-tool-20260713-v2/dataset/" in reference
                and reference.endswith("/eval/trajectory.json")
                for reference in entry.evidence_refs
            )
            assert any(
                "reports/evidence/legacy-runs/"
                "line-a-l4-dual-tool-20260713-v2/dataset/" in reference
                and reference.endswith("/eval/labels.json")
                for reference in entry.evidence_refs
            )
        else:
            assert entry.l4_open_status != "pass"
            assert entry.l4_commercial_status != "pass"


def test_non_implemented_families_carry_no_run_or_reference_evidence():
    entries = load_task_family_evidence()

    for entry in entries:
        if entry.generator_status == "not_implemented":
            assert entry.last_verified_run == ""
            assert entry.mutation_evidence.run_id == ""
            assert entry.evidence_refs == ()


def test_renderer_separates_target_implementation_and_evidence():
    markdown = render_task_evidence_markdown()

    assert "## Target Task Map" in markdown
    assert "## Current Implementation Matrix" in markdown
    assert "## Ledger-Declared Verification Claims" in markdown
    assert "not an audit of local artifacts" in markdown
    assert "Implemented families | 31 / 71" in markdown
    assert "Paper 1 core implemented | 14 / 14" in markdown
    assert "OpenXC7 L4 pass | 2" in markdown
    assert "Independent Python oracle qualified" in markdown
    assert "Independent oracle" in markdown

    target_map = markdown.split("## Target Task Map", 1)[1].split(
        "## Current Implementation Matrix", 1
    )[0]
    assert target_map.index("| clock_divider |") < target_map.index(
        "| binary_bcd_counter |"
    )


def test_docs_index_links_catalog_and_evidence_separately():
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    normalized_text = text.lower()

    assert "sr2fpga-task-catalog-v0.2.json" in text
    assert "sr2fpga-task-evidence-v0.1.json" in text
    assert "sr2fpga-task-evidence-status.md" in text
    assert "intended target contract and target policy" in normalized_text
    assert "current executable and verification facts" in normalized_text
    assert "human-readable derived view" in normalized_text
    assert "24-alias deterministic smoke curriculum" in normalized_text


def test_current_status_names_the_paper1_core_denominator():
    text = (REPO_ROOT / "docs" / "current-status.md").read_text(encoding="utf-8")

    assert (
        "| Paper 1 core implemented | 14/14 (denominator: v0.2 catalog "
        "`recommended_sets.paper1_core`) |" in text
    )
    assert "| Paper 1 core executable / L3 | 14/14 |" in text
    assert "| Paper 1 core mutation-qualified | 14/14 |" in text
    assert "| Mutation-qualified families | 21 |" in text
    assert "| Independent Python oracle qualified | 9 |" in text
    assert "`recommended_sets.paper1_core`" in text


def test_local_artifact_audit_is_explicit(tmp_path):
    issues = audit_local_run_artifacts(load_task_family_evidence(), tmp_path)

    assert any("phase-c-independent-oracle-20260716-v2" in issue for issue in issues)


def test_local_artifact_audit_matches_summary_run_id(tmp_path):
    summary = tmp_path / "arbitrary-directory" / "summary.json"
    summary.parent.mkdir()
    summary.write_text(
        json.dumps({"run_id": "line-a-l4-dual-tool-20260713-v2"}),
        encoding="utf-8",
    )

    issues = audit_local_run_artifacts(load_task_family_evidence(), tmp_path)

    assert not any("line-a-l4-dual-tool-20260713-v2" in issue for issue in issues)


def test_local_artifact_audit_accepts_qualified_trajectory_and_mutations(tmp_path):
    entry, run_root, _, _ = _qualified_audit_fixture(tmp_path)

    assert audit_local_run_artifacts((entry,), run_root) == ()


def test_local_artifact_audit_rejects_qualified_mutation_without_tool_evidence(tmp_path):
    entry, run_root, _, mutations = _qualified_audit_fixture(tmp_path)
    (mutations / "wrong_data" / "eval" / "sim_run.json").unlink()

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("missing mutation sim_run.json" in issue for issue in issues)


def test_local_artifact_audit_rejects_mutation_that_tool_run_did_not_kill(tmp_path):
    entry, run_root, _, mutations = _qualified_audit_fixture(tmp_path)
    sim_run = mutations / "wrong_data" / "eval" / "sim_run.json"
    sim_run.write_text(
        json.dumps(
            {
                "stage": "sim_run",
                "status": "passed",
                "exit_code": 0,
                "stdout": "TEST_PASS",
                "stderr": "",
            }
        ),
        encoding="utf-8",
    )

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("mutation tool evidence is not killed" in issue for issue in issues)


def test_local_artifact_audit_accepts_qualified_independent_oracle_artifacts(tmp_path):
    entry, run_root, _, _ = _qualified_independent_oracle_audit_fixture(tmp_path)

    assert audit_local_run_artifacts((entry,), run_root) == ()


def test_local_artifact_audit_accepts_withheld_independent_oracle_vectors(tmp_path):
    entry, run_root, _, oracle_root = _qualified_independent_oracle_audit_fixture(tmp_path)
    manifest = json.loads((oracle_root / "manifest.json").read_text(encoding="utf-8"))
    for scenario in manifest["scenarios"]:
        (oracle_root / scenario["input_path"]).unlink()
        (oracle_root / scenario["expected_path"]).unlink()

    assert audit_local_run_artifacts((entry,), run_root) == ()


def test_local_artifact_audit_rejects_partial_independent_oracle_vectors(tmp_path):
    entry, run_root, _, oracle_root = _qualified_independent_oracle_audit_fixture(tmp_path)
    manifest = json.loads((oracle_root / "manifest.json").read_text(encoding="utf-8"))
    (oracle_root / manifest["scenarios"][0]["input_path"]).unlink()

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("partial record files" in issue for issue in issues)


def test_local_artifact_audit_rejects_qualified_mutation_without_artifact_references(tmp_path):
    entry, run_root, _, _ = _qualified_audit_fixture(tmp_path)
    entry = replace(entry, evidence_refs=())

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any(
        "qualified evidence missing trajectory.json" in issue for issue in issues
    )
    assert any(
        "qualified evidence missing oracle_mutations" in issue for issue in issues
    )


def test_local_artifact_audit_rejects_qualified_independent_oracle_without_artifact_references(tmp_path):
    entry, run_root, _, _ = _qualified_independent_oracle_audit_fixture(tmp_path)
    entry = replace(entry, evidence_refs=())

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any(
        "qualified evidence missing trajectory.json" in issue for issue in issues
    )


def test_local_artifact_audit_rejects_independent_oracle_hidden_vector_leakage(tmp_path):
    entry, run_root, trajectory, _ = _qualified_independent_oracle_audit_fixture(tmp_path)
    payload = json.loads(trajectory.read_text(encoding="utf-8"))
    payload["oracle_profile"]["hidden_vectors_exported"] = True
    trajectory.write_text(json.dumps(payload), encoding="utf-8")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("hidden vectors were exported" in issue for issue in issues)


def test_local_artifact_audit_rejects_missing_independent_oracle_seed_hash(tmp_path):
    entry, run_root, trajectory, _ = _qualified_independent_oracle_audit_fixture(tmp_path)
    payload = json.loads(trajectory.read_text(encoding="utf-8"))
    del payload["oracle_profile"]["scenarios"][1]["seed_sha256"]
    trajectory.write_text(json.dumps(payload), encoding="utf-8")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("seed_sha256 does not match" in issue for issue in issues)


@pytest.mark.parametrize("leak_kind", ("seed", "path", "vector"))
def test_local_artifact_audit_inspects_exports_for_withheld_oracle_leakage(
    tmp_path, leak_kind
):
    entry, run_root, _, oracle_root = _qualified_independent_oracle_audit_fixture(tmp_path)
    manifest = json.loads((oracle_root / "manifest.json").read_text(encoding="utf-8"))
    hidden = next(
        scenario
        for scenario in manifest["scenarios"]
        if scenario["scenario_class"] == "hidden_deterministic"
    )
    if leak_kind == "seed":
        leaked = hidden["seed"]
    elif leak_kind == "path":
        leaked = hidden["input_path"]
    else:
        leaked = (oracle_root / hidden["input_path"]).read_text(encoding="utf-8").strip()
    export_path = run_root / "exports" / "failure_to_diagnosis.jsonl"
    export_path.parent.mkdir(parents=True)
    export_path.write_text(json.dumps({"leaked": leaked}) + "\n", encoding="utf-8")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any(f"withheld oracle {leak_kind} leaked" in issue for issue in issues)


@pytest.mark.parametrize(
    ("leak_kind", "encode"),
    (
        ("seed", lambda hidden, oracle_root: str(hidden["seed"])),
        ("path", lambda hidden, oracle_root: hidden["input_path"].replace("/", "\\")),
        (
            "vector",
            lambda hidden, oracle_root: "prefix="
            + (oracle_root / hidden["input_path"]).read_text(encoding="utf-8").strip()
            + ";suffix",
        ),
    ),
)
def test_local_artifact_audit_rejects_equivalent_withheld_oracle_serializations(
    tmp_path, leak_kind, encode
):
    entry, run_root, _, oracle_root = _qualified_independent_oracle_audit_fixture(tmp_path)
    manifest = json.loads((oracle_root / "manifest.json").read_text(encoding="utf-8"))
    hidden = next(
        scenario
        for scenario in manifest["scenarios"]
        if scenario["scenario_class"] == "hidden_deterministic"
    )
    export_path = run_root / "exports" / "failure_to_diagnosis.jsonl"
    export_path.parent.mkdir(parents=True)
    export_path.write_text(
        json.dumps({"leaked": encode(hidden, oracle_root)}) + "\n",
        encoding="utf-8",
    )

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any(f"withheld oracle {leak_kind} leaked" in issue for issue in issues)


def test_local_artifact_audit_rejects_independent_oracle_bundle_hash_mismatch(tmp_path):
    entry, run_root, _, _ = _qualified_independent_oracle_audit_fixture(tmp_path)
    entry = replace(
        entry,
        independent_oracle_evidence=replace(
            entry.independent_oracle_evidence,
            bundle_sha256="b" * 64,
        ),
    )

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("bundle_sha256 does not match" in issue for issue in issues)


def test_local_artifact_audit_rejects_non_l3_sample_for_l3_ledger_entry(tmp_path):
    entry, run_root, _, _ = _qualified_audit_fixture(
        tmp_path,
        summary_bucket="repair_trajectory",
        pass_level="L2",
        highest_official_level="L2",
    )

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("sample labels do not reach ledger highest_verified_level" in issue for issue in issues)
    assert any("L3 ledger evidence is not in summary success_l3 bucket" in issue for issue in issues)


@pytest.mark.parametrize("ledger_level", ("L4", "L5"))
def test_local_artifact_audit_uses_generic_level_order_for_higher_ledger_levels(tmp_path, ledger_level):
    entry, run_root, _, _ = _qualified_audit_fixture(tmp_path)
    entry = replace(entry, highest_verified_level=ledger_level)

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("sample labels do not reach ledger highest_verified_level" in issue for issue in issues)


def test_independent_oracle_refresh_rejects_unbacked_l4_level(tmp_path):
    entry, run_root, _, _ = _qualified_independent_oracle_audit_fixture(tmp_path)
    entry = replace(
        entry,
        highest_verified_level="L4",
        l4_open_status="pass",
        l4_commercial_status="pass",
        evidence_refs=entry.evidence_refs + ("docs/historical-l4-evidence.md",),
    )

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("L4 evidence is not artifact-backed" in issue for issue in issues)


def test_independent_oracle_refresh_accepts_artifact_backed_l4_level(tmp_path):
    entry, run_root, _, _ = _qualified_independent_oracle_audit_fixture(tmp_path)
    historical_run_id = "line-a-l4-reference"
    historical_sample_id = "sample_line_a_l4_family"
    summary = run_root / historical_run_id / "summary.json"
    summary.parent.mkdir(parents=True)
    summary.write_text(
        json.dumps(
            {
                "run_id": historical_run_id,
                "buckets": {
                    "success_l3": [historical_sample_id],
                    "repair_trajectory": [],
                    "rejected": [],
                },
            }
        ),
        encoding="utf-8",
    )
    sample_dir = tmp_path / "l4_dataset" / historical_sample_id
    labels = sample_dir / "eval" / "labels.json"
    trajectory = sample_dir / "eval" / "trajectory.json"
    labels.parent.mkdir(parents=True)
    (sample_dir / "metadata.json").write_text(
        json.dumps({"family_id": "family", "task_type": "family_alias"}),
        encoding="utf-8",
    )
    labels.write_text(
        json.dumps({"pass_level": "L4", "highest_official_level": "L4"}),
        encoding="utf-8",
    )
    open_report = sample_dir / "reports" / "openxc7.json"
    commercial_report = sample_dir / "reports" / "vivado.json"
    open_report.parent.mkdir(parents=True)
    open_report.write_text("{}", encoding="utf-8")
    commercial_report.write_text("{}", encoding="utf-8")
    trajectory.write_text(
        json.dumps(
            {
                "sample_id": historical_sample_id,
                "verification": {
                    "l4_open": {
                        "status": "pass",
                        "report_paths": ["reports/openxc7.json"],
                    },
                    "l4_commercial": {
                        "status": "pass",
                        "report_paths": ["reports/vivado.json"],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    entry = replace(
        entry,
        highest_verified_level="L4",
        l4_open_status="pass",
        l4_commercial_status="pass",
        evidence_refs=entry.evidence_refs
        + (str(summary), str(trajectory), str(labels)),
    )

    assert audit_local_run_artifacts((entry,), run_root) == ()


def test_local_artifact_audit_reports_missing_trajectory_reference(tmp_path):
    entry, run_root, _, mutations = _qualified_audit_fixture(tmp_path)
    missing_trajectory = tmp_path / "dataset" / "missing" / "eval" / "trajectory.json"
    entry = replace(entry, evidence_refs=(entry.evidence_refs[0], str(missing_trajectory), str(mutations)))

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("missing trajectory.json evidence artifact" in issue for issue in issues)


def test_local_artifact_audit_reports_trajectory_sample_from_wrong_run(tmp_path):
    entry, run_root, _, _ = _qualified_audit_fixture(
        tmp_path, summary_sample_id="sample_from_another_run"
    )

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("is not recorded by summary run_id: line-a-qualified" in issue for issue in issues)


def test_local_artifact_audit_reports_trajectory_family_mismatch(tmp_path):
    entry, run_root, _, _ = _qualified_audit_fixture(tmp_path, trajectory_family="other_family")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("trajectory task_family does not match ledger family_id" in issue for issue in issues)


def test_local_artifact_audit_reports_missing_declared_mutation_artifact(tmp_path):
    entry, run_root, _, mutations = _qualified_audit_fixture(tmp_path)
    shutil.rmtree(mutations / "missing_stall")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("missing declared mutation artifact" in issue for issue in issues)


def test_local_artifact_audit_reports_qualified_score_mismatch(tmp_path):
    entry, run_root, trajectory, _ = _qualified_audit_fixture(tmp_path)
    payload = json.loads(trajectory.read_text(encoding="utf-8"))
    payload["oracle_strength"]["mutation_score"] = 0.5
    trajectory.write_text(json.dumps(payload), encoding="utf-8")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("trajectory mutation_score does not match ledger score" in issue for issue in issues)


def test_local_artifact_audit_reports_non_scoreable_declared_mutation(tmp_path):
    entry, run_root, trajectory, _ = _qualified_audit_fixture(tmp_path)
    payload = json.loads(trajectory.read_text(encoding="utf-8"))
    oracle = payload["oracle_strength"]
    oracle["mutation_details"]["missing_stall"]["outcome"] = "non_scoreable"
    oracle["non_scoreable_mutations"] = ["missing_stall"]
    oracle["killed"] = 1
    oracle["mutation_cases"] = 1
    trajectory.write_text(json.dumps(payload), encoding="utf-8")

    issues = audit_local_run_artifacts((entry,), run_root)

    assert any("declared mutations are not all scoreable and killed" in issue for issue in issues)


def test_cli_writes_only_explicit_output_and_preserves_ledger(tmp_path):
    output = tmp_path / "status.md"
    ledger_before = EVIDENCE_PATH.read_bytes()

    assert main(["--output", str(output)]) == 0

    assert output.read_text(encoding="utf-8") == render_task_evidence_markdown()
    assert EVIDENCE_PATH.read_bytes() == ledger_before


def test_cli_rejects_the_evidence_ledger_output_path(tmp_path, monkeypatch, capsys):
    ledger = tmp_path / "evidence.json"
    ledger.write_text('{"unchanged": true}\n', encoding="utf-8")
    alias_directory = tmp_path / "alias"
    alias_directory.mkdir()
    alias = alias_directory / ".." / ledger.name
    monkeypatch.setattr(task_evidence, "EVIDENCE_PATH", ledger)

    with pytest.raises(SystemExit) as excinfo:
        main(["--output", str(alias)])

    assert excinfo.value.code == 2
    assert "--output must not overwrite the evidence ledger" in capsys.readouterr().err
    assert ledger.read_text(encoding="utf-8") == '{"unchanged": true}\n'


def test_cli_audit_returns_one_and_reports_missing_declared_run(tmp_path, capsys):
    output = tmp_path / "status.md"

    assert main(["--output", str(output), "--audit-run-root", str(tmp_path)]) == 1

    captured = capsys.readouterr()
    assert "phase-c-independent-oracle-20260716-v2" in captured.err
    assert output.read_text(encoding="utf-8") == render_task_evidence_markdown()


def test_cli_audit_returns_zero_when_every_declared_run_has_summary(tmp_path, capsys, monkeypatch):
    run_root = tmp_path / "runs"
    run_id = "legacy-summary-only"
    summary = run_root / "run" / "summary.json"
    summary.parent.mkdir(parents=True)
    summary.write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    entries = (
        TaskFamilyEvidence(
            family_id="legacy",
            generator_status="not_implemented",
            testbench_status="not_implemented",
            golden_model_status="none",
            mutation_evidence=MutationEvidence(status="not_run", score=None, run_id=""),
            highest_verified_level="not_run",
            l4_open_status="not_run",
            l4_commercial_status="not_run",
            l5_status="not_run",
            last_verified_run=run_id,
            evidence_refs=(),
        ),
    )
    monkeypatch.setattr(task_evidence, "load_task_family_evidence", lambda: entries)
    monkeypatch.setattr(task_evidence, "render_task_evidence_markdown", lambda: "fixture status\n")
    output = tmp_path / "status.md"

    assert main(["--output", str(output), "--audit-run-root", str(run_root)]) == 0

    assert capsys.readouterr().err == ""
    assert output.read_text(encoding="utf-8") == "fixture status\n"


def test_phase_b_core_closure_evidence_is_retained_or_superseded_by_phase_c():
    phase_b_retained = {
        "uart_rx",
        "uart_fifo_loopback",
        "pattern_matcher",
        "p_stream_trigger_filter",
    }
    phase_c_promoted = {
        "matched_filter",
        "peak_detector",
        "p_pulse_radar_signal",
        "sobel_threshold",
        "p_vision_defect_core",
    }
    entries = {entry.family_id: entry for entry in load_task_family_evidence()}

    for family_id in phase_b_retained:
        entry = entries[family_id]
        assert entry.generator_status == "implemented"
        assert entry.testbench_status == "implemented"
        assert entry.golden_model_status == "embedded_sv"
        assert entry.highest_verified_level == "L3"
        assert entry.mutation_evidence.status == "qualified"
        assert entry.mutation_evidence.score == 1.0
        assert entry.mutation_evidence.run_id == entry.last_verified_run
        assert entry.l4_open_status == "not_run"
        assert entry.l4_commercial_status == "not_run"
        assert entry.l5_status == "not_run"
        assert len(entry.evidence_refs) == 3
        assert entry.evidence_refs[0].endswith("/summary.json")
        assert entry.evidence_refs[1].endswith("/eval/trajectory.json")
        assert entry.evidence_refs[2].endswith("/oracle_mutations")
        assert all(
            reference.startswith(
                "reports/evidence/legacy-runs/"
                "phase-b-core-closure-20260713-v4/"
            )
            for reference in entry.evidence_refs
        )
        assert entry.last_verified_run == "phase-b-core-closure-20260713-v4"

    for family_id in phase_c_promoted:
        entry = entries[family_id]
        assert entry.golden_model_status == "python_reference"
        assert entry.last_verified_run == "phase-c-independent-oracle-20260716-v2"
        assert entry.independent_oracle_evidence.status == "qualified"


def test_phase_c_promotes_exactly_nine_independent_python_reference_families():
    expected = {
        "fir_filter",
        "matrix_vector_mac",
        "matched_filter",
        "peak_detector",
        "p_pulse_radar_signal",
        "sobel_threshold",
        "p_vision_defect_core",
        "qtable_update_core",
        "p_rl_qlearning_accel",
    }
    entries = {entry.family_id: entry for entry in load_task_family_evidence()}
    qualified = {
        family_id
        for family_id, entry in entries.items()
        if entry.independent_oracle_evidence.status == "qualified"
    }

    assert qualified == expected
    for family_id in expected:
        entry = entries[family_id]
        oracle = entry.independent_oracle_evidence
        assert entry.golden_model_status == "python_reference"
        assert entry.mutation_evidence.status == "qualified"
        assert entry.mutation_evidence.score == 1.0
        assert entry.mutation_evidence.run_id == "phase-c-independent-oracle-20260716-v2"
        assert entry.last_verified_run == "phase-c-independent-oracle-20260716-v2"
        assert set(oracle.scenario_classes) == {
            "public_smoke",
            "hidden_deterministic",
            "randomized_fixed_seed",
            "stress",
        }
        assert oracle.hidden_vectors_exported is False
        assert len(oracle.bundle_sha256) == 64
        assert any(reference.endswith("/eval/trajectory.json") for reference in entry.evidence_refs)
        assert any(reference.endswith("/eval/oracle/manifest.json") for reference in entry.evidence_refs)
        assert any(reference.endswith("/eval/oracle/evidence.json") for reference in entry.evidence_refs)
        assert any(reference.endswith("/oracle_mutations") for reference in entry.evidence_refs)


def test_all_catalog_paper1_core_families_are_mutation_qualified():
    catalog = json.loads(
        (REPO_ROOT / "docs" / "sr2fpga-task-catalog-v0.2.json").read_text(
            encoding="utf-8"
        )
    )
    entries = {entry.family_id: entry for entry in load_task_family_evidence()}

    for family_id in catalog["recommended_sets"]["paper1_core"]:
        evidence = entries[family_id].mutation_evidence
        assert evidence.status == "qualified"
        assert evidence.score == 1.0
