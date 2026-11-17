"""Legacy entry points must not silently claim the adopted research protocol."""
import json

import pytest

from sr2fpga_agent.cli import main
from sr2fpga_agent.runner import load_runner_config


@pytest.mark.parametrize("field,value", [
    ("research_plan_version", "paper1-v2.3"),
    ("research_plan_version", "paper1-v2.2"),
    ("pc_format", "sr2fpga-pc-2.1"),
    ("research_plan_version", "unknown-future-version"),
    ("pc_format", None),
])
def test_runner_rejects_protocol_claim_before_loading_run_paths(tmp_path, field, value):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({field: value}), encoding="utf-8")
    with pytest.raises(SystemExit, match="legacy development runner"):
        load_runner_config(path)


@pytest.mark.parametrize("flag,value", [
    ("--research-plan-version", "paper1-v2.3"),
    ("--research-plan-version", "paper1-v2.2"),
    ("--pc-format", "sr2fpga-pc-2.1"),
])
def test_cli_rejects_protocol_claim_before_creating_artifacts(tmp_path, flag, value):
    destination = tmp_path / "samples"
    with pytest.raises(SystemExit, match="legacy development entry point"):
        main(["--dataset-root", str(destination), "--sample-id", "probe",
              "--project-name", "probe", "--provider", "openai_compat", flag, value])
    assert not destination.exists()
