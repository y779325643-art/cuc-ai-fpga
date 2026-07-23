import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

ENTRYPOINTS = (
    (
        [sys.executable, "-m", "LLM.src.sr2fpga_agent.runner", "--help"],
        "python -m LLM.src.sr2fpga_agent.runner",
        "python -m sr2fpga_agent.runner",
        "--config",
    ),
    (
        [sys.executable, "-m", "LLM.src.sr2fpga_agent.cli", "--help"],
        "python -m LLM.src.sr2fpga_agent.cli",
        "python -m sr2fpga_agent.cli",
        "--dataset-root",
    ),
    (
        [sys.executable, "-m", "LLM.src.req2file_eval", "--help"],
        "python -m LLM.src.req2file_eval",
        "python -m sr2fpga_agent.req2file_eval",
        "verify-static",
    ),
    (
        [sys.executable, "LLM/src/prepare_dataset.py", "--help"],
        "python LLM/src/prepare_dataset.py",
        "python -m sr2fpga_training.prepare_dataset",
        "--input",
    ),
    (
        [sys.executable, "LLM/src/training_dry_run.py", "--help"],
        "python LLM/src/training_dry_run.py",
        "python -m sr2fpga_training.training_dry_run",
        "--max-seq-length",
    ),
    (
        [sys.executable, "LLM/src/train_lora.py", "--help"],
        "python LLM/src/train_lora.py",
        "python -m sr2fpga_training.train_lora",
        "--config",
    ),
    (
        [sys.executable, "LLM/src/merge_lora.py", "--help"],
        "python LLM/src/merge_lora.py",
        "python -m sr2fpga_training.merge_lora",
        "--base-model",
    ),
)


@pytest.mark.parametrize(
    ("command", "old_command", "replacement", "usage_token"),
    ENTRYPOINTS,
)
def test_documented_legacy_python_entrypoint_forwards(
    command: list[str],
    old_command: str,
    replacement: str,
    usage_token: str,
) -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert f"DEPRECATED: {old_command} -> {replacement}" in completed.stderr
    assert usage_token in completed.stdout


def test_legacy_non_entrypoint_agent_imports_resolve_once() -> None:
    script = """
import warnings
warnings.simplefilter("default", DeprecationWarning)
import LLM.src.sr2fpga_agent.recorder as legacy_recorder
import LLM.src.sr2fpga_agent.system_his_checker as legacy_checker
import sr2fpga_agent.recorder as canonical_recorder
import sr2fpga_agent.system_his_checker as canonical_checker
assert legacy_recorder is canonical_recorder
assert legacy_checker is canonical_checker
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr.count("DeprecationWarning") <= 1
