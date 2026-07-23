import ast
from pathlib import Path
import re
import subprocess

import yaml

from sr2fpga_agent.runner import load_runner_config


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = REPO_ROOT / "agent" / "configs"
CURRENT_ROOT = CONFIG_ROOT / "current"
SCRIPT_ROOT = REPO_ROOT / "agent" / "scripts"
OUTPUT_KEYS = {
    "checkpoint_dir",
    "dataset_root",
    "export_root",
    "output_dir",
    "output_root",
    "run_root",
}
MOVED_SCRIPTS = {
    "analyze_phase_d_h2_failures.py",
    "audit_phase_d_pilot.py",
    "openxc7_pnr.sh",
}


def _walk_values(value: object, keys: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_values(item, (*keys, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_values(item, (*keys, str(index)))
    else:
        yield keys, value


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_agent_configs_and_scripts_have_canonical_owners() -> None:
    assert CURRENT_ROOT.is_dir()
    assert SCRIPT_ROOT.is_dir()
    assert not (REPO_ROOT / "configs").exists()
    for script_name in MOVED_SCRIPTS:
        assert (SCRIPT_ROOT / script_name).is_file()
        assert not (REPO_ROOT / "scripts" / script_name).exists()


def test_active_configs_resolve_and_write_only_under_agent_artifacts() -> None:
    config_paths = sorted(CURRENT_ROOT.glob("*.yaml"))
    assert config_paths

    for path in config_paths:
        load_runner_config(path)
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        for keys, value in _walk_values(payload):
            if not keys or keys[-1] not in OUTPUT_KEYS or value is None:
                continue
            assert isinstance(value, str), f"{path.name}:{'.'.join(keys)}"
            normalized = value.replace("\\", "/")
            assert normalized.startswith("artifacts/agent/"), (
                f"{path.name}:{'.'.join(keys)} uses active output {value!r}"
            )


def test_agent_python_scripts_use_only_canonical_agent_namespace() -> None:
    imported = {
        module
        for path in SCRIPT_ROOT.glob("*.py")
        for module in _imported_modules(path)
    }
    assert not any(module == "LLM" or module.startswith("LLM.") for module in imported)


def test_archive_and_legacy_configs_are_labeled_non_default() -> None:
    archive_readme = (CONFIG_ROOT / "archive" / "README.md").read_text(
        encoding="utf-8"
    )
    legacy_readme = (CONFIG_ROOT / "legacy" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "not executed by default" in archive_readme
    assert "compatibility-only" in legacy_readme


def test_openxc7_wrapper_is_executable_in_git() -> None:
    relative_path = "agent/scripts/openxc7_pnr.sh"
    completed = subprocess.run(
        ["git", "ls-files", "-s", "--", relative_path],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.startswith("100755 ")


def test_openxc7_wrapper_has_no_machine_specific_default_path() -> None:
    source = (SCRIPT_ROOT / "openxc7_pnr.sh").read_text(encoding="utf-8")

    assert re.search(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]", source) is None
    assert re.search(r"/mnt/[A-Za-z]/", source) is None
    assert re.search(r"/home/[^/\s]+/", source) is None
    assert 'flake_path="${OPENXC7_FLAKE_PATH:-}"' in source
