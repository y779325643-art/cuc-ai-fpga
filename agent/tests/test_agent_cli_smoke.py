import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("module", "usage_token"),
    (
        ("sr2fpga_agent.cli", "--dataset-root"),
        ("sr2fpga_agent.runner", "--config"),
        ("sr2fpga_agent.baseline_report", "--summary"),
        ("sr2fpga_agent.req2file_eval", "verify-static"),
        ("sr2fpga_agent.task_evidence", "--audit-run-root"),
    ),
)
def test_canonical_cli_help_works_from_installed_agent(
    tmp_path: Path,
    module: str,
    usage_token: str,
) -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "usage:" in completed.stdout
    assert usage_token in completed.stdout


def test_legacy_runner_module_warns_once_and_remains_executable() -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "-W",
            "default",
            "-m",
            "LLM.src.sr2fpga_agent.runner",
            "--help",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--config" in completed.stdout
    assert completed.stderr.count("DeprecationWarning") == 1
    assert "RuntimeWarning" not in completed.stderr
