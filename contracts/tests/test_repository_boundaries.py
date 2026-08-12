from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read_root_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_repository_project_directories_have_readmes() -> None:
    for directory in ("agent", "training", "contracts", "artifacts", "reports"):
        project_root = REPO_ROOT / directory
        assert project_root.is_dir(), f"missing repository directory: {directory}/"
        assert (project_root / "README.md").is_file(), (
            f"missing ownership document: {directory}/README.md"
        )


def test_runtime_and_local_config_paths_are_root_scoped_ignores() -> None:
    ignore_lines = {
        line.strip()
        for line in read_root_file(".gitignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert {
        "/artifacts/*",
        "!/artifacts/README.md",
        "/tmp/",
        "/agent/configs/local/",
        "/training/configs/local/",
    } <= ignore_lines
    assert {
        "LLM/runs/",
        "LLM/data/*.jsonl",
        "LLM/merged/",
        "LLM/checkpoints/",
        "configs/*.local.yaml",
        "configs/local/",
    }.isdisjoint(ignore_lines)


def test_datasets_and_reports_are_not_globally_ignored() -> None:
    ignore_lines = {
        line.strip()
        for line in read_root_file(".gitignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "/datasets/" not in ignore_lines
    assert "datasets/" not in ignore_lines
    assert "/reports/" not in ignore_lines
    assert "reports/" not in ignore_lines
