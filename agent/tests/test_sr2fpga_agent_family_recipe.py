import json
import re

import pytest

from sr2fpga_agent.family_recipe import recipe_task_type, select_family_recipe
from sr2fpga_agent.generation.req2his import _prepare_requirement
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.prompts import (
    _system_his_v12_messages,
    _with_system_his_retry_feedback,
)
from sr2fpga_agent.requirement_envelope import build_request_requirement_envelope


def test_natural_alu_phrase_cannot_use_recipe_to_resolve_preflight_ambiguity() -> None:
    request = _request(
        task_type="unclassified",
        description="Build an 8-bit ALU control unit.",
    )

    from sr2fpga_agent.generation.req2his import RequirementClarificationRequired

    with pytest.raises(RequirementClarificationRequired) as caught:
        _prepare_requirement(request, _platform())

    assert caught.value.ambiguity_keys == ("functional_decomposition",)


def test_registered_chinese_mac_phrase_applies_recipe() -> None:
    request = _request(
        task_type="unclassified",
        description="设计一个 8 位乘加阵列 MAC。",
    )
    envelope = build_request_requirement_envelope(request, _platform())

    decision = select_family_recipe(request, envelope)

    assert decision.status == "applied"
    assert decision.family_id == "mac_array"
    assert decision.matched_alias == "乘加阵列 mac"
    assert recipe_task_type(decision) == "composed_vector_mac_pipeline"


def test_candidate_heldout_t4_recipe_is_denied() -> None:
    request = _request(
        task_type="composed_dual_stream_join",
        description="Generate a dual stream join.",
    )
    envelope = build_request_requirement_envelope(request, _platform())

    decision = select_family_recipe(request, envelope)

    assert decision.status == "not_applied"
    assert decision.family_id == "stream_fork_join"
    assert decision.recipe_id == "sr2fpga-family-recipe:composed_dual_stream_join"
    assert decision.reason == "candidate_primary_family_heldout"
    assert recipe_task_type(decision) is None


def test_heldout_natural_phrase_does_not_leak_family_or_policy_into_prompt() -> None:
    request = _request(
        task_type="unclassified",
        description="Generate an 8-bit dual stream join.",
    )
    envelope = build_request_requirement_envelope(request, _platform())
    decision = select_family_recipe(request, envelope)

    messages = _system_his_v12_messages(request, _platform())
    prompt = "\n".join(message["content"] for message in messages)

    assert decision.status == "not_applied"
    assert decision.family_id == "stream_fork_join"
    assert decision.reason == "candidate_primary_family_heldout"
    assert '"strategy": "capability_composition"' in prompt
    assert "Required architecture for composed_dual_stream_join" not in prompt
    assert decision.recipe_id not in prompt
    assert decision.policy_id not in prompt
    assert decision.policy_status not in prompt
    assert "stream_fork_join" not in prompt
    assert "composed_dual_stream_join" not in prompt
    assert "t4_dual_stream_join" not in prompt


def test_unknown_requirement_uses_generic_fallback() -> None:
    request = _request(
        task_type="customer_datapath",
        description="Build a custom arithmetic datapath.",
    )
    envelope = build_request_requirement_envelope(request, _platform())

    decision = select_family_recipe(request, envelope)

    assert decision.status == "not_applied"
    assert decision.reason == "no_exact_match"
    assert decision.recipe_id is None
    assert decision.family_id is None


def test_near_fuzzy_and_broad_phrases_do_not_match() -> None:
    descriptions = (
        "Build an ALU control units array.",
        "Build an alu-control-unitish accelerator.",
        "设计一个 8 位乘加模块。",
    )

    for description in descriptions:
        request = _request(task_type="unclassified", description=description)
        envelope = build_request_requirement_envelope(request, _platform())
        decision = select_family_recipe(request, envelope)
        assert decision.status == "not_applied"
        assert decision.reason == "no_exact_match"


