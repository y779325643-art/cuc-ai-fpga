"""Fail-closed reader and renderer for canonical training-view-row-v2 artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .contracts import TrainingContractError, load_registered_schema


_GLOBAL_FORBIDDEN_KEYS = frozenset(
    {
        "official_hidden_outcome",
        "official_outcome_refs",
        "hidden_raw_material",
        "hidden_reference",
        "hidden_ref",
        "private_evaluator",
        "trusted_testbench",
        "candidate_testbench",
        "evaluator_testbench",
        "golden_model",
        "scoring_code",
        "eligibility_proof",
        "audit_envelope",
    }
)
_M6U_FORBIDDEN_KEYS = frozenset(
    {
        "verdict",
        "status",
        "diagnosis",
        "patch",
        "tool_feedback",
        "tool_output",
        "terminal_selection",
        "eligibility_reason",
        "eligibility_reasons",
    }
)
_GLOBAL_FORBIDDEN_TEXT_MARKERS = (
    "official_hidden_outcome",
    "hidden_raw_material",
    "private_evaluator",
    "trusted_testbench",
    "evaluator_testbench",
    "golden_model",
    "scoring_code",
)
_M6U_JSON_FIELD_PATTERN = re.compile(
    r'"(?:verdict|status|diagnosis|patch|tool_feedback|tool_output|'
    r'terminal_selection|eligibility_reasons?|verified[^"\\]*)"\s*:',
    flags=re.IGNORECASE,
)


def load_training_view_rows_v2(
    path: Path | str,
    *,
    forbidden_canaries: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Load a canonical JSONL view and reject the whole file on any invalid row."""

    source = Path(path)
    rows: list[dict[str, Any]] = []
    row_ids: set[str] = set()
    with source.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise TrainingContractError(
                    f"invalid training view JSON on line {line_number}: {error.msg}"
                ) from error
            if not isinstance(row, dict):
                raise TrainingContractError(
                    f"training view row {line_number} must be a JSON object"
                )
            validate_training_view_row_v2(row, forbidden_canaries=forbidden_canaries)
            row_id = row["row_id"]
            if row_id in row_ids:
                raise TrainingContractError(f"duplicate training view row_id: {row_id}")
            row_ids.add(row_id)
            rows.append(row)
    if not rows:
        raise TrainingContractError("canonical training view JSONL must not be empty")
    return rows


def validate_training_view_row_v2(
    row: dict[str, Any],
    *,
    forbidden_canaries: Iterable[str] = (),
) -> None:
    schema = load_registered_schema("training_view_row")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(row),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        rendered = "; ".join(
            f"{_json_path(error.absolute_path)}: {error.message}" for error in errors
        )
        raise TrainingContractError("invalid training-view-row-v2: " + rendered)
    expected = _sha256({key: value for key, value in row.items() if key != "row_sha256"})
    if row["row_sha256"] != expected:
        raise TrainingContractError("training view row_sha256 does not match canonical row")
    _assert_model_visible_payload(
        row["payload"],
        treatment=row["treatment"],
        forbidden_canaries=tuple(forbidden_canaries),
    )


def render_training_view_row_v2(row: dict[str, Any]) -> list[dict[str, str]]:
    """Render only the model-visible payload; never serialize the row envelope."""

    validate_training_view_row_v2(row)
    payload = row["payload"]
    messages = [dict(message) for message in payload["prompt_messages"]]
    messages.append(
        {
            "role": "assistant",
            "content": json.dumps(
                payload["assistant_target"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
    )
    return messages


def _assert_model_visible_payload(
    payload: dict[str, Any],
    *,
    treatment: str,
    forbidden_canaries: tuple[str, ...],
) -> None:
    forbidden_keys = set(_GLOBAL_FORBIDDEN_KEYS)
    if treatment == "M6U":
        forbidden_keys.update(_M6U_FORBIDDEN_KEYS)
    for path, value in _walk(payload):
        if path:
            key = path[-1]
            if isinstance(key, str):
                normalized = key.strip().lower().replace("-", "_")
                if normalized in forbidden_keys or (
                    treatment == "M6U" and normalized.startswith("verified")
                ):
                    raise TrainingContractError(
                        f"forbidden {treatment} payload field: {_json_path(path)}"
                    )
        if not isinstance(value, str):
            continue
        lowered = value.lower()
        if any(marker in lowered for marker in _GLOBAL_FORBIDDEN_TEXT_MARKERS):
            raise TrainingContractError(
                f"forbidden audit/hidden marker in model-visible payload: {_json_path(path)}"
            )
        if treatment == "M6U" and _M6U_JSON_FIELD_PATTERN.search(value):
            raise TrainingContractError(
                f"forbidden M6U feedback field in model-visible payload: {_json_path(path)}"
            )
        for canary in forbidden_canaries:
            if canary and canary in value:
                raise TrainingContractError(
                    f"forbidden canary in model-visible payload: {_json_path(path)}"
                )


def _walk(value: Any, path: tuple[str | int, ...] = ()):
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, (*path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, (*path, index))


def _json_path(parts: Iterable[str | int]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
