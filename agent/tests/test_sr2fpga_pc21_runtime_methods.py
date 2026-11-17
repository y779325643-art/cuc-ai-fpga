"""Offline six-method lifecycle regressions with explicit synthetic responses.

Answers are supplied by this test fixture, never an implementation generation
service. PC admission, specialization and real Yosys behavior parsing remain
real; only the method-neutral public verdict is controlled in these unit tests.
"""

from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
from importlib import import_module
import json

import pytest

from sr2fpga_agent.execution.budgets import BudgetLimits
from sr2fpga_agent.execution.evaluation import EvaluationResult, task_identity
from sr2fpga_agent.execution.gateway import ReplayTransport
from sr2fpga_agent.execution.isolation import ToolLimits, candidate_sha256
from sr2fpga_agent.execution import runtime as runtime_module
from sr2fpga_agent.execution.runtime import METHODS, PairedBlockRuntime, RuntimeIdentity
from sr2fpga_agent.local_tools import resolve_executable
from sr2fpga_agent.models import ToolResult, canonical_json_bytes
from sr2fpga_agent.pc.context import check_task_design, load_public_task
from sr2fpga_agent.pc.emitter import build_structure
from sr2fpga_agent.pc.inputs import ParseLimits, TrustedContext, TrustedSource


pytestmark = pytest.mark.skipif(resolve_executable("yosys") is None, reason="real Yosys behavior frontend required")
PRIVATE_CANARY = "PRIVATE_EVALUATOR_ONLY_9f1ac7"


def public_fixture(tmp_path):
    module = import_module("sr2fpga_agent.tasks.llm_ffn")
    value = module.build_development_task()
    public = tmp_path / "input-public"
    public.mkdir()
    assets = []
    for index, (name, content) in enumerate(value["public_assets"].items()):
        path = f"asset-{index}.json"
        (public / path).write_bytes(content)
        assets.append({"id": name, "path": path, "size_bytes": len(content),
                       "sha256": hashlib.sha256(content).hexdigest()})
    requirements = {
        "contract_version": "development-public-context-v2", "analysis_population": "development",
        "requirement_id": value["task_id"], "revision_id": "synthetic-runtime-fixture-v1",
        "public_text": value["public_text"], "boundary": value["boundary"]["boundary"],
        "fact_records": [{"fact_id": name, **fact, "provenance": "system_assumption", "source_ids": ["fixture"]}
                         for name, fact in value["facts"].items()], "public_assets": assets,
    }
    context = TrustedContext(TrustedSource("requirements", canonical_json_bytes(requirements)),
                             TrustedSource("target", canonical_json_bytes(value["target_profile"])),
                             TrustedSource("capability", canonical_json_bytes(value["capability_profile"])))
    task = load_public_task(context, asset_root=public, limits=ParseLimits(8_000_000, 128))
    design = module.reference_design()
    build = build_structure(check_task_design(design, task), bindings=context.bindings(),
                            toolchain_id=task.target["target_id"])
    bodies = import_module("sr2fpga_agent.tasks.llm_ffn.reference").reference_behavior_bodies()
    files = dict(build.files)
    for unit in build.units.values():
        files[unit["path"]] = unit["header"] + bodies[unit["module_id"]] + "\nendmodule\n"
    files["manifest.json"] = canonical_json_bytes(build.manifest).decode()
    return task, design, bodies, files


