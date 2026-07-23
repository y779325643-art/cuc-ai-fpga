import ast
from pathlib import Path
import re

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINING_ROOT = REPO_ROOT / "training"
CONFIG_ROOT = TRAINING_ROOT / "configs"
SCRIPT_ROOT = TRAINING_ROOT / "scripts"

EXPECTED_CONFIGS = {
    "serve_vllm.env.example",
    "train_lora.example.yaml",
    "train_qwen_req2file_short.example.yaml",
    "train_qwen_smoke.example.yaml",
}
EXPECTED_SCRIPTS = {
    "merge_lora.sh",
    "serve_qwen_vllm.sh",
    "serve_vllm.sh",
    "setup_server.sh",
    "test_api.sh",
    "test_gemma_transformers.py",
    "train_lora.sh",
}

PRIVATE_PATH_PATTERNS = (
    re.compile(r"/mnt/[A-Za-z]/(?:Users/)?[^/\s`\"'<>|]+"),
    re.compile(r"(?i)(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![<\[])"),
    re.compile(r"sk-[A-Za-z0-9]"),
)


def _all_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


def test_expected_training_configs_and_scripts_are_canonical() -> None:
    assert {path.name for path in CONFIG_ROOT.iterdir() if path.is_file()} >= (
        EXPECTED_CONFIGS | {"README.md"}
    )
    assert {path.name for path in SCRIPT_ROOT.iterdir() if path.is_file()} >= (
        EXPECTED_SCRIPTS | {"README.md"}
    )


def test_committed_training_assets_contain_no_private_paths_or_keys() -> None:
    violations: list[str] = []
    paths = [
        *CONFIG_ROOT.rglob("*"),
        *SCRIPT_ROOT.rglob("*"),
    ]
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(text):
                violations.append(str(path.relative_to(REPO_ROOT)))
                break

    assert violations == []


def test_training_config_outputs_are_ignored_artifacts() -> None:
    for path in CONFIG_ROOT.glob("*.yaml"):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        assert str(config["train_file"]).startswith(
            "artifacts/training/prepared-data/"
        )
        assert str(config["output_dir"]).startswith(
            "artifacts/training/adapters/"
        )
        model = str(config["model_name_or_path"])
        assert not any(pattern.search(model) for pattern in PRIVATE_PATH_PATTERNS)


def test_local_training_config_overrides_are_ignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "training/configs/local/" in gitignore


def test_shell_scripts_use_training_owned_overrides_and_modules() -> None:
    runtime_scripts = {
        path.name: path.read_text(encoding="utf-8")
        for path in SCRIPT_ROOT.glob("*.sh")
    }
    for name in (
        "setup_server.sh",
        "serve_qwen_vllm.sh",
        "serve_vllm.sh",
        "train_lora.sh",
        "merge_lora.sh",
    ):
        assert "TRAINING_VENV_PATH" in runtime_scripts[name], name
        assert "LLM_VENV_PATH" not in runtime_scripts[name], name

    assert "QWEN_MODEL_PATH" in runtime_scripts["serve_qwen_vllm.sh"]
    assert "MODEL_PATH" in runtime_scripts["serve_vllm.sh"]
    assert "sr2fpga_training." in runtime_scripts["train_lora.sh"]
    assert "sr2fpga_training." in runtime_scripts["merge_lora.sh"]
    assert "LLM.src" not in "\n".join(runtime_scripts.values())


def test_training_fixture_tests_do_not_write_to_tracked_tmp() -> None:
    test_path = TRAINING_ROOT / "tests" / "test_training_smoke_assets.py"
    source = test_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(test_path))

    assert 'REPO_ROOT / "tmp' not in source
    assert "TemporaryDirectory" in source or "tmp_path" in source
    assert not any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.replace("\\", "/").startswith("tmp/")
        for node in ast.walk(tree)
    )
