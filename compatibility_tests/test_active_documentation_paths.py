from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_ACTIVE_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/README.md"),
    Path("docs/current-status.md"),
)
ADDITIONAL_ACTIVE_DOCS = (
    Path("agent/README.md"),
    Path("training/README.md"),
    Path("contracts/README.md"),
    Path("datasets/README.md"),
    Path("agent/configs/README.md"),
    Path("agent/configs/archive/README.md"),
    Path("agent/configs/legacy/README.md"),
    Path("training/configs/README.md"),
    Path("agent/scripts/README.md"),
    Path("training/scripts/README.md"),
    Path("reports/evidence/task-ledger/sr2fpga-task-evidence-status.md"),
)

OLD_PRIMARY_COMMANDS = (
    re.compile(r"python(?:3)?\s+-m\s+LLM\.src"),
    re.compile(r"python(?:3)?\s+LLM/src"),
    re.compile(r"(?m)^\s*[-*]?\s*`LLM/scripts/"),
    re.compile(r"(?<!agent/)configs/current/"),
)


def _read(path: Path) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_core_active_docs_define_canonical_project_ownership() -> None:
    for path in CORE_ACTIVE_DOCS:
        source = _read(path)
        with_path = f"{path}: {source}"
        assert "agent/" in source, with_path
        assert "training/" in source, with_path
        assert "contracts/" in source, with_path
        assert "datasets/" in source, with_path
        assert "artifacts/" in source, with_path


def test_active_docs_do_not_present_legacy_paths_as_primary_commands() -> None:
    for path in (*CORE_ACTIVE_DOCS, *ADDITIONAL_ACTIVE_DOCS):
        source = _read(path)
        for pattern in OLD_PRIMARY_COMMANDS:
            assert pattern.search(source) is None, (
                f"{path} presents a legacy path as current: {pattern.pattern}"
            )


def test_active_docs_state_cross_project_and_verdict_rules() -> None:
    corpus = re.sub(r"\s+", " ", "\n".join(_read(path) for path in CORE_ACTIVE_DOCS))

    assert "Training does not import Agent" in corpus
    assert "`not_run` is not a failure" in corpus


def test_retired_compatibility_surfaces_are_absent() -> None:
    assert not (REPO_ROOT / "LLM").exists()
    assert not (REPO_ROOT / "docs/migration/llm-to-agent-training.md").exists()


def test_agents_is_the_only_repository_agent_guidance() -> None:
    agents = _read(Path("AGENTS.md"))
    docs_index = _read(Path("docs/README.md"))

    assert "This file guides repository development agents" in agents
    assert "docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md" in agents
    assert "not frozen" in agents
    assert "[Coding-agent guidance](../AGENTS.md)" in docs_index
    assert not (REPO_ROOT / "CLAUDE.md").exists()


def test_markdown_links_in_core_active_docs_resolve() -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for path in CORE_ACTIVE_DOCS:
        source_path = REPO_ROOT / path
        for target in link_pattern.findall(_read(path)):
            if "://" in target or target.startswith("#"):
                continue
            local_target = target.split("#", 1)[0]
            if not local_target:
                continue
            resolved = (source_path.parent / local_target).resolve()
            assert resolved.exists(), f"{path}: broken link {target}"
