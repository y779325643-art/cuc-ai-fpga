import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT / "training" / "tests" / "fixtures" / "smoke_verilog_raw.jsonl"
)


def _installed_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return environment


@pytest.mark.parametrize(
    ("module", "usage_token"),
    (
        ("sr2fpga_training.prepare_dataset", "--input"),
        ("sr2fpga_training.training_dry_run", "--max-seq-length"),
        ("sr2fpga_training.train_lora", "--config"),
        ("sr2fpga_training.merge_lora", "--base-model"),
    ),
)
def test_training_cli_help_works_from_lightweight_install(
    tmp_path: Path,
    module: str,
    usage_token: str,
) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        cwd=tmp_path,
        env=_installed_environment(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "usage:" in completed.stdout
    assert usage_token in completed.stdout


def test_lightweight_install_converts_and_dry_runs_without_model(
    tmp_path: Path,
) -> None:
    converted = tmp_path / "smoke.chat.jsonl"
    environment = _installed_environment()

    conversion = subprocess.run(
        [
            sys.executable,
            "-m",
            "sr2fpga_training.prepare_dataset",
            "--input",
            str(FIXTURE),
            "--output",
            str(converted),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert conversion.returncode == 0, conversion.stderr
    assert "Converted 6 rows" in conversion.stdout

    dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "sr2fpga_training.training_dry_run",
            "--input",
            str(converted),
            "--max-seq-length",
            "2048",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr
    report = json.loads(dry_run.stdout)
    assert report["rows"] == 6
    assert report["fits_max_seq_length"] is True
