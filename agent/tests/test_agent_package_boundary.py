import ast
import importlib
from pathlib import Path
import re
import sys
import tomllib

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = REPO_ROOT / "agent" / "pyproject.toml"
PACKAGE_ROOT = REPO_ROOT / "agent" / "src" / "sr2fpga_agent"
HEAVY_TRAINING_DEPENDENCIES = {
    "torch",
    "transformers",
    "datasets",
    "peft",
    "trl",
    "bitsandbytes",
    "accelerate",
    "vllm",
}
EXPECTED_SCRIPTS = {
    "sr2fpga-agent": "sr2fpga_agent.cli:main",
    "sr2fpga-runner": "sr2fpga_agent.runner:main",
    "sr2fpga-baseline-report": "sr2fpga_agent.baseline_report:main",
    "sr2fpga-req2file-eval": "sr2fpga_agent.req2file_eval:main",
    "sr2fpga-task-evidence": "sr2fpga_agent.task_evidence:main",
}
EXPLICIT_AGENT_TESTS = {
    "test_req2file_eval.py",
    "test_analyze_phase_d_h2_failures.py",
    "test_sr2fpga_measurement_freeze.py",
    "test_sr2fpga_paired_measurement.py",
    "test_sr2fpga_phase_d_audit.py",
    "test_sr2fpga_phase_d_integration.py",
    "test_sr2fpga_task_catalog_v02.py",
    "test_sr2fpga_task_evidence_v01.py",
}


def load_pyproject() -> dict:
    with PYPROJECT_PATH.open("rb") as stream:
        return tomllib.load(stream)


def dependency_name(requirement: str) -> str:
    return re.split(r"[<>=!~\s\[]", requirement, maxsplit=1)[0].lower()


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_agent_pyproject_declares_lightweight_runtime() -> None:
    project = load_pyproject()["project"]
    assert project["name"] == "sr2fpga-agent"
    assert project["requires-python"] == ">=3.11"
    dependencies = {dependency_name(item) for item in project["dependencies"]}
    assert {"pyyaml", "certifi"} <= dependencies
    assert dependencies.isdisjoint(HEAVY_TRAINING_DEPENDENCIES)


def test_agent_pyproject_declares_canonical_console_scripts() -> None:
    assert load_pyproject()["project"]["scripts"] == EXPECTED_SCRIPTS


def test_canonical_agent_source_has_no_training_or_legacy_imports() -> None:
    assert PACKAGE_ROOT.is_dir()
    modules = {
        module
        for path in PACKAGE_ROOT.rglob("*.py")
        for module in imported_modules(path)
    }
    top_level_modules = {module.split(".", maxsplit=1)[0] for module in modules}
    assert top_level_modules.isdisjoint(HEAVY_TRAINING_DEPENDENCIES)
    assert not any(module == "LLM" or module.startswith("LLM.") for module in modules)


def test_legacy_namespace_warns_and_resolves_canonical_source() -> None:
    for module_name in tuple(sys.modules):
        if module_name == "LLM.src.sr2fpga_agent" or module_name.startswith(
            "LLM.src.sr2fpga_agent."
        ):
            sys.modules.pop(module_name)

    with pytest.warns(DeprecationWarning, match="canonical import is sr2fpga_agent"):
        legacy_package = importlib.import_module("LLM.src.sr2fpga_agent")
    legacy_runner = importlib.import_module("LLM.src.sr2fpga_agent.runner")
    legacy_oracle_types = importlib.import_module(
        "LLM.src.sr2fpga_agent.oracles.types"
    )
    canonical_package = importlib.import_module("sr2fpga_agent")
    canonical_oracle_types = importlib.import_module(
        "sr2fpga_agent.oracles.types"
    )

    assert legacy_package.ProjectRequest is canonical_package.ProjectRequest
    assert Path(legacy_runner.__file__).resolve().is_relative_to(PACKAGE_ROOT)
    assert (
        legacy_oracle_types.OracleScenarioSpec
        is canonical_oracle_types.OracleScenarioSpec
    )


def test_agent_owned_tests_live_only_in_agent_project() -> None:
    legacy_test_root = REPO_ROOT / "LLM" / "tests"
    remaining = {
        path.name
        for path in legacy_test_root.glob("test_*.py")
        if path.name.startswith("test_sr2fpga_agent_")
        or path.name in EXPLICIT_AGENT_TESTS
    }
    assert not remaining


def test_canonical_agent_tests_do_not_import_legacy_namespace() -> None:
    imported = {
        module
        for path in (REPO_ROOT / "agent" / "tests").glob("test_*.py")
        for module in imported_modules(path)
    }
    assert not any(module == "LLM" or module.startswith("LLM.") for module in imported)


def test_agent_implementation_has_one_source_of_truth() -> None:
    source_roots = (
        REPO_ROOT / "agent" / "src",
        REPO_ROOT / "LLM" / "src",
        REPO_ROOT / "training" / "src",
    )
    for filename in ("agent.py", "runner.py", "recorder.py"):
        matches = [
            path.resolve()
            for root in source_roots
            if root.is_dir()
            for path in root.rglob(filename)
        ]
        assert matches == [(PACKAGE_ROOT / filename).resolve()]
