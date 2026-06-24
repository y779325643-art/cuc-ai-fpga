"""Synthetic failure injectors for SR2FPGA repair trajectory generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


@dataclass(frozen=True)
class FailureInjectingProjectGenerator:
    """Wrap a project generator and apply named synthetic failures."""

    base_generator: object
    injectors: list[str]

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        project = self.base_generator.generate(request, platform)
        return apply_failure_injectors(project, self.injectors)


def apply_failure_injectors(project: GeneratedProject, injectors: list[str]) -> GeneratedProject:
    files = dict(project.files)
    for injector in injectors:
        if injector == "rename_reset_port":
            files = _rename_reset_port(files)
        elif injector == "missing_manifest_source":
            files = _missing_manifest_source(files)
        elif injector == "wrong_top_module":
            files = _wrong_top_module(files)
        elif injector == "width_mismatch":
            files = _width_mismatch(files)
        elif injector == "testbench_expected_value_mismatch":
            files = _testbench_expected_value_mismatch(files)
        elif injector == "constraint_missing_clock":
            files = _constraint_missing_clock(files)
        elif injector == "multimodule_connection_mismatch":
            files = _multimodule_connection_mismatch(files)
        else:
            raise ValueError(f"Unsupported failure injector: {injector}")
    return GeneratedProject(project_name=project.project_name, files=files)


def _rename_reset_port(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("rename_reset_port requires rtl/top.v")
    updated[top_path] = top_rtl.replace("rst_n", "reset_n", 1)
    return updated


def _missing_manifest_source(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    manifest = _load_manifest(updated)
    sources = list(manifest["sources"])
    missing_source = "rtl/missing_dependency.v"
    if missing_source not in sources:
        sources.append(missing_source)
    manifest["sources"] = sources
    updated["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return updated


def _wrong_top_module(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    manifest = _load_manifest(updated)
    manifest["top_module"] = "missing_top"
    updated["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return updated


def _width_mismatch(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("width_mismatch requires rtl/top.v")
    match = re.search(r"output reg \[(\d+):0\] count", top_rtl)
    if match is None:
        raise ValueError("width_mismatch requires a counter-style count port")
    old = match.group(0)
    new = f"output reg [{int(match.group(1)) + 1}:0] count"
    updated[top_path] = top_rtl.replace(old, new, 1)
    return updated


def _testbench_expected_value_mismatch(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    testbench_path = "sim/tb_top.v"
    testbench = updated.get(testbench_path)
    if testbench is None:
        raise ValueError("testbench_expected_value_mismatch requires sim/tb_top.v")
    updated[testbench_path] = _replace_once(
        testbench,
        "count !== 4'd4",
        "count !== 4'd5",
        "testbench_expected_value_mismatch requires a 4-bit counter self-check",
    )
    return updated


def _constraint_missing_clock(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    sdc_path = "constraints/timing.sdc"
    if sdc_path not in updated:
        raise ValueError("constraint_missing_clock requires constraints/timing.sdc")
    updated[sdc_path] = "create_clock -name missing_clk -period 10.000 [get_ports missing_clk]\n"
    return updated


def _multimodule_connection_mismatch(files: dict[str, str]) -> dict[str, str]:
    updated = dict(files)
    top_path = "rtl/top.v"
    top_rtl = updated.get(top_path)
    if top_rtl is None:
        raise ValueError("multimodule_connection_mismatch requires rtl/top.v")
    replacements = [
        ("uart_tx_core u_uart_tx_core", "uart_tx_core_missing u_uart_tx_core"),
        ("spi_master_core u_spi_master_core", "spi_master_core_missing u_spi_master_core"),
        ("pwm_channel u_pwm_channel", "pwm_channel_missing u_pwm_channel"),
        ("fir_filter_core u_fir_filter_core", "fir_filter_core_missing u_fir_filter_core"),
        ("stream_stage u_stream_stage", "stream_stage_missing u_stream_stage"),
        ("dot_product_engine u_dot_product_engine", "dot_product_engine_missing u_dot_product_engine"),
    ]
    for old, new in replacements:
        if old in top_rtl:
            updated[top_path] = top_rtl.replace(old, new, 1)
            return updated
    raise ValueError("multimodule_connection_mismatch requires a known multi-module top instantiation")


def _replace_once(text: str, old: str, new: str, error_message: str) -> str:
    if old not in text:
        raise ValueError(error_message)
    return text.replace(old, new, 1)


def _load_manifest(files: dict[str, str]) -> dict[str, object]:
    try:
        manifest = json.loads(files["manifest.json"])
    except KeyError as exc:
        raise ValueError("failure injector requires manifest.json") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc
    if not isinstance(manifest.get("sources"), list):
        raise ValueError("manifest.json must contain sources list")
    return manifest
