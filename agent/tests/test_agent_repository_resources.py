import importlib
import os
from pathlib import Path

import pytest

from sr2fpga_agent import agent as agent_module
from sr2fpga_agent import task_catalog, task_evidence
from sr2fpga_agent.repository_paths import RepositoryPaths


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repository_paths_expose_agent_runtime_and_evidence_resources() -> None:
    paths = RepositoryPaths.discover()
    assert paths.agent_artifacts_dir == REPO_ROOT / "artifacts" / "agent"
    assert paths.task_evidence == (
        REPO_ROOT / "docs" / "sr2fpga-task-evidence-v0.1.json"
    )


def test_task_catalog_and_evidence_use_canonical_repository_paths() -> None:
    paths = RepositoryPaths.discover()
    assert task_catalog.CATALOG_PATH == paths.task_catalog
    assert task_evidence.EVIDENCE_PATH == paths.task_evidence
    assert task_evidence._resolve_evidence_ref("datasets/example/metadata.json") == (
        REPO_ROOT / "datasets" / "example" / "metadata.json"
    )


def test_openxc7_wrapper_resolves_under_agent_scripts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = REPO_ROOT / "agent" / "scripts" / "openxc7_pnr.sh"
    original_is_file = Path.is_file
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: path == expected or original_is_file(path),
    )

    command = agent_module._default_openxc7_command_prefix()

    if os.name == "nt":
        assert command == [
            "wsl",
            "bash",
            agent_module._windows_path_to_wsl(expected),
        ]
    else:
        assert command == ["bash", str(expected)]


def test_repository_resources_ignore_process_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    reloaded_catalog = importlib.reload(task_catalog)
    reloaded_evidence = importlib.reload(task_evidence)

    assert reloaded_catalog.CATALOG_PATH == (
        REPO_ROOT
        / "contracts"
        / "task-catalog"
        / "sr2fpga-task-catalog-v0.2.json"
    )
    assert reloaded_evidence.EVIDENCE_PATH == (
        REPO_ROOT / "docs" / "sr2fpga-task-evidence-v0.1.json"
    )


def test_repository_resource_modules_do_not_use_parent_indexing() -> None:
    for path in (
        REPO_ROOT / "agent" / "src" / "sr2fpga_agent" / "agent.py",
        REPO_ROOT / "agent" / "src" / "sr2fpga_agent" / "task_catalog.py",
        REPO_ROOT / "agent" / "src" / "sr2fpga_agent" / "task_evidence.py",
    ):
        assert "parents[" not in path.read_text(encoding="utf-8"), path.name
