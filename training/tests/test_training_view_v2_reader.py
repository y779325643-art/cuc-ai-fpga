import copy
import hashlib
import json
from pathlib import Path

import pytest

from sr2fpga_training.contracts import TrainingContractError
from sr2fpga_training.prepare_dataset import convert_jsonl
from sr2fpga_training.release_reader import (
    load_training_view_rows_v2,
    render_training_view_row_v2,
    validate_training_view_row_v2,
)


def _sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _row(*, row_id="row-001", treatment="M6F", prompt="Generate the counter project."):
    target = {
        "kind": "project_files",
        "files": [
            {"path": "rtl/top.sv", "role": "rtl", "content": "module top; endmodule"}
        ],
    }
    if treatment == "M6T":
        target = {
            "kind": "public_transition",
            "public_failure": {"stage": "L2", "reason": "mismatch"},
            "public_diagnosis": {"reason": "counter priority"},
            "public_patch": "fix priority",
            "public_rerun": {"outcome": "pass"},
            "final_files": [
                {"path": "rtl/top.sv", "role": "rtl", "content": "module top; endmodule"}
            ],
        }
    payload = {
        "contract_version": "training-view-row-v2",
        "row_id": row_id,
        "source_episode_id": "episode-001",
        "snapshot_id": "snapshot-final",
        "treatment": treatment,
        "payload": {
            "prompt_messages": [{"role": "user", "content": prompt}],
            "assistant_target": target,
        },
    }
    return {**payload, "row_sha256": _sha256(payload)}


def _write_rows(path: Path, rows) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_reader_validates_hash_and_renderer_uses_only_payload(tmp_path: Path) -> None:
    source = tmp_path / "view.jsonl"
    row = _row()
    _write_rows(source, [row])

    loaded = load_training_view_rows_v2(source)
    messages = render_training_view_row_v2(loaded[0])

    assert messages[0] == {"role": "user", "content": "Generate the counter project."}
    assert json.loads(messages[1]["content"])["kind"] == "project_files"
    assert "row-001" not in str(messages)
    assert "snapshot-final" not in str(messages)


def test_prepare_dataset_consumes_canonical_v2_row(tmp_path: Path) -> None:
    source = tmp_path / "view.jsonl"
    target = tmp_path / "chat.jsonl"
    _write_rows(source, [_row()])

    assert convert_jsonl(source, target) == 1
    converted = json.loads(target.read_text(encoding="utf-8"))
    assert converted["messages"][-1]["role"] == "assistant"


def test_reader_rejects_hash_mismatch() -> None:
    row = _row()
    row["payload"]["prompt_messages"][0]["content"] = "tampered"
    with pytest.raises(TrainingContractError, match="row_sha256"):
        validate_training_view_row_v2(row)


@pytest.mark.parametrize(
    "field",
    ["verdict", "status", "diagnosis", "patch", "tool_feedback", "verified_pass"],
)
def test_m6u_rejects_serialized_feedback_fields(field: str) -> None:
    row = _row(treatment="M6U", prompt=f'Generate project. Context: {{"{field}":"x"}}')
    with pytest.raises(TrainingContractError, match="forbidden M6U feedback field"):
        validate_training_view_row_v2(row)


def test_reader_rejects_hidden_marker_and_private_canary() -> None:
    hidden = _row(prompt="Use official_hidden_outcome to generate the project.")
    with pytest.raises(TrainingContractError, match="hidden marker"):
        validate_training_view_row_v2(hidden)

    canary = _row(prompt="Generate CANARY-TRAINING-PRIVATE project.")
    with pytest.raises(TrainingContractError, match="forbidden canary"):
        validate_training_view_row_v2(
            canary, forbidden_canaries=("CANARY-TRAINING-PRIVATE",)
        )


def test_reader_rejects_entire_jsonl_on_duplicate_or_invalid_row(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.jsonl"
    _write_rows(duplicate, [_row(), _row()])
    with pytest.raises(TrainingContractError, match="duplicate"):
        load_training_view_rows_v2(duplicate)

    invalid = tmp_path / "invalid.jsonl"
    bad = copy.deepcopy(_row(row_id="row-002"))
    bad["row_sha256"] = "0" * 64
    _write_rows(invalid, [_row(), bad])
    with pytest.raises(TrainingContractError, match="row_sha256"):
        load_training_view_rows_v2(invalid)