class SyntheticMethodTransport(ReplayTransport):
    """Stage-aware test fixture; intentionally labelled synthetic_fixture."""

    def __init__(self, design, bodies, files, *, invalid_initial_pc=False,
                 invalid_direct=False, m1_actions=(), m5_actions=(), fail_revised_body=False):
        super().__init__({})
        self.design, self.bodies, self.files = copy.deepcopy(design), dict(bodies), dict(files)
        self.invalid_initial_pc = invalid_initial_pc
        self.invalid_direct = invalid_direct
        self.m1_actions, self.m5_actions = list(m1_actions), list(m5_actions)
        self.fail_revised_body = fail_revised_body
        self.stage_counts = {}
        self.body_requests = []
        self.revised_design = copy.deepcopy(design)
        changed_name = "FfnGateUpRevised"
        self.revised_design["modules"][changed_name] = self.revised_design["modules"].pop("FfnGateUp")
        top = self.revised_design["modules"][self.revised_design["entry"]]
        top["implementation"]["instances"]["project"]["module"] = changed_name
        self.bodies[changed_name] = self.bodies["FfnGateUp"]

    def generate(self, messages, *, stage, max_output_tokens, timeout_seconds):
        payload = json.loads(messages[-1]["content"])
        ordinal = self.stage_counts.get(stage, 0)
        self.stage_counts[stage] = ordinal + 1
        if stage in {"direct_project", "project_from_plan", "project_from_pc"}:
            files = dict(self.files)
            path = next(path for path in sorted(files) if path.startswith("rtl/"))
            files[path] += "\n// fixture-stage: " + stage + "\n"
            response = {"contract_version": "pc21-project-proposal-v1", "files": files}
            if self.invalid_direct and stage == "direct_project":
                response["files"] = {"manifest.json": "{}"}
        elif stage == "untyped_plan":
            response = "Buffer and project the two public tokens; preserve their public stream order."
        elif stage == "pc_plan":
            response = copy.deepcopy(self.design)
            if self.invalid_initial_pc:
                response["entry"] = "UndefinedEntry"
        elif stage == "behavior":
            self.body_requests.append(copy.deepcopy(payload))
            if self.fail_revised_body and any(
                    unit["module_id"] == "FfnGateUpRevised" for unit in payload["required_units"].values()):
                response = {"text": "{truncated", "input_tokens": self.count_input_tokens(messages),
                            "output_tokens": 10, "failure": "output_truncated"}
                self.responses.setdefault(stage, []).append(response)
                return super().generate(messages, stage=stage, max_output_tokens=max_output_tokens,
                                        timeout_seconds=timeout_seconds)
            response = {"contract_version": "pc21-behavior-bundle-v1",
                        "build_plan_sha256": payload["build_plan_sha256"],
                        "units": {unit_id: {"body": self.bodies[unit["module_id"]]}
                                  for unit_id, unit in payload["required_units"].items()}}
        elif stage == "repair_M1":
            action = self.m1_actions.pop(0) if self.m1_actions else "noop"
            if action == "project":
                response = {"contract_version": "pc21-repair-proposal-v1", "action": "replace_project",
                            "files": self.files}
            elif action == "invalid":
                response = {"contract_version": "pc21-repair-proposal-v1", "action": "replace_project_files",
                            "base_candidate_sha256": payload["current_candidate_sha256"],
                            "files": {"hidden/evaluator.sv": "module forbidden;endmodule"}, "remove_paths": []}
            else:
                files = payload["current_files"]
                path = next(path for path in sorted(files) if path.startswith("rtl/"))
                text = files[path] + ("\n// M1 repaired fixture\n" if action == "patch" else "")
                response = {"contract_version": "pc21-repair-proposal-v1", "action": "replace_project_files",
                            "base_candidate_sha256": payload["current_candidate_sha256"],
                            "files": {path: text}, "remove_paths": []}
        elif stage == "repair_M5":
            action = self.m5_actions.pop(0) if self.m5_actions else "invalid"
            if action in {"design", "correct_pc"}:
                response = {"contract_version": "pc21-repair-proposal-v1", "action": "replace_design",
                            "design": self.revised_design if action == "design" else self.design}
            elif action == "body":
                unit = next(iter(payload["behavior_bundle"]["units"]))
                body = payload["behavior_bundle"]["units"][unit]["body"] + "\n// M5 repaired fixture\n"
                response = {"contract_version": "pc21-repair-proposal-v1", "action": "replace_behavior_units",
                            "base_candidate_sha256": payload["current_candidate_sha256"],
                            "build_plan_sha256": payload["build"]["build_plan_sha256"], "units": {unit: {"body": body}}}
            else:
                response = {"contract_version": "pc21-repair-proposal-v1", "action": "replace_design", "design": {}}
        else:
            raise AssertionError("unexpected synthetic model stage " + stage)
        text = response if isinstance(response, str) else canonical_json_bytes(response).decode()
        self.responses.setdefault(stage, []).append(text)
        return super().generate(messages, stage=stage, max_output_tokens=max_output_tokens,
                                timeout_seconds=timeout_seconds)


