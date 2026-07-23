"""Vivado representative-flow Tcl generation and normalized report parsing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any


def build_vivado_tcl(project_dir: Path, *, part: str, target_period_ns: float) -> str:
    project_dir = project_dir.resolve()
    manifest = json.loads((project_dir / "manifest.json").read_text(encoding="utf-8"))
    sources = manifest.get("sources")
    top_module = manifest.get("top_module")
    if not isinstance(sources, list) or not sources or not isinstance(top_module, str) or not top_module:
        raise ValueError("manifest must define non-empty sources and top_module")

    clock_name = "clk"
    system_his_path = project_dir / "system_his.json"
    if system_his_path.is_file():
        system_his = json.loads(system_his_path.read_text(encoding="utf-8"))
        clocks = system_his.get("clocks", [])
        if clocks and isinstance(clocks[0], dict) and isinstance(clocks[0].get("name"), str):
            clock_name = clocks[0]["name"]

    source_paths = [_tcl_brace(project_dir / str(source)) for source in sources]
    output_dir = _tcl_brace(project_dir / "eval" / "vivado")
    source_list = " ".join(source_paths)
    return "\n".join(
        [
            f"set output_dir {output_dir}",
            "file mkdir $output_dir",
            f"read_verilog -sv [list {source_list}]",
            f"synth_design -top {_tcl_atom(top_module)} -part {_tcl_atom(part)}",
            f"create_clock -period {target_period_ns:.6f} [get_ports {_tcl_atom(clock_name)}]",
            "opt_design",
            "place_design",
            "route_design",
            "report_timing_summary -delay_type max -max_paths 10 -file [file join $output_dir vivado_timing_summary.rpt]",
            "report_utilization -file [file join $output_dir vivado_utilization.rpt]",
            "report_clock_utilization -file [file join $output_dir vivado_clock_utilization.rpt]",
            "report_drc -file [file join $output_dir vivado_drc.rpt]",
            "report_methodology -file [file join $output_dir vivado_methodology.rpt]",
            "write_checkpoint -force [file join $output_dir vivado_routed.dcp]",
            "",
        ]
    )


def parse_vivado_reports(
    timing_report: str,
    utilization_report: str,
    *,
    target_period_ns: float,
    drc_report: str = "",
    methodology_report: str = "",
) -> dict[str, Any]:
    wns_ns = _parse_wns(timing_report)
    critical_period_ns = target_period_ns - wns_ns if wns_ns is not None else None
    fmax_mhz = 1000.0 / critical_period_ns if critical_period_ns and critical_period_ns > 0 else None
    resources = {
        "lut": _parse_utilization_value(utilization_report, r"Slice LUTs\*?"),
        "ff": _parse_utilization_value(utilization_report, r"Slice Registers"),
        "bram": _parse_utilization_value(utilization_report, r"Block RAM Tile"),
        "dsp": _parse_utilization_value(utilization_report, r"DSPs"),
    }
    drc_rules = _parse_report_rules(drc_report)
    methodology_rules = _parse_report_rules(methodology_report)
    expected_board_drc = sorted(
        rule for rule, severity in drc_rules.items() if severity == "Critical Warning" and rule in {"NSTD-1", "UCIO-1"}
    )
    invalidating_critical = sorted(
        rule
        for rule, severity in drc_rules.items()
        if severity in {"Critical Warning", "Error"} and rule not in {"NSTD-1", "UCIO-1"}
    )
    timing_pass = wns_ns is not None and wns_ns >= 0
    return {
        "tool": "vivado",
        "status": "pass" if timing_pass and not invalidating_critical else "fail",
        "constraint_scope": "logical_only",
        "board_constraints_applied": False,
        "official_board_ready": False,
        "drc_warnings": sorted(drc_rules),
        "expected_board_drc_exceptions": expected_board_drc,
        "invalidating_critical_warnings": invalidating_critical,
        "methodology_warnings": sorted(methodology_rules),
        "wns_ns": wns_ns,
        "fmax_mhz": fmax_mhz,
        **resources,
    }


def run_vivado_reference(
    project_dir: Path,
    *,
    vivado_command: str,
    part: str,
    target_period_ns: float,
    timeout_seconds: int,
) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    report_dir = project_dir / "eval" / "vivado"
    report_dir.mkdir(parents=True, exist_ok=True)
    tcl_path = report_dir / "vivado_run.tcl"
    tcl_path.write_text(
        build_vivado_tcl(project_dir, part=part, target_period_ns=target_period_ns),
        encoding="utf-8",
    )
    command = [vivado_command, "-mode", "batch", "-source", str(tcl_path)]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    runtime_sec = time.monotonic() - started
    log_text = completed.stdout
    if completed.stderr:
        log_text += completed.stderr
    (report_dir / "vivado.log").write_text(log_text, encoding="utf-8")

    report = normalize_existing_vivado_reports(project_dir, target_period_ns=target_period_ns)
    report.update(
        {
            "status": report["status"] if completed.returncode == 0 else "fail",
            "exit_code": completed.returncode,
            "runtime_sec": runtime_sec,
            "part": part,
            "target_period_ns": target_period_ns,
            "command": command,
            "report_paths": [
                path.relative_to(project_dir).as_posix()
                for path in sorted(report_dir.iterdir())
                if path.is_file()
            ],
        }
    )
    (report_dir / "vivado_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def normalize_existing_vivado_reports(project_dir: Path, *, target_period_ns: float) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    report_dir = project_dir / "eval" / "vivado"

    def read_report(name: str) -> str:
        path = report_dir / name
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""

    report = parse_vivado_reports(
        read_report("vivado_timing_summary.rpt"),
        read_report("vivado_utilization.rpt"),
        target_period_ns=target_period_ns,
        drc_report=read_report("vivado_drc.rpt"),
        methodology_report=read_report("vivado_methodology.rpt"),
    )
    report["target_period_ns"] = target_period_ns
    report["report_paths"] = [
        path.relative_to(project_dir).as_posix()
        for path in sorted(report_dir.iterdir())
        if path.is_file()
    ]
    (report_dir / "vivado_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a Vivado representative P&R reference flow.")
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--vivado", required=True)
    parser.add_argument("--part", default="XC7Z020CLG484-2")
    parser.add_argument("--period-ns", type=float, default=10.0)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    report = run_vivado_reference(
        args.project_dir,
        vivado_command=args.vivado,
        part=args.part,
        target_period_ns=args.period_ns,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


def _parse_wns(report: str) -> float | None:
    lines = report.splitlines()
    for index, line in enumerate(lines):
        if "WNS(ns)" not in line:
            continue
        for candidate in lines[index + 1 :]:
            match = re.match(r"\s*([-+]?[0-9]+(?:\.[0-9]+)?)\b", candidate)
            if match:
                return float(match.group(1))
    return None


def _parse_utilization_value(report: str, label_pattern: str) -> int | float:
    match = re.search(rf"^\s*\|\s*{label_pattern}\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*\|", report, re.MULTILINE)
    if not match:
        return 0
    value = float(match.group(1))
    return int(value) if value.is_integer() else value


def _parse_report_rules(report: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for match in re.finditer(
        r"^\s*\|\s*([A-Z][A-Z0-9_-]*-[0-9]+)\s*\|\s*(Critical Warning|Warning|Error)\s*\|",
        report,
        re.MULTILINE,
    ):
        rules[match.group(1)] = match.group(2)
    return rules


def _tcl_brace(path: Path) -> str:
    return _tcl_atom(path.resolve().as_posix())


def _tcl_atom(value: str) -> str:
    if "{" in value or "}" in value:
        raise ValueError("Tcl value cannot contain braces")
    return "{" + value + "}"


if __name__ == "__main__":
    main()