def test_declared_and_description_cross_family_match_is_generic() -> None:
    request = _request(
        task_type="alu_control_unit",
        description="Build an 8-bit CRC stream checker.",
    )
    envelope = build_request_requirement_envelope(request, _platform())

    decision = select_family_recipe(request, envelope)

    assert decision.status == "not_applied"
    assert decision.reason == "conflicting_exact_matches"
    assert decision.recipe_id is None
    assert decision.family_id is None


def test_conflicting_mac_array_owners_do_not_select_a_recipe() -> None:
    request = _request(
        task_type="mac_array",
        description="Build an 8-bit vector MAC pipeline.",
    )
    envelope = build_request_requirement_envelope(request, _platform())

    decision = select_family_recipe(request, envelope)

    assert decision.status == "not_applied"
    assert decision.reason == "conflicting_exact_owners"
    assert decision.recipe_id is None
    assert decision.family_id is None


def test_decision_hash_and_policy_metadata_are_json_safe() -> None:
    request = _request(
        task_type="alu_control_unit",
        description="Build an 8-bit ALU control unit.",
    )
    envelope = build_request_requirement_envelope(request, _platform())

    first = select_family_recipe(request, envelope).to_dict()
    second = select_family_recipe(request, envelope).to_dict()

    assert first == second
    assert set(first) == {
        "recipe_id",
        "version",
        "sha256",
        "family_id",
        "matched_alias",
        "status",
        "reason",
        "policy_id",
        "policy_version",
        "policy_sha256",
        "policy_status",
        "catalog_version",
    }
    assert re.fullmatch(r"[0-9a-f]{64}", str(first["sha256"]))
    assert re.fullmatch(r"[0-9a-f]{64}", str(first["policy_sha256"]))
    assert first["policy_status"] == "candidate_g4a_not_signed"
    assert first["catalog_version"] == "0.2.2"
    assert json.loads(json.dumps(first, sort_keys=True)) == first


def test_decision_metadata_is_not_exposed_to_the_model_prompt() -> None:
    request = _request(
        task_type="alu_control_unit",
        description="Build an 8-bit ALU control unit.",
    )
    envelope, route, decision = _prepare_requirement(request, _platform())

    messages = _system_his_v12_messages(
        request,
        _platform(),
        requirement_envelope=envelope,
        requirement_route=route,
        family_recipe_decision=decision,
    )
    prompt = "\n".join(message["content"] for message in messages)

    assert "Required architecture for alu_control_unit" in prompt
    assert decision.recipe_id not in prompt
    assert decision.policy_id not in prompt
    assert decision.policy_status not in prompt
    assert "family_recipe_decision" not in prompt


def test_initial_and_retry_prompts_use_the_same_programmatic_recipe() -> None:
    request = _request(
        task_type="alu_control_unit",
        description="Build an 8-bit ALU control unit.",
    )
    envelope, route, decision = _prepare_requirement(request, _platform())
    selected_task_type = recipe_task_type(decision)
    initial = _system_his_v12_messages(
        request,
        _platform(),
        requirement_envelope=envelope,
        requirement_route=route,
        family_recipe_decision=decision,
    )

    retry = _with_system_his_retry_feedback(
        initial,
        "H3 validation failed",
        "{}",
        task_type=request.task_type,
        family_recipe_task_type=selected_task_type,
        requirement_trace_template=envelope.requirement_trace_template(),
    )

    assert selected_task_type == "alu_control_unit"
    assert "Required architecture for alu_control_unit" in initial[-1]["content"]
    assert "Keep control_decode, alu_core, and status_flags" in retry[-1]["content"]
    assert decision.recipe_id not in retry[-1]["content"]
    assert decision.policy_id not in retry[-1]["content"]


def _request(*, task_type: str, description: str) -> ProjectRequest:
    return ProjectRequest(
        task_type=task_type,
        width=8,
        project_name="family_recipe_test",
        description=description,
    )


def _platform() -> PlatformProfile:
    return PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )
