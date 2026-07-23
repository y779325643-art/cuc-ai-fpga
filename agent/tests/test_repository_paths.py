from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def repository_api():
    from sr2fpga_agent.repository_paths import (
        RepositoryPaths,
        discover_repository_root,
    )

    return RepositoryPaths, discover_repository_root


def create_repository_marker(root: Path) -> None:
    contracts = root / "contracts"
    contracts.mkdir(parents=True)
    (contracts / "manifest.json").write_text("{}\n", encoding="utf-8")


def test_environment_override_has_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, discover_repository_root = repository_api()
    override_root = tmp_path / "override"
    create_repository_marker(override_root)
    monkeypatch.setenv("SR2FPGA_REPO_ROOT", str(override_root))

    assert discover_repository_root(REPO_ROOT) == override_root.resolve()


def test_upward_discovery_from_agent_source() -> None:
    _, discover_repository_root = repository_api()
    nested_start = REPO_ROOT / "agent" / "src" / "nested" / "location"
    assert discover_repository_root(nested_start) == REPO_ROOT


def test_discovery_rejects_missing_contract_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, discover_repository_root = repository_api()
    monkeypatch.delenv("SR2FPGA_REPO_ROOT", raising=False)
    start = tmp_path / "no-repository" / "nested"
    start.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="contracts/manifest.json"):
        discover_repository_root(start)


def test_environment_override_rejects_missing_contract_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, discover_repository_root = repository_api()
    monkeypatch.setenv("SR2FPGA_REPO_ROOT", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="SR2FPGA_REPO_ROOT"):
        discover_repository_root(REPO_ROOT)


def test_repository_paths_expose_owned_resources(tmp_path: Path) -> None:
    RepositoryPaths, _ = repository_api()
    paths = RepositoryPaths.discover(REPO_ROOT / "agent" / "src")

    assert paths.root == REPO_ROOT
    assert paths.contracts_dir == REPO_ROOT / "contracts"
    assert paths.task_catalog == (
        REPO_ROOT
        / "contracts"
        / "task-catalog"
        / "sr2fpga-task-catalog-v0.2.json"
    )
    assert paths.agent_scripts_dir == REPO_ROOT / "agent" / "scripts"
    assert paths.artifacts_dir == REPO_ROOT / "artifacts"
    assert paths.reports_dir == REPO_ROOT / "reports"
    assert paths.datasets_dir == REPO_ROOT / "datasets"
    with pytest.raises(FrozenInstanceError):
        paths.root = tmp_path  # type: ignore[misc]


def test_default_discovery_does_not_treat_cwd_as_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, discover_repository_root = repository_api()
    fake_root = tmp_path / "fake-repository"
    create_repository_marker(fake_root)
    monkeypatch.chdir(fake_root)
    monkeypatch.delenv("SR2FPGA_REPO_ROOT", raising=False)

    assert discover_repository_root() == REPO_ROOT
