import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINING_ROOT = REPO_ROOT / "training"
PYPROJECT = TRAINING_ROOT / "pyproject.toml"
SOURCE_ROOT = TRAINING_ROOT / "src"


def _requirement_name(requirement: str) -> str:
    for separator in ("<", ">", "=", "!", "~", "["):
        requirement = requirement.split(separator, 1)[0]
    return requirement.strip().lower()


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_training_project_metadata_and_entry_points() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = metadata["project"]

    assert project["name"] == "sr2fpga-training"
    assert project["requires-python"] == ">=3.11"
    assert {
        _requirement_name(requirement) for requirement in project["dependencies"]
    } == {"pyyaml"}

    extras = project["optional-dependencies"]
    assert {
        _requirement_name(requirement) for requirement in extras["train"]
    } == {
        "accelerate",
        "bitsandbytes",
        "datasets",
        "peft",
        "torch",
        "transformers",
        "trl",
    }
    assert {
        _requirement_name(requirement) for requirement in extras["serve"]
    } == {"vllm"}
    assert {
        _requirement_name(requirement) for requirement in extras["dev"]
    } == {"pytest"}

    assert project["scripts"] == {
        "sr2fpga-prepare-dataset": "sr2fpga_training.prepare_dataset:main",
        "sr2fpga-training-dry-run": "sr2fpga_training.training_dry_run:main",
        "sr2fpga-train-lora": "sr2fpga_training.train_lora:main",
        "sr2fpga-merge-lora": "sr2fpga_training.merge_lora:main",
    }


def test_training_source_has_no_agent_or_legacy_imports() -> None:
    forbidden = {"sr2fpga_agent", "LLM"}
    violations: dict[str, list[str]] = {}

    for path in SOURCE_ROOT.rglob("*.py"):
        found = sorted(_import_roots(path) & forbidden)
        if found:
            violations[str(path.relative_to(REPO_ROOT))] = found

    assert violations == {}


def test_lightweight_modules_do_not_eagerly_import_heavy_backends() -> None:
    script = """
import importlib
import json
import sys

for module_name in (
    "sr2fpga_training.prepare_dataset",
    "sr2fpga_training.training_dry_run",
):
    importlib.import_module(module_name)

heavy = {
    "accelerate",
    "bitsandbytes",
    "datasets",
    "peft",
    "torch",
    "transformers",
    "trl",
    "vllm",
}
print(json.dumps(sorted(heavy.intersection(sys.modules))))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(SOURCE_ROOT),
                    os.environ.get("PYTHONPATH", ""),
                ]
            ),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []
