import ast
from pathlib import Path
import re

from sr2fpga_agent.repository_paths import (
    discover_repository_root as discover_agent_root,
)
from sr2fpga_training.contracts import (
    discover_repository_root as discover_training_root,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_SOURCE = REPO_ROOT / "agent" / "src" / "sr2fpga_agent"
TRAINING_SOURCE = REPO_ROOT / "training" / "src" / "sr2fpga_training"
LEGACY_SOURCE = REPO_ROOT / "LLM" / "src"

HEAVY_ML_IMPORTS = {
    "accelerate",
    "bitsandbytes",
    "datasets",
    "peft",
    "torch",
    "transformers",
    "trl",
    "vllm",
}
PRIVATE_VALUE_PATTERNS = (
    re.compile(r"(?i)(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![<\[])"),
    re.compile(r"/mnt/[A-Za-z]/(?:Users/)?[^/\s`\"'<>|]+/"),
    re.compile(r"/home/[^/\s`\"'<>|]+/"),
    re.compile(r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9]{8,}"),
)


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _source_violations(
    source_root: Path,
    forbidden_imports: set[str],
) -> dict[str, list[str]]:
    violations: dict[str, list[str]] = {}
    for path in source_root.rglob("*.py"):
        found = sorted(_import_roots(path) & forbidden_imports)
        if found:
            violations[str(path.relative_to(REPO_ROOT))] = found
    return violations


def _private_value_violations(source_root: Path) -> list[str]:
    violations: list[str] = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        values = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        if any(
            pattern.search(value)
            for value in values
            for pattern in PRIVATE_VALUE_PATTERNS
        ):
            violations.append(str(path.relative_to(REPO_ROOT)))
    return violations


def test_agent_does_not_depend_on_training_or_heavy_ml_stack() -> None:
    forbidden = {"sr2fpga_training", "training"} | HEAVY_ML_IMPORTS
    assert _source_violations(AGENT_SOURCE, forbidden) == {}


def test_training_does_not_depend_on_agent_or_legacy_namespace() -> None:
    assert _source_violations(
        TRAINING_SOURCE,
        {"sr2fpga_agent", "LLM"},
    ) == {}


def test_both_projects_discover_the_versioned_contract_registry() -> None:
    manifest = REPO_ROOT / "contracts" / "manifest.json"
    assert manifest.is_file()
    assert discover_agent_root(AGENT_SOURCE) == REPO_ROOT
    assert discover_training_root(TRAINING_SOURCE) == REPO_ROOT


def test_canonical_source_contains_no_private_paths_or_keys() -> None:
    assert _private_value_violations(AGENT_SOURCE) == []
    assert _private_value_violations(TRAINING_SOURCE) == []


def test_legacy_source_contains_compatibility_shim_only() -> None:
    python_files = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in LEGACY_SOURCE.rglob("*.py")
    )
    assert python_files == ["LLM/src/sr2fpga_agent/__init__.py"]
