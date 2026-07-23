"""Dry-run checks for chat fine-tuning JSONL files.

This module validates the data shape consumed by ``train_lora.py`` without
loading a model or starting training.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


class DryRunError(ValueError):
    """Raised when a chat training file cannot be consumed safely."""


def dry_run_from_config(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    train_file = Path(str(config["train_file"]))
    max_seq_length = int(config.get("max_seq_length", 2048))
    return dry_run_chat_jsonl(train_file, max_seq_length=max_seq_length)


def dry_run_chat_jsonl(train_file: Path, max_seq_length: int) -> dict[str, Any]:
    lengths: list[int] = []
    rows = 0
    with train_file.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DryRunError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            messages = _validate_messages(row.get("messages"), line_number)
            lengths.append(_estimate_tokens(_render_messages(messages)))

    over_max = sum(1 for length in lengths if length > max_seq_length)
    return {
        "train_file": str(train_file),
        "max_seq_length": max_seq_length,
        "rows": rows,
        "valid_rows": len(lengths),
        "min_tokens": min(lengths) if lengths else 0,
        "max_tokens": max(lengths) if lengths else 0,
        "mean_tokens": round(sum(lengths) / len(lengths), 2) if lengths else 0,
        "over_max_seq_length": over_max,
        "over_max_seq_length_ratio": round(over_max / len(lengths), 4) if lengths else 0,
        "fits_max_seq_length": over_max == 0,
    }


def _load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DryRunError(f"Training config must be a mapping: {path}")
    if "train_file" not in data:
        raise DryRunError(f"Training config is missing train_file: {path}")
    return data


def _validate_messages(messages: Any, line_number: int) -> list[dict[str, str]]:
    if not isinstance(messages, list) or len(messages) < 2:
        raise DryRunError(f"Row {line_number} messages need user and assistant turns")
    normalized: list[dict[str, str]] = []
    has_user = False
    has_assistant = False
    for message in messages:
        if not isinstance(message, dict):
            raise DryRunError(f"Row {line_number} messages must be objects")
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in {"system", "user", "assistant"}:
            raise DryRunError(f"Row {line_number} has unsupported role: {role}")
        if not content:
            raise DryRunError(f"Row {line_number} has empty {role} content")
        has_user = has_user or role == "user"
        has_assistant = has_assistant or role == "assistant"
        normalized.append({"role": role, "content": content})
    if not has_user or not has_assistant:
        raise DryRunError(f"Row {line_number} messages need user and assistant turns")
    return normalized


def _render_messages(messages: list[dict[str, str]]) -> str:
    return "\n".join(f"{message['role']}: {message['content']}" for message in messages)


def _estimate_tokens(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run chat fine-tuning JSONL without loading a model.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=Path, help="Training YAML config with train_file/max_seq_length")
    group.add_argument(
        "--input",
        "--train-file",
        dest="input",
        type=Path,
        help="Chat JSONL file to validate",
    )
    parser.add_argument("--max-seq-length", type=int, default=2048)
    parser.add_argument("--fail-on-truncation", action="store_true")
    args = parser.parse_args()

    if args.config:
        report = dry_run_from_config(args.config)
    else:
        report = dry_run_chat_jsonl(args.input, max_seq_length=args.max_seq_length)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_truncation and not report["fits_max_seq_length"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