class ControlledPublicVerdicts:
    """Deterministic verdicts test controller transitions, not RTL performance."""

    def __init__(self, accept=lambda files: True):
        self.accept = accept
        self.calls = []

    def factory(self, case, task, root, **options):
        owner = self
        suite = options["suite"]
        class Evaluator:
            tool_policy_sha256 = "c" * 64

            def evaluate(self, files, *, evaluation_id, visibility="public"):
                owner.calls.append({"files": copy.deepcopy(files), "visibility": visibility,
                                    "evaluation_id": evaluation_id})
                accepted = owner.accept(files)
                stages = {"l0": "pass", "l1": "pass", "l2": "pass" if accepted else "fail",
                          "l3": "pass" if accepted else "not_run"}
                return EvaluationResult(candidate_sha256(files), task_identity(task), suite.commitment_sha256,
                                        self.tool_policy_sha256, visibility, "completed", "pass" if accepted else "fail",
                                        stages, () if accepted else ("functional_mismatch",),
                                        private_record_ref={"key": PRIVATE_CANARY, "sha256": "f" * 64})
        return Evaluator()


def configured_runtime(tmp_path, *, verdicts=None, transport_options=None, schedule_seed=0, backend=None):
    task, design, bodies, files = public_fixture(tmp_path)
    transport = SyntheticMethodTransport(design, bodies, files, **(transport_options or {}))
    limits = {method: BudgetLimits.for_method(method, max_total_input_tokens=5_000_000,
        max_total_output_tokens=2_000_000, max_single_output_tokens=1_000_000, max_context_tokens=2_000_000,
        max_public_tool_calls=100, max_active_seconds=600, max_eda_seconds=600,
        max_cpu_seconds=3600, max_memory_bytes=536_870_912) for method in METHODS}
    verdicts = verdicts or ControlledPublicVerdicts()
    identity = RuntimeIdentity("offline-fixture-campaign", "llm_gated_ffn", "fixture-cluster", None,
                               task.requirements["requirement_id"], "replicate-1")
    kwargs = dict(case="ffn", identity=identity, output_root=tmp_path / "control",
                  evaluator_root=tmp_path / "p", transport=transport, limits=limits,
                  backend=backend,
                  tool_limits=ToolLimits(timeout_seconds=10, cpu_seconds=10, memory_bytes=536_870_912),
                  schedule_seed=schedule_seed, evaluator_factory=verdicts.factory)
    runtime = PairedBlockRuntime(task, **kwargs)
    return runtime, transport, verdicts, task, kwargs


def test_shared_initial_dag_uses_six_actual_ten_attributed_calls_and_no_m3_builder(tmp_path, monkeypatch):
    runtime, transport, verdicts, _, _ = configured_runtime(tmp_path)
    built = []
    original = runtime_module.build_structure
    def observed_build(*args, **kwargs):
        built.append(runtime._active_operation)
        return original(*args, **kwargs)
    monkeypatch.setattr(runtime_module, "build_structure", observed_build)
    result = runtime.generate()
    assert transport.stage_counts == {"direct_project": 1, "pc_plan": 1, "behavior": 1,
                                       "project_from_pc": 1, "untyped_plan": 1, "project_from_plan": 1}
    assert built == ["initial-SB"]
    terminals = result["terminals"]
    assert terminals["M0"]["candidate"]["candidate_sha256"] == terminals["M1"]["candidate"]["candidate_sha256"]
    assert terminals["M4"]["candidate"]["candidate_sha256"] == terminals["M5"]["candidate"]["candidate_sha256"]
    pc_values = [terminals[method]["candidate"]["pc"] for method in ("M3", "M4", "M5")]
    assert pc_values[0] == pc_values[1] == pc_values[2]
    assert result["budget"]["actual"]["used"]["model_calls"] == 6
    assert sum(row["used"]["model_calls"] for row in result["budget"]["methods"].values()) == 10
    assert len(verdicts.calls) == 4
    assert all(call["visibility"] == "public" for call in verdicts.calls)
    assert result["source_class"] == "synthetic_fixture" and result["official"] is False
    for request in transport.requests:
        if request["stage"] in {"direct_project", "project_from_plan", "project_from_pc"}:
            payload = json.loads(request["messages"][-1]["content"])
            assert payload["project_proposal_schema"]["properties"]["contract_version"]["const"] == "pc21-project-proposal-v1"
            assert payload["project_manifest_schema"]["properties"]["contract_version"]["const"] == "project-package-v1"
            assert "required_units" not in payload and "build_plan_sha256" not in payload


