"""Prepare JSONL chat fine-tuning data.

Supported input rows:
- {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
- {"instruction": "...", "input": "...", "output": "..."}
- {"prompt": "...", "completion": "..."}
- SR2FPGA training-view rows exported by DatasetRecorder:
  requirement_to_his, his_to_project, requirement_to_project,
  requirement_to_file, failure_to_diagnosis, failure_to_patch,
  project_to_predicted_qor, and project_to_measured_qor.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class DatasetFormatError(ValueError):
    """Raised when a dataset row cannot be converted to chat messages."""


def convert_jsonl(
    source: Path,
    target: Path,
    *,
    sample_id_prefix: str = "",
    exclude_file_paths: set[str] | None = None,
) -> int:
    """Convert a JSONL dataset into chat-message JSONL format."""
    rows: list[dict[str, Any]] = []
    excluded_paths = exclude_file_paths or set()
    with source.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetFormatError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            if sample_id_prefix and not str(row.get("sample_id", "")).startswith(sample_id_prefix):
                continue
            if str(row.get("file_path", "")) in excluded_paths:
                continue
            rows.append({"messages": _row_to_messages(row, line_number)})

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as output_file:
        for row in rows:
            output_file.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _row_to_messages(row: dict[str, Any], line_number: int) -> list[dict[str, str]]:
    if "messages" in row:
        return _validate_messages(row["messages"], line_number)

    if "requirement" in row and "system_his" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Convert this SR2FPGA requirement into System-HIS JSON.\n\n"
                    f"SR2FPGA requirement:\n{str(row['requirement']).strip()}",
                },
                {"role": "assistant", "content": _compact_json(row["system_his"])},
            ],
            line_number,
        )

    if "system_his" in row and "files" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Generate complete SR2FPGA project files from this System-HIS JSON.\n\n"
                    f"System-HIS JSON:\n{_pretty_json(row['system_his'])}",
                },
                {"role": "assistant", "content": _compact_json(row["files"])},
            ],
            line_number,
        )

    if "requirement" in row and "files" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Generate complete SR2FPGA project files from this requirement.\n\n"
                    f"SR2FPGA requirement:\n{str(row['requirement']).strip()}",
                },
                {"role": "assistant", "content": _compact_json(row["files"])},
            ],
            line_number,
        )

    if "requirement" in row and "file_path" in row and "file_content" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Generate this SR2FPGA project file from the requirement.\n\n"
                    f"SR2FPGA requirement:\n{str(row['requirement']).strip()}\n\n"
                    f"File path:\n{str(row['file_path']).strip()}",
                },
                {"role": "assistant", "content": str(row["file_content"]).strip()},
            ],
            line_number,
        )

    if "files" in row and "predicted_qor" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Predict QoR for this SR2FPGA project.\n\n"
                    f"Project files JSON:\n{_pretty_json(row['files'])}",
                },
                {"role": "assistant", "content": _compact_json(row["predicted_qor"])},
            ],
            line_number,
        )

    if "files" in row and "measured_qor" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Estimate measured QoR for this SR2FPGA project after synthesis.\n\n"
                    f"Project files JSON:\n{_pretty_json(row['files'])}",
                },
                {"role": "assistant", "content": _compact_json(row["measured_qor"])},
            ],
            line_number,
        )

    if "diagnosis" in row and "patch" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Patch this SR2FPGA failure using the diagnosis and trajectory context.\n\n"
                    f"Diagnosis JSON:\n{_pretty_json(row['diagnosis'])}\n\n"
                    f"Episode JSON:\n{_pretty_json(row.get('episode', {}))}",
                },
                {"role": "assistant", "content": str(row["patch"]).strip()},
            ],
            line_number,
        )

    if "diagnosis" in row:
        return _validate_messages(
            [
                {
                    "role": "user",
                    "content": "Diagnose this SR2FPGA failure from the trajectory context.\n\n"
                    f"Episode JSON:\n{_pretty_json(row.get('episode', {}))}",
                },
                {"role": "assistant", "content": _compact_json(row["diagnosis"])},
            ],
            line_number,
        )

    if "instruction" in row:
        prompt = str(row["instruction"]).strip()
        extra_input = str(row.get("input", "")).strip()
        if extra_input:
            prompt = f"{prompt}\n\n{extra_input}"
        answer = row.get("output") or row.get("response") or row.get("answer")
        if not answer:
            raise DatasetFormatError(f"Row {line_number} is missing assistant response")
        return _validate_messages(
            [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": str(answer).strip()},
            ],
            line_number,
        )

    if "prompt" in row:
        answer = row.get("completion") or row.get("response") or row.get("answer")
        if not answer:
            raise DatasetFormatError(f"Row {line_number} is missing assistant response")
        return _validate_messages(
            [
                {"role": "user", "content": str(row["prompt"]).strip()},
                {"role": "assistant", "content": str(answer).strip()},
            ],
            line_number,
        )

    raise DatasetFormatError(f"Row {line_number} must contain messages, instruction, or prompt")


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _validate_messages(messages: Any, line_number: int) -> list[dict[str, str]]:
    if not isinstance(messages, list) or len(messages) < 2:
        raise DatasetFormatError(f"Row {line_number} messages must contain at least two turns")

    normalized: list[dict[str, str]] = []
    has_user = False
    has_assistant = False
    for message in messages:
        if not isinstance(message, dict):
            raise DatasetFormatError(f"Row {line_number} messages must be objects")
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in {"system", "user", "assistant"}:
            raise DatasetFormatError(f"Row {line_number} has unsupported role: {role}")
        if not content:
            raise DatasetFormatError(f"Row {line_number} has empty content")
        has_user = has_user or role == "user"
        has_assistant = has_assistant or role == "assistant"
        normalized.append({"role": role, "content": content})

    if not has_user or not has_assistant:
        raise DatasetFormatError(f"Row {line_number} messages need user and assistant turns")
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert JSONL data to chat fine-tuning JSONL.")
    parser.add_argument("--input", required=True, type=Path, help="Source JSONL file.")
    parser.add_argument("--output", required=True, type=Path, help="Converted JSONL file.")
    parser.add_argument("--sample-id-prefix", default="", help="Only convert rows whose sample_id starts with this.")
    parser.add_argument(
        "--exclude-file-path",
        action="append",
        default=[],
        help="Skip rows with this file_path. Can be passed more than once.",
    )
    args = parser.parse_args()

    count = convert_jsonl(
        args.input,
        args.output,
        sample_id_prefix=args.sample_id_prefix,
        exclude_file_paths=set(args.exclude_file_path),
    )
    print(f"Converted {count} rows to {args.output}")


if __name__ == "__main__":
    main()
