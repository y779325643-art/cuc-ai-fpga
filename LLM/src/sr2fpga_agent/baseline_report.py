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
    _append_contract_skeleton_ablation_section(lines, summary or {})
    _append_latent_testbench_issue_section(lines, summary or {})
    _append_oracle_strength_section(lines, summary or {})
    _append_repair_metrics_section(lines, summary or {})
    _append_l0_l4_survival_section(lines, summary or {})
    _append_generated_his_credit_section(lines, summary or {})
    _append_h_stage_section(lines, summary or {})
    _append_l4_open_section(lines, summary or {})
    _append_l4_commercial_section(lines, summary or {})
    _append_derived_training_views_section(lines, summary or {})
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


def _append_contract_skeleton_ablation_section(lines: list[str], summary: dict[str, Any]) -> None:
    matrix = summary.get("calibration_matrix", {})
    if not isinstance(matrix, dict):
        return
    cells = matrix.get("contract_skeleton_mode", {})
    if not isinstance(cells, dict) or not cells:
        return
    lines.extend(
        [
            "",
            "## Contract Skeleton Ablation",
            "",
            "| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for mode in sorted(cells, key=_contract_skeleton_sort_key):
        cell = cells[mode]
        if not isinstance(cell, dict):
            continue
        lines.append(
            "| {mode} | {total} | {pass_levels} | {l3_rate} | {l0_failures} | {l0_rate} |".format(
                mode=str(mode),
                total=int(cell.get("total", 0)),
                pass_levels=_format_pass_levels(_pass_levels(cell.get("pass_levels", {}))),
                l3_rate=_format_rate(float(cell.get("l3_pass_rate", 0.0))),
                l0_failures=int(cell.get("l0_contract_failures", 0)),
                l0_rate=_format_rate(float(cell.get("cross_file_consistency_error_rate", 0.0))),
            )
        )
    legacy = cells.get("legacy_full_project")
    behavior = cells.get("behavior_files")
    if isinstance(legacy, dict) and isinstance(behavior, dict):
        l0_delta = int(behavior.get("l0_contract_failures", 0)) - int(legacy.get("l0_contract_failures", 0))
        l3_delta = float(behavior.get("l3_pass_rate", 0.0)) - float(legacy.get("l3_pass_rate", 0.0))
        lines.extend(
            [
                "",
                f"L0 contract failure delta (behavior_files - legacy_full_project): {l0_delta:+d}",
                f"L3 pass-rate delta (behavior_files - legacy_full_project): {_format_percentage_points(l3_delta)}",
            ]
        )


def _contract_skeleton_sort_key(value: object) -> tuple[int, str]:
    order = {
        "legacy_full_project": 0,
        "behavior_files": 1,
        "deterministic_template": 2,
    }
    text = str(value)
    return (order.get(text, 999), text)


def _format_percentage_points(delta: float) -> str:
    return f"{delta * 100:+.1f} pp"


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


def _append_oracle_strength_section(lines: list[str], summary: dict[str, Any]) -> None:
    strength = summary.get("oracle_strength", {})
    if not isinstance(strength, dict) or not strength.get("samples"):
        return
    lines.extend(
        [
            "",
            "## Testbench Oracle Strength",
            "",
            "| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |",
            "|---:|---:|---:|---:|---:|---:|---:|",
            "| {samples} | {reference_passed} | {mutation_cases} | {killed} | {score:.1%} | {line_a_ready} | {line_a_not_ready} |".format(
                samples=int(strength.get("samples", 0)),
                reference_passed=int(strength.get("reference_passed", 0)),
                mutation_cases=int(strength.get("mutation_cases", 0)),
                killed=int(strength.get("killed", 0)),
                score=float(strength.get("mutation_score", 0.0)),
                line_a_ready=int(strength.get("line_a_ready", 0)),
                line_a_not_ready=int(strength.get("line_a_not_ready", 0)),
            ),
            "",
            "| surviving_mutation | samples |",
            "|---|---:|",
        ]
    )
    survivors = strength.get("surviving_mutations", {})
    if isinstance(survivors, dict):
        for name in sorted(survivors):
            lines.append(f"| {name} | {int(survivors[name])} |")
    non_scoreable = strength.get("non_scoreable_mutations", {})
    if isinstance(non_scoreable, dict) and non_scoreable:
        lines.extend(
            [
                "",
                "| non_scoreable_mutation | samples |",
                "|---|---:|",
            ]
        )
        for name in sorted(non_scoreable):
            lines.append(f"| {name} | {int(non_scoreable[name])} |")


def _append_repair_metrics_section(lines: list[str], summary: dict[str, Any]) -> None:
    metrics = summary.get("repair_metrics", {})
    if not isinstance(metrics, dict) or not metrics.get("total_patches"):
        return
    lines.extend(
        [
            "",
            "## Patch-as-PR Repair",
            "",
            "| total patches | valid patches | invalid edit surface | fixed target | automatic pass credit | regressing patches | regression rate |",
            "|---:|---:|---:|---:|---:|---:|---:|",
            "| {total} | {valid} | {invalid} | {fixed} | {credit} | {regressing} | {rate} |".format(
                total=int(metrics.get("total_patches", 0)),
                valid=int(metrics.get("valid_patches", 0)),
                invalid=int(metrics.get("invalid_edit_surface", 0)),
                fixed=int(metrics.get("fixed_target", 0)),
                credit=int(metrics.get("automatic_pass_credit", 0)),
                regressing=int(metrics.get("regressing_patches", 0)),
                rate=_format_rate(float(metrics.get("regression_rate", 0.0))),
            ),
        ]
    )


def _append_l4_open_section(lines: list[str], summary: dict[str, Any]) -> None:
    counts = summary.get("l4_open", {})
    if not isinstance(counts, dict):
        return
    skip_reasons = summary.get("l4_open_skip_reasons", {})
    skip_reasons = skip_reasons if isinstance(skip_reasons, dict) else {}
    lines.extend(
        [
            "",
            "## L4-open",
            "",
            "| pass | fail | not_run |",
            "|---:|---:|---:|",
            f"| {int(counts.get('pass', 0))} | {int(counts.get('fail', 0))} | {int(counts.get('not_run', 0))} |",
            "",
            "| skip_reason | count |",
            "|---|---:|",
        ]
    )
    for reason in sorted(skip_reasons):
        lines.append(f"| {reason} | {int(skip_reasons[reason])} |")


def _append_l4_commercial_section(lines: list[str], summary: dict[str, Any]) -> None:
    counts = summary.get("l4_commercial", {})
    if not isinstance(counts, dict):
        return
    skip_reasons = summary.get("l4_commercial_skip_reasons", {})
    skip_reasons = skip_reasons if isinstance(skip_reasons, dict) else {}
    lines.extend(
        [
            "",
            "## L4-commercial",
            "",
            "| pass | fail | not_run |",
            "|---:|---:|---:|",
            f"| {int(counts.get('pass', 0))} | {int(counts.get('fail', 0))} | {int(counts.get('not_run', 0))} |",
            "",
            "| skip_reason | count |",
            "|---|---:|",
        ]
    )
    for reason in sorted(skip_reasons):
        lines.append(f"| {reason} | {int(skip_reasons[reason])} |")


def _append_h_stage_section(lines: list[str], summary: dict[str, Any]) -> None:
    h_stage = summary.get("h_stage", {})
    if not isinstance(h_stage, dict) or not h_stage:
        return
    lines.extend(
        [
            "",
            "## H0-H3 Summary",
            "",
            "| stage | pass | fail | not_applicable |",
            "|---|---:|---:|---:|",
        ]
    )
    for stage in ("h0", "h1", "h2", "h3"):
        counts = h_stage.get(stage, {})
        counts = counts if isinstance(counts, dict) else {}
        lines.append(
            "| {stage} | {passed} | {failed} | {not_applicable} |".format(
                stage=stage,
                passed=int(counts.get("pass", 0)),
                failed=int(counts.get("fail", 0)),
                not_applicable=int(counts.get("not_applicable", 0)),
            )
        )


def _append_l0_l4_survival_section(lines: list[str], summary: dict[str, Any]) -> None:
    levels = summary.get("levels", {})
    if not isinstance(levels, dict) or not levels:
        return
    lines.extend(
        [
            "",
            "## L0-L4 Survival",
            "",
            "| level | pass | fail | not_run |",
            "|---|---:|---:|---:|",
        ]
    )
    for level in ("l0", "l1", "l2", "l3", "l4_open"):
        counts = levels.get(level, {})
        counts = counts if isinstance(counts, dict) else {}
        lines.append(
            f"| {level} | {int(counts.get('pass', 0))} | {int(counts.get('fail', 0))} | {int(counts.get('not_run', 0))} |"
        )


def _append_generated_his_credit_section(lines: list[str], summary: dict[str, Any]) -> None:
    credit = summary.get("generated_his_credit", {})
    pass_levels = summary.get("generated_his_pass_level_breakdown", {})
    if not isinstance(credit, dict) or not credit:
        return
    pass_levels = pass_levels if isinstance(pass_levels, dict) else {}
    lines.extend(
        [
            "",
            "## Generated-HIS Credit",
            "",
            "| credit_bucket | count |",
            "|---|---:|",
        ]
    )
    for bucket, count in sorted(credit.items()):
        lines.append(f"| {bucket} | {int(count)} |")
    lines.extend(
        [
            "",
            "| generated_his_pass_level | count |",
            "|---|---:|",
        ]
    )
    for pass_level, count in sorted(pass_levels.items()):
        lines.append(f"| {pass_level} | {int(count)} |")


def _append_derived_training_views_section(lines: list[str], summary: dict[str, Any]) -> None:
    views = summary.get("derived_training_views", {})
    if not isinstance(views, dict) or not views:
        return
    lines.extend(
        [
            "",
            "## Derived Training Views",
            "",
            "| view | available | official eval unit | standalone pass credit | rows | file-level passed |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    for view_name in sorted(views):
        view = views[view_name]
        if not isinstance(view, dict):
            continue
        lines.append(
            "| {view} | {available} | {official} | {credit} | {rows} | {file_passed} |".format(
                view=str(view_name),
                available=_yes_no(view.get("available")),
                official=_yes_no(view.get("official_eval_unit")),
                credit=_yes_no(view.get("standalone_pass_credit")),
                rows=int(view.get("rows", 0)),
                file_passed=int(view.get("file_level_passed", 0)),
            )
        )


def _yes_no(value: Any) -> str:
    return "yes" if value is True else "no"


if __name__ == "__main__":
    main()
