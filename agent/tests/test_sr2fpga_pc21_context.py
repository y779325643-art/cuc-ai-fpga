"""Typed public-source admission, actual byte identity and saved call ceilings."""

import json
import subprocess
import sys
import uuid
from dataclasses import replace

import pytest

from sr2fpga_agent.artifact_store import BudgetReservationError
from sr2fpga_agent.pc.context import check_task_design, load_public_task
from sr2fpga_agent.pc.development import DevelopmentSession, prepare_dw_pw
from sr2fpga_agent.pc.inputs import ParseLimits, TrustedSource, assemble_project_contract
from sr2fpga_agent.tasks.ai_dw_pw import reference_design
from sr2fpga_agent.repository_paths import RepositoryPaths


def test_public_task_resolves_reference_and_exact_assets(tmp_path):
    session = prepare_dw_pw(tmp_path / "run", max_model_calls=0)
    task = session.load_task()
    checked = check_task_design(reference_design(), task)
    assert checked.instances["self"].port_widths == {"rx": 18, "tx": 18}
    assert task.asset_bytes
    assert "algorithm_correctness" in checked.deferred_checks
    asset = task.requirements["public_assets"][0]
    (session.root / "public" / asset["path"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="size mismatch|byte binding"):
        session.load_task()


@pytest.mark.parametrize("change,match", [
    (lambda d: d["fact_records"].append(d["fact_records"][0]), "duplicate public fact"),
    (lambda d: d["public_assets"][0].update(path="../private.json"), "unsafe project file path"),
    (lambda d: d["public_assets"][0].update(path="C:/secret"), "unsafe project file path"),
    (lambda d: d.update(analysis_population="official"), "development"),
])
def test_context_rejects_ambiguity_escape_and_official_scope(tmp_path, change, match):
    session = prepare_dw_pw(tmp_path / "run", max_model_calls=0)
    task = session.load_task()
    data = json.loads(task.sources.requirements.content)
    change(data)
    sources = replace(task.sources, requirements=TrustedSource("requirements", json.dumps(data).encode()))
    with pytest.raises(ValueError, match=match):
        load_public_task(sources, asset_root=session.root / "public", limits=ParseLimits(1_000_000, 128))


def test_call_budget_survives_reopen_and_failed_response(tmp_path):
    session = prepare_dw_pw(tmp_path / "run", max_model_calls=2)
    assert session.reserve_call("design", "public prompt") == 1
    session.record_response(1, "invalid json is still a spent call", transport_identity="offline-test")
    reopened = DevelopmentSession(session.root)
    assert reopened.reserve_call("design", "public correction") == 2
    with pytest.raises(BudgetReservationError):
        DevelopmentSession(session.root).reserve_call("behavior", "third call")
    with pytest.raises(ValueError, match="reserved"):
        reopened.record_response(3, "unreserved", transport_identity="offline-test")


def test_preparation_preserves_existing_run(tmp_path):
    root = tmp_path / "run"
    prepare_dw_pw(root, max_model_calls=0)
    original = (root / "public" / "requirements.json").read_bytes()
    with pytest.raises(ValueError, match="fresh"):
        prepare_dw_pw(root)
    assert (root / "public" / "requirements.json").read_bytes() == original


def test_session_rejects_changed_frozen_public_requirements(tmp_path):
    session = prepare_dw_pw(tmp_path / "run", max_model_calls=0)
    source = session.root / "public" / "requirements.json"
    payload = json.loads(source.read_bytes())
    payload["public_text"] = "changed task"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen public source bytes changed"):
        DevelopmentSession(session.root).load_task()


def test_typed_public_cli_validates_and_builds_actual_reference(tmp_path):
    session = prepare_dw_pw(tmp_path / "run", max_model_calls=0)
    task = session.load_task()
    pc = assemble_project_contract(json.dumps(reference_design()).encode(), task.sources,
                                   limits=ParseLimits(1_000_000, 128))
    source = tmp_path / "pc.json"
    source.write_text(json.dumps(pc), encoding="utf-8")
    args = ["--input", str(source), "--asset-root", str(session.root / "public"),
            "--max-bytes", "1000000", "--max-depth", "128"]
    for name in ("requirements", "target-profile", "capability-profile"):
        args += ["--" + name, str(session.root / "public" / (name + ".json")), "--" + name + "-id", name]
    result = subprocess.run([sys.executable, "-B", "-m", "sr2fpga_agent.pc", "validate", *args],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["semantic_validation"] == "pass"
    assert receipt["functional_correctness"] == "not_evaluated"
    assert "algorithm_correctness" in receipt["deferred_checks"]
    # Exercise the production containment rule even with an external pytest tmp.
    output = RepositoryPaths.discover().root / "artifacts" / "pc21-cli-tests" / uuid.uuid4().hex
    command = [sys.executable, "-B", "-m", "sr2fpga_agent.pc", "build", *args, "--output", str(output)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert built.returncode == 0, built.stderr
    assert (output / "build-plan.json").is_file()
    assert json.loads(built.stdout)["rtl_construction"] == "structure_only_behavior_required"
    assert subprocess.run(command, capture_output=True, timeout=20).returncode == 2
    pc["design"]["modules"]["AiDwPwDev"]["implementation"]["nets"].pop("output")
    source.write_text(json.dumps(pc), encoding="utf-8")
    rejected = subprocess.run([sys.executable, "-B", "-m", "sr2fpga_agent.pc", "validate", *args],
                              capture_output=True, text=True, timeout=20)
    assert rejected.returncode == 2


def test_context_cannot_mutate_projection_under_old_binding(tmp_path):
    task = prepare_dw_pw(tmp_path / "run", max_model_calls=0).load_task()
    task.boundary["rtl_top"] = "ChangedTop"
    with pytest.raises(ValueError, match="projection differs"):
        check_task_design(reference_design(), task)