def test_m1_noop_spends_a_call_then_transactional_patch_gets_real_recheck(tmp_path):
    def accepted(files):
        text = "\n".join(files.values())
        return "fixture-stage: direct_project" not in text or "M1 repaired fixture" in text
    runtime, transport, verdicts, _, _ = configured_runtime(tmp_path,
        verdicts=ControlledPublicVerdicts(accepted), transport_options={"m1_actions": ["noop", "patch"]})
    result = runtime.generate()
    old, new = result["terminals"]["M0"], result["terminals"]["M1"]
    assert old["public_evaluation"]["public"]["accepted"] is False
    assert new["public_evaluation"]["public"]["accepted"] is True
    assert transport.stage_counts["repair_M1"] == 2
    assert result["budget"]["methods"]["M1"]["used"]["model_calls"] == 3
    assert len(new["repairs"]) == 1 and new["repairs"][0]["public_rechecked"]
    assert new["candidate"]["parent_candidate_sha256"] == old["candidate"]["candidate_sha256"]
    assert new["candidate"]["candidate_sha256"] != old["candidate"]["candidate_sha256"]
    assert len(verdicts.calls) == 5
    repair_payloads = [json.loads(request["messages"][-1]["content"]) for request in transport.requests
                       if request["stage"] == "repair_M1"]
    assert all(payload["repair_proposal_schema"]["properties"]["contract_version"]["const"] == "pc21-repair-proposal-v1"
               for payload in repair_payloads)


def test_m1_can_replace_an_initially_invalid_incomplete_project(tmp_path):
    runtime, transport, _, _, _ = configured_runtime(tmp_path,
        transport_options={"invalid_direct": True, "m1_actions": ["project"]})
    result = runtime.generate()
    assert result["terminals"]["M0"]["candidate"] is None
    terminal = result["terminals"]["M1"]
    assert terminal["candidate"] is not None
    assert terminal["public_evaluation"]["public"]["accepted"] is True
    assert terminal["candidate"]["parent_candidate_sha256"] is None
    assert terminal["repairs"][0]["action"] == "replace_project"
    assert transport.stage_counts["repair_M1"] == 1
    assert result["budget"]["methods"]["M1"]["used"]["model_calls"] == 2


def test_m1_invalid_and_repeated_proposals_stop_at_four_calls_without_new_candidates(tmp_path):
    def accepted(files):
        return "fixture-stage: direct_project" not in "\n".join(files.values())
    runtime, transport, verdicts, _, _ = configured_runtime(tmp_path,
        verdicts=ControlledPublicVerdicts(accepted), transport_options={"m1_actions": ["invalid", "noop", "noop"]})
    result = runtime.generate()
    assert transport.stage_counts["repair_M1"] == 3
    assert result["budget"]["methods"]["M1"]["used"]["model_calls"] == 4
    assert result["terminals"]["M1"]["repairs"] == []
    assert result["terminals"]["M1"]["candidate"] == result["terminals"]["M0"]["candidate"]
    assert len(verdicts.calls) == 4


def test_m5_corrects_shared_invalid_pc_without_free_calls_or_backflow(tmp_path):
    runtime, transport, _, _, _ = configured_runtime(tmp_path,
        transport_options={"invalid_initial_pc": True, "m5_actions": ["correct_pc"]})
    result = runtime.generate()
    assert result["terminals"]["M3"]["candidate"] is None
    assert result["terminals"]["M4"]["candidate"] is None
    assert result["terminals"]["M5"]["candidate"] is not None
    assert result["terminals"]["M5"]["public_evaluation"]["public"]["accepted"] is True
    assert transport.stage_counts["pc_plan"] == 1 and "project_from_pc" not in transport.stage_counts
    assert transport.stage_counts["repair_M5"] == 1 and transport.stage_counts["behavior"] == 1
    assert result["budget"]["methods"]["M5"]["used"]["model_calls"] == 3
    assert result["budget"]["methods"]["M3"]["used"]["model_calls"] == 1
    assert result["budget"]["methods"]["M4"]["used"]["model_calls"] == 1


