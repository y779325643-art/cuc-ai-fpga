"""Prepare JSONL chat fine-tuning data.

Supported input rows:
- {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
- {"instruction": "...", "input": "...", "output": "..."}
- {"prompt": "...", "completion": "..."}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class DatasetFormatError(ValueError):
    """Raised when a dataset row cannot be converted to chat messages."""


def convert_jsonl(source: Path, target: Path) -> int:
    """Convert a JSONL dataset into chat-message JSONL format."""
    rows: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetFormatError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            rows.append({"messages": _row_to_messages(row, line_number)})

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as output_file:
        for row in rows:
            output_file.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _row_to_messages(row: dict[str, Any], line_number: int) -> list[dict[str, str]]:
    if "messages" in row:
        return _validate_messages(row["messages"], line_number)

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
    args = parser.parse_args()

    count = convert_jsonl(args.input, args.output)
    print(f"Converted {count} rows to {args.output}")


if __name__ == "__main__":
    main()
