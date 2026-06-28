"""Baseline report helpers for SR2FPGA runner summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPORT_GROUPS = (
    "failure_family",
    "source",
    "failure_origin",
    "difficulty_tier",
    "requirement_style",
    "contract_skeleton_mode",
    "topology_id",
    "measurement_point",
)
DEFAULT_KNEE_THRESHOLD = 0.8


def baseline_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract baseline calibration rows from a runner summary."""
    calibration = summary.get("calibration_matrix", {})
    if not isinstance(calibration, dict):
        return []
    rows: list[dict[str, Any]] = []
    for group in REPORT_GROUPS:
        cells = calibration.get(group, {})
        if not isinstance(cells, dict):
            continue
        for value in sorted(cells, key=_sort_key):
            cell = cells[value]
            if not isinstance(cell, dict):
                continue
            rows.append(
                {
                    "group": group,
                    "value": str(value),
                    "total": int(cell.get("total", 0)),
                    "pass_levels": _pass_levels(cell.get("pass_levels", {})),
                    "l3_pass_rate": float(cell.get("l3_pass_rate", 0.0)),
                    "l0_contract_failures": int(cell.get("l0_contract_failures", 0)),
                    "cross_file_consistency_error_rate": float(
                        cell.get("cross_file_consistency_error_rate", 0.0)
                    ),
                }
            )
    return rows


def detect_pass_rate_knee(rows: list[dict[str, Any]], threshold: float = DEFAULT_KNEE_THRESHOLD) -> dict[str, Any]:
    """Return the first difficulty tier whose L3 pass rate drops below threshold."""
    tier_rows = [row for row in rows if row.get("group") == "difficulty_tier"]
    for row in sorted(tier_rows, key=lambda item: _sort_key(item.get("value", ""))):
        if float(row.get("l3_pass_rate", 0.0)) < threshold:
            return dict(row)
    return {}


def render_markdown(
    run_id: str,
    rows: list[dict[str, Any]],
    knee_threshold: float = DEFAULT_KNEE_THRESHOLD,
    summary: dict[str, Any] | None = None,
) -> str:
    """Render calibration rows as a compact experiment-note table."""
    knee = detect_pass_rate_knee(rows, threshold=knee_threshold)
    lines = [
        f"# SR2FPGA Baseline Report: {run_id}",
        "",
        _knee_summary(knee, knee_threshold),
        "",
        "| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {group} | {value} | {total} | {pass_levels} | {l3_rate} | {l0_failures} | {l0_rate} |".format(
                group=row["group"],
                value=row["value"],
                total=row["total"],
                pass_levels=_format_pass_levels(row["pass_levels"]),
                l3_rate=_format_rate(row["l3_pass_rate"]),
                l0_failures=row["l0_contract_failures"],
                l0_rate=_format_rate(row["cross_file_consistency_error_rate"]),
            )
        )
    _append_latent_testbench_issue_section(lines, summary or {})
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render an SR2FPGA baseline summary table.")
    parser.add_argument("--summary", required=True, type=Path, help="Path to runner summary.json")
    parser.add_argument("--output", type=Path, help="Optional markdown output path")
    parser.add_argument(
        "--knee-threshold",
        type=float,
        default=DEFAULT_KNEE_THRESHOLD,
        help="L3 pass-rate threshold used to flag the first failing difficulty tier",
    )
    args = parser.parse_args(argv)

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    run_id = str(summary.get("run_id", args.summary.parent.name))
    markdown = render_markdown(
        run_id,
        baseline_rows(summary),
        knee_threshold=args.knee_threshold,
        summary=summary,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")


def _sort_key(value: object) -> tuple[int, str]:
    text = str(value)
    if text.startswith("T") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (9999, text)


def _pass_levels(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): int(count) for key, count in value.items()}


def _format_pass_levels(pass_levels: dict[str, int]) -> str:
    if not pass_levels:
        return ""
    return ", ".join(f"{key}:{pass_levels[key]}" for key in sorted(pass_levels))


def _format_rate(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def _knee_summary(knee: dict[str, Any], threshold: float) -> str:
    if not knee:
        return f"Pass-rate knee: not observed above threshold {_format_rate(threshold)}."
    return (
        "Pass-rate knee: {value} (L3 pass rate {rate} < {threshold}).".format(
            value=knee["value"],
            rate=_format_rate(float(knee.get("l3_pass_rate", 0.0))),
            threshold=_format_rate(threshold),
        )
    )


def _append_latent_testbench_issue_section(lines: list[str], summary: dict[str, Any]) -> None:
    issues = summary.get("latent_testbench_issue_breakdown", {})
    if not isinstance(issues, dict) or not issues:
        return
    lines.extend(
        [
            "",
            "## Latent Testbench Issues",
            "",
            "| issue_type | count |",
            "|---|---:|",
        ]
    )
    for issue_type in sorted(issues):
        lines.append(f"| {issue_type} | {int(issues[issue_type])} |")


if __name__ == "__main__":
    main()
