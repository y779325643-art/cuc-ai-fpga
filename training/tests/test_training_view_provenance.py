import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from sr2fpga_training.prepare_dataset import DatasetFormatError, convert_jsonl


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "training" / "src"


def _canonical_req2file_row() -> dict[str, object]:
    return {
        "contract_version": "training-view-row-v1",
        "view_type": "requirement_to_file",
        "source_episode_id": "episode-001",
        "file_role": "rtl",
        "path": "rtl/top.sv",
        "official_eval_unit": False,
        "standalone_pass_credit": False,
        "input": {"requirement": "Implement a synchronous counter."},
        "output": {"content": "module top; endmodule"},
    }


def _convert_one(tmp_path: Path, row: dict[str, object]) -> dict[str, object]:
    source = tmp_path / "source.jsonl"
    target = tmp_path / "chat.jsonl"
    source.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert convert_jsonl(source, target) == 1
    return json.loads(target.read_text(encoding="utf-8"))


def test_valid_requirement_to_file_provenance_converts(tmp_path: Path) -> None:
    converted = _convert_one(tmp_path, _canonical_req2file_row())

    assert "rtl/top.sv" in converted["messages"][0]["content"]
    assert converted["messages"][1]["content"] == "module top; endmodule"


def test_requirement_to_file_requires_source_episode_id(tmp_path: Path) -> None:
    row = _canonical_req2file_row()
    del row["source_episode_id"]

    with pytest.raises(DatasetFormatError, match="source_episode_id"):
        _convert_one(tmp_path, row)


def test_requirement_to_file_cannot_be_official_eval_unit(tmp_path: Path) -> None:
    row = _canonical_req2file_row()
    row["official_eval_unit"] = True

    with pytest.raises(DatasetFormatError, match="official_eval_unit"):
        _convert_one(tmp_path, row)


def test_requirement_to_file_cannot_receive_standalone_credit(
    tmp_path: Path,
) -> None:
    row = _canonical_req2file_row()
    row["standalone_pass_credit"] = True

    with pytest.raises(DatasetFormatError, match="standalone_pass_credit"):
        _convert_one(tmp_path, row)


def test_legacy_project_level_view_still_converts(tmp_path: Path) -> None:
    converted = _convert_one(
        tmp_path,
        {
            "sample_id": "legacy-project",
            "requirement": "Implement a counter project.",
            "files": [
                {
                    "path": "rtl/top.sv",
                    "content": "module top; endmodule",
                }
            ],
        },
    )

    assert "complete SR2FPGA project files" in converted["messages"][0]["content"]


def test_historical_req2file_without_view_type_still_converts(
    tmp_path: Path,
) -> None:
    converted = _convert_one(
        tmp_path,
        {
            "sample_id": "legacy-file",
            "requirement": "Implement a counter.",
            "file_path": "rtl/top.sv",
            "file_content": "module top; endmodule",
        },
    )

    assert converted["messages"][1]["content"] == "module top; endmodule"


def test_training_contract_reader_does_not_import_agent() -> None:
    script = """
import sr2fpga_training.contracts
import json
import sys
print(json.dumps(sorted({"sr2fpga_agent", "LLM"}.intersection(sys.modules))))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(SOURCE_ROOT), os.environ.get("PYTHONPATH", "")]
            ),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []
