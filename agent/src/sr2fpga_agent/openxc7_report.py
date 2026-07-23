"""OpenXC7/nextpnr-xilinx report parsing helpers."""

from __future__ import annotations

import json
import re
from typing import Any


def parse_openxc7_report(report_text: str) -> dict[str, Any]:
    """Extract coarse post-P&R QoR metrics from nextpnr report/log text."""

    metrics: dict[str, Any] = {
        "lut": 0,
        "ff": 0,
        "bram": 0,
        "dsp": 0,
        "fmax_mhz": None,
        "wns_ns": None,
    }
    json_metrics = _parse_json_report(report_text)
    metrics.update(json_metrics or _parse_log_report(report_text))
    return metrics


def _parse_log_report(report_text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    utilization = {"lut": 0, "ff": 0, "bram": 0, "dsp": 0}
    saw_utilization = False
    for line in report_text.splitlines():
        match = re.search(r"\b([A-Za-z0-9_$]+)\s*:\s*([0-9]+)\s*/", line)
        if not match:
            continue
        bucket = _resource_bucket(match.group(1))
        if bucket is None:
            continue
        utilization[bucket] += int(match.group(2))
        saw_utilization = True
    if saw_utilization:
        metrics.update(utilization)

    frequency_matches = re.findall(
        r"Max frequency for clock\b.*?:\s*([0-9]+(?:\.[0-9]+)?)\s*MHz"
        r"(?:\s*\((?:PASS|FAIL) at\s*([0-9]+(?:\.[0-9]+)?)\s*MHz\))?",
        report_text,
        re.IGNORECASE,
    )
    worst_frequency: tuple[str, str] | None = None
    if frequency_matches:
        worst_frequency = min(frequency_matches, key=lambda match: float(match[0]))
        metrics["fmax_mhz"] = float(worst_frequency[0])

    wns_match = re.search(r"\bWNS\b[^-+0-9]*([-+]?[0-9]+(?:\.[0-9]+)?)\s*ns", report_text, re.IGNORECASE)
    if wns_match:
        metrics["wns_ns"] = float(wns_match.group(1))
    elif worst_frequency and worst_frequency[1]:
        fmax_mhz = float(worst_frequency[0])
        target_mhz = float(worst_frequency[1])
        if fmax_mhz > 0 and target_mhz > 0:
            metrics["wns_ns"] = (1000.0 / target_mhz) - (1000.0 / fmax_mhz)
    return metrics


def _parse_json_report(report_text: str) -> dict[str, Any]:
    payload = _extract_json_payload(report_text)
    if payload is None:
        return {}

    metrics: dict[str, Any] = {}
    utilization = {"lut": 0, "ff": 0, "bram": 0, "dsp": 0}
    saw_utilization = False
    for key, value in _walk_json_items(payload):
        bucket = _resource_bucket(key)
        used = _used_count(value)
        if bucket is None or used is None:
            continue
        utilization[bucket] += used
        saw_utilization = True
    if saw_utilization:
        metrics.update(utilization)

    fmax = _find_numeric_by_key(payload, ("fmax", "max_frequency", "max_freq"))
    if fmax is not None:
        metrics["fmax_mhz"] = fmax
    wns = _find_numeric_by_key(payload, ("wns", "worst_negative_slack"))
    if wns is not None:
        metrics["wns_ns"] = wns
    for log_text in _json_log_strings(payload):
        metrics.update(_parse_log_report(log_text))
    return metrics


def _extract_json_payload(report_text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(report_text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for match in reversed(list(re.finditer(r"\{", report_text))):
            try:
                payload, _ = decoder.raw_decode(report_text, match.start())
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        return None
    return payload if isinstance(payload, dict) else None


def _resource_bucket(resource_name: str) -> str | None:
    name = resource_name.upper()
    if "DSP" in name:
        return "dsp"
    if "RAMB" in name or "BRAM" in name or name.startswith("FIFO18"):
        return "bram"
    if "LUT" in name and "LUTFF" not in name:
        return "lut"
    if ("FF" in name or name.endswith("FFX")) and "LUTFF" not in name:
        return "ff"
    return None


def _walk_json_items(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk_json_items(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json_items(child)


def _used_count(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if not isinstance(value, dict):
        return None
    for key in ("used", "count", "used_count"):
        item = value.get(key)
        if isinstance(item, int) and not isinstance(item, bool):
            return item
        if isinstance(item, float):
            return int(item)
    return None


def _find_numeric_by_key(value: Any, key_fragments: tuple[str, ...]) -> float | None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in key_fragments):
                number = _as_float(child)
                if number is not None:
                    return number
            found = _find_numeric_by_key(child, key_fragments)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_numeric_by_key(child, key_fragments)
            if found is not None:
                return found
    return None


def _json_log_strings(value: Any) -> list[str]:
    logs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, str) and str(key).lower() in {"log", "stdout", "stderr", "nextpnr_log"}:
                logs.append(child)
            else:
                logs.extend(_json_log_strings(child))
    elif isinstance(value, list):
        for child in value:
            logs.extend(_json_log_strings(child))
    return logs


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?[0-9]+(?:\.[0-9]+)?", value)
        if match:
            return float(match.group(0))
    return None
