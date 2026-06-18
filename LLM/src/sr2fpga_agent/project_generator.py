"""Deterministic V1 project generator for small RTL tasks."""

from __future__ import annotations

import json
from textwrap import dedent

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


class ProjectGenerator:
    """Generate minimal Verilog RTL project packages."""

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        if request.task_type != "counter":
            raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
        if request.width <= 0:
            raise ValueError("width must be positive")

        files = {
            "system_his.json": _to_json(_system_his(request, platform)),
            "manifest.json": _to_json(_manifest(request, platform)),
            "rtl/top.v": _counter_rtl(request.width),
            "constraints/timing.sdc": _timing_sdc(platform),
            "sim/tb_top.v": _counter_testbench(request.width),
            "reports/predicted_qor.json": _to_json(_predicted_qor(request, platform)),
        }
        return GeneratedProject(project_name=request.project_name, files=files)


def _to_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _system_his(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    return {
        "project_name": request.project_name,
        "task_type": request.task_type,
        "system": {
            "description": request.description
            or f"Generate a {request.width}-bit synchronous counter with enable and active-low reset.",
        },
        "interface": {
            "clock": "clk",
            "reset": "rst_n",
            "reset_polarity": platform.reset_polarity,
            "inputs": [
                {"name": "clk", "width": 1},
                {"name": "rst_n", "width": 1},
                {"name": "en", "width": 1},
            ],
            "outputs": [{"name": "count", "width": request.width}],
        },
        "platform": {
            "name": platform.name,
            "vendor": platform.vendor,
            "family": platform.family,
            "part": platform.part,
            "board": platform.board,
            "toolchain": platform.toolchain,
            "clock_hz": platform.clock_hz,
        },
        "verification": {
            "testbench": "sim/tb_top.v",
            "expected_behavior": "count increments when en is high and holds when en is low",
        },
    }


def _manifest(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    return {
        "project_name": request.project_name,
        "top_module": "top",
        "language": "verilog",
        "target": {
            "vendor": platform.vendor,
            "family": platform.family,
            "part": platform.part,
            "board": platform.board,
            "toolchain": platform.toolchain,
        },
        "sources": ["rtl/top.v"],
        "constraints": {"timing": "constraints/timing.sdc"},
        "simulation": {"testbench": "sim/tb_top.v", "type": "self_checking"},
        "reports": {"predicted_qor": "reports/predicted_qor.json"},
        "clock": {"name": "clk", "frequency_hz": platform.clock_hz},
        "reset": {"name": "rst_n", "polarity": platform.reset_polarity},
    }


def _counter_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire en,
            output reg [{msb}:0] count
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              count <= {width}'d0;
            end else if (en) begin
              count <= count + {{ {width - 1}'d0, 1'b1 }};
            end
          end

        endmodule
        """
    )


def _timing_sdc(platform: PlatformProfile) -> str:
    period_ns = 1_000_000_000 / platform.clock_hz
    return f"create_clock -name clk -period {period_ns:.3f} [get_ports clk]\n"


def _counter_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg en;
          wire [{msb}:0] count;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .en(en),
            .count(count)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            en = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            en = 1'b1;
            repeat (4) @(posedge clk);
            if (count !== {width}'d4) begin
              $display("TEST_FAIL expected count=4 got %0d", count);
              $finish;
            end
            en = 1'b0;
            repeat (2) @(posedge clk);
            if (count !== {width}'d4) begin
              $display("TEST_FAIL hold failed got %0d", count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _predicted_qor(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    return {
        "project_name": request.project_name,
        "target": {
            "platform": platform.name,
            "vendor": platform.vendor,
            "toolchain": platform.toolchain,
        },
        "predicted": {
            "lut": max(1, request.width // 2),
            "ff": request.width,
            "bram": 0,
            "dsp": 0,
            "fmax_mhz": min(500.0, platform.clock_hz / 1_000_000 * 3),
            "confidence": 0.65,
        },
        "assumptions": {
            "counter_width": request.width,
            "single_clock": True,
            "no_vendor_ip": True,
            "estimate_type": "pre_synthesis_model_prediction",
        },
    }
