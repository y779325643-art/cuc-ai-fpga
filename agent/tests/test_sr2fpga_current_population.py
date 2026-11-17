"""LLM case amendment v2.3: current identity is not historical readiness."""

import json

import pytest

from sr2fpga_agent import task_catalog
from sr2fpga_agent.testbench_checker import build_oracle_strength, oracle_strength_ready


def test_current_population_is_three_unqualified_llm_families():
    specs = task_catalog.current_research_family_specs()
    assert {spec.family_id for spec in specs} == {
        "llm_quantized_qkv_projection", "llm_kv_cache_decode_attention", "llm_gated_ffn",
    }
    for spec in specs:
        assert spec.pc_format == "sr2fpga-pc-2.1"
        assert spec.implementation_status == "partial"
        assert spec.oracle_readiness == "partial"
        assert spec.current_generator_aliases == ()
        assert spec.mutation_score_threshold is None
        assert not oracle_strength_ready(spec.family_id, 1.0)
        strength = build_oracle_strength(True, {"synthetic_probe": "failed"}, spec.family_id)
        assert strength["threshold"] is None
        assert strength["line_a_ready"] is False


@pytest.mark.parametrize("damage", ["missing", "old_plan", "old_population", "old_format", "legacy_set", "prior_ai_set", "duplicate"])
def test_population_never_falls_back_to_old_tasks(tmp_path, monkeypatch, damage):
    catalog = json.loads(task_catalog.CATALOG_PATH.read_text(encoding="utf-8"))
    if damage == "missing":
        del catalog["current_research"]
    elif damage == "old_plan":
        catalog["current_research"]["research_plan_version"] = "paper1-v2.2"
    elif damage == "old_population":
        catalog["current_research"]["population_id"] = "quantized_ai_subsystems_v1"
    elif damage == "old_format":
        catalog["current_research"]["pc_format"] = "system-his-v1.2"
    elif damage == "legacy_set":
        catalog["current_research"]["primary_recommended_set"] = "legacy_paper1_core"
    elif damage == "prior_ai_set":
        catalog["current_research"]["primary_recommended_set"] = "legacy_quantized_ai_core_v2_2"
    else:
        catalog["recommended_sets"]["paper1_core"] *= 2
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(task_catalog, "CATALOG_PATH", path)
    with pytest.raises(ValueError):
        task_catalog.current_research_family_specs()