def test_m4_builder_failure_cannot_revoke_m3_shared_pc_admission(tmp_path, monkeypatch):
    runtime, transport, _, _, _ = configured_runtime(tmp_path)
    def builder_unavailable(*args, **kwargs):
        raise ValueError("synthetic structure construction failure")
    monkeypatch.setattr(runtime_module, "build_structure", builder_unavailable)
    result = runtime.generate()
    assert result["terminals"]["M3"]["candidate"] is not None
    assert result["terminals"]["M3"]["public_evaluation"]["public"]["accepted"] is True
    assert result["terminals"]["M4"]["candidate"] is None
    assert transport.stage_counts["project_from_pc"] == 1
    assert "behavior" not in transport.stage_counts
    assert result["budget"]["methods"]["M3"]["used"]["model_calls"] == 2


def test_m5_design_change_invalidates_all_units_and_keeps_old_complete_candidate_on_truncation(tmp_path):
    def accepted(files):
        return "fixture-stage:" in "\n".join(files.values())
    runtime, transport, _, _, _ = configured_runtime(tmp_path,
        verdicts=ControlledPublicVerdicts(accepted),
        transport_options={"m5_actions": ["design"], "fail_revised_body": True})
    result = runtime.generate()
    m4, m5 = result["terminals"]["M4"], result["terminals"]["M5"]
    assert m5["candidate"] == m4["candidate"]
    assert m5["candidate"]["pc"]["design"] == transport.design
    assert len(transport.body_requests) == 2
    old, revised = transport.body_requests
    assert old["build_plan_sha256"] != revised["build_plan_sha256"]
    assert set(old["required_units"]).isdisjoint(revised["required_units"])
    assert any(unit["module_id"] == "FfnGateUpRevised" for unit in revised["required_units"].values())
    assert result["budget"]["methods"]["M5"]["used"]["model_calls"] == 4
    assert m5["repairs"] == []


def test_m5_behavior_patch_preserves_pc_plan_and_structural_bytes(tmp_path):
    def accepted(files):
        text = "\n".join(files.values())
        return "fixture-stage:" in text or "M5 repaired fixture" in text
    runtime, transport, verdicts, _, _ = configured_runtime(tmp_path,
        verdicts=ControlledPublicVerdicts(accepted), transport_options={"m5_actions": ["body"]})
    result = runtime.generate()
    before = result["terminals"]["M4"]["candidate"]
    after = result["terminals"]["M5"]["candidate"]
    assert result["terminals"]["M5"]["public_evaluation"]["public"]["accepted"] is True
    assert before["pc"] == after["pc"] and before["build"] == after["build"]
    assert after["parent_candidate_sha256"] == before["candidate_sha256"]
    assert before["files"]["rtl/top.sv"] == after["files"]["rtl/top.sv"]
    assert before["files"]["manifest.json"] == after["files"]["manifest.json"]
    changed = [path for path in before["files"] if before["files"][path] != after["files"][path]]
    assert len(changed) == 1 and changed[0].startswith("rtl/")
    assert transport.stage_counts["repair_M5"] == 1
    assert result["budget"]["methods"]["M5"]["used"]["model_calls"] == 3
    assert len(result["terminals"]["M5"]["repairs"]) == 1
    assert len(verdicts.calls) == 5


def test_generation_resume_is_read_only_and_does_not_reset_or_dispatch(tmp_path):
    runtime, transport, _, task, kwargs = configured_runtime(tmp_path)
    first = runtime.generate()
    count = len(transport.requests)
    assert runtime.generate() == first
    reopened = PairedBlockRuntime(task, **kwargs)
    assert reopened.generate() == first
    assert len(transport.requests) == count == 6
    assert reopened.ledger.remaining("M0", "model_calls") == 0
    assert reopened.ledger.remaining("M1", "model_calls") == 3


def test_partial_shared_node_checkpoint_resumes_without_reissuing_direct(tmp_path, monkeypatch):
    runtime, transport, _, task, kwargs = configured_runtime(tmp_path, schedule_seed=0)
    original = runtime._cached
    def interrupted_after_commit(operation, consumers, action):
        value = original(operation, consumers, action)
        if operation == "initial-SD":
            raise RuntimeError("synthetic_controller_crash_after_node_commit")
        return value
    monkeypatch.setattr(runtime, "_cached", interrupted_after_commit)
    with pytest.raises(RuntimeError, match="synthetic_controller_crash"):
        runtime.generate()
    assert transport.stage_counts["direct_project"] == 1
    assert runtime.ledger.remaining("M0", "model_calls") == 0
    assert runtime.ledger.remaining("M1", "model_calls") == 3
    reopened = PairedBlockRuntime(task, **kwargs)
    result = reopened.generate()
    assert transport.stage_counts["direct_project"] == 1
    assert len(transport.requests) == 6
    assert result["budget"]["actual"]["used"]["model_calls"] == 6
    assert result["terminals"]["M0"]["candidate"] == result["terminals"]["M1"]["candidate"]


def test_public_failure_feedback_never_contains_private_evaluator_material(tmp_path):
    def accepted(files):
        return "fixture-stage: direct_project" not in "\n".join(files.values())
    runtime, transport, _, _, _ = configured_runtime(tmp_path,
        verdicts=ControlledPublicVerdicts(accepted), transport_options={"m1_actions": ["invalid", "noop", "noop"]})
    runtime.generate()
    serialized = json.dumps(transport.requests)
    assert PRIVATE_CANARY not in serialized
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for key, nested in value.items():
                yield str(key)
                yield from strings(nested)
        elif isinstance(value, (tuple, list)):
            for nested in value:
                yield from strings(nested)
    decoded_payloads = [json.loads(request["messages"][-1]["content"]) for request in transport.requests]
    visible_strings = list(strings(decoded_payloads))
    assert not any(str(runtime.private_root) in value or runtime.private_root.as_posix() in value
                   for value in visible_strings)
    assert not any(str(runtime.root) in value or runtime.root.as_posix() in value for value in visible_strings)
    repair = [request for request in transport.requests if request["stage"] == "repair_M1"]
    assert repair and "functional_mismatch" in json.dumps(repair[0])
    assert all("private_record_ref" not in json.dumps(request) for request in transport.requests)
    with pytest.raises(PermissionError, match="sealed"):
        runtime._call("after-seal", "direct_project", ("M1",), {}, "Return project")


def test_runtime_rejects_cross_case_family_identity_before_any_dispatch(tmp_path):
    runtime, transport, _, task, kwargs = configured_runtime(tmp_path)
    mismatched = {**kwargs, "identity": replace(runtime.identity, family_id="llm_kv_cache_decode_attention"),
                  "output_root": tmp_path / "wrong-case-control", "evaluator_root": tmp_path / "wrong-case-private"}
    with pytest.raises(ValueError, match="family"):
        PairedBlockRuntime(task, **mismatched)
    assert transport.requests == []


@pytest.mark.parametrize("status,exit_code", [("missing_tool", None), ("failed", 3221225477)])
def test_composition_infrastructure_failure_stops_model_repair_without_design_failure_credit(tmp_path, status, exit_code):
    class FaultBackend:
        isolation_qualified = False

        def policy(self):
            return {"backend": "synthetic-composition-fault", "fault_status": status, "exit_code": exit_code}

        def run(self, command, cwd, stage, limits):
            return ToolResult(stage, command, status, exit_code, "", "synthetic tool unavailable/crash", 0.01)
    runtime, transport, _, _, _ = configured_runtime(tmp_path, backend=FaultBackend())
    result = runtime.generate()
    assert result["terminals"]["M3"]["candidate"] is not None
    for method in ("M4", "M5"):
        assert result["terminals"][method]["candidate"] is None
        assert result["terminals"][method]["infrastructure"] is True
        assert result["terminals"][method]["reason"]["reason"] == "tool_infrastructure_error"
    assert transport.stage_counts["behavior"] == 1
    assert "repair_M5" not in transport.stage_counts
    assert result["budget"]["methods"]["M5"]["used"]["model_calls"] == 2
