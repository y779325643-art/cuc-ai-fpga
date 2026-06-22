"""Deterministic V1 project generator for small RTL tasks."""

from __future__ import annotations

import json
from textwrap import dedent

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


class ProjectGenerator:
    """Generate minimal Verilog RTL project packages."""

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        if request.task_type not in {"counter", "fifo", "simple_fsm", "ram_read_write"}:
            raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
        if request.width <= 0:
            raise ValueError("width must be positive")

        files = {
            "system_his.json": _to_json(_system_his(request, platform)),
            "manifest.json": _to_json(_manifest(request, platform)),
            "rtl/top.v": _rtl(request),
            "constraints/timing.sdc": _timing_sdc(platform),
            "sim/tb_top.v": _testbench(request),
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
            or _default_description(request),
        },
        "interface": _interface(request, platform),
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
            "expected_behavior": _expected_behavior(request),
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


def _rtl(request: ProjectRequest) -> str:
    if request.task_type == "counter":
        return _counter_rtl(request.width)
    if request.task_type == "fifo":
        return _fifo_rtl(request.width)
    if request.task_type == "simple_fsm":
        return _simple_fsm_rtl(max(2, request.width))
    if request.task_type == "ram_read_write":
        return _ram_read_write_rtl(request.width)
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")


def _timing_sdc(platform: PlatformProfile) -> str:
    period_ns = 1_000_000_000 / platform.clock_hz
    return f"create_clock -name clk -period {period_ns:.3f} [get_ports clk]\n"


def _testbench(request: ProjectRequest) -> str:
    if request.task_type == "counter":
        return _counter_testbench(request.width)
    if request.task_type == "fifo":
        return _fifo_testbench(request.width)
    if request.task_type == "simple_fsm":
        return _simple_fsm_testbench(max(2, request.width))
    if request.task_type == "ram_read_write":
        return _ram_read_write_testbench(request.width)
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")


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


def _fifo_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire wr_en,
            input wire rd_en,
            input wire [{msb}:0] din,
            output reg [{msb}:0] dout,
            output wire full,
            output wire empty
        );

          reg [{msb}:0] mem [0:3];
          reg [1:0] wr_ptr;
          reg [1:0] rd_ptr;
          reg [2:0] count;

          assign full = (count == 3'd4);
          assign empty = (count == 3'd0);

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              wr_ptr <= 2'd0;
              rd_ptr <= 2'd0;
              count <= 3'd0;
              dout <= {width}'d0;
            end else begin
              if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 2'd1;
              end
              if (rd_en && !empty) begin
                dout <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 2'd1;
              end
              case ({{wr_en && !full, rd_en && !empty}})
                2'b10: count <= count + 3'd1;
                2'b01: count <= count - 3'd1;
                default: count <= count;
              endcase
            end
          end

        endmodule
        """
    )


def _fifo_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg wr_en;
          reg rd_en;
          reg [{msb}:0] din;
          wire [{msb}:0] dout;
          wire full;
          wire empty;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .wr_en(wr_en),
            .rd_en(rd_en),
            .din(din),
            .dout(dout),
            .full(full),
            .empty(empty)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b0;
            din = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            din = {width}'d42;
            wr_en = 1'b1;
            @(negedge clk);
            wr_en = 1'b0;
            if (empty !== 1'b0) begin
              $display("TEST_FAIL fifo should not be empty after write");
              $finish;
            end

            rd_en = 1'b1;
            @(negedge clk);
            rd_en = 1'b0;
            @(negedge clk);
            if (dout !== {width}'d42) begin
              $display("TEST_FAIL expected dout=42 got %0d", dout);
              $finish;
            end
            if (empty !== 1'b1) begin
              $display("TEST_FAIL fifo should be empty after read");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _simple_fsm_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            output reg done,
            output reg [{msb}:0] state_value
        );

          localparam [1:0] IDLE = 2'd0;
          localparam [1:0] RUN = 2'd1;
          localparam [1:0] DONE = 2'd2;

          reg [1:0] state;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              state <= IDLE;
              done <= 1'b0;
              state_value <= {width}'d0;
            end else begin
              case (state)
                IDLE: begin
                  done <= 1'b0;
                  state_value <= {width}'d0;
                  if (start) begin
                    state <= RUN;
                  end
                end
                RUN: begin
                  state_value <= state_value + {{ {width - 1}'d0, 1'b1 }};
                  if (state_value == {width}'d2) begin
                    state <= DONE;
                  end
                end
                DONE: begin
                  done <= 1'b1;
                  if (!start) begin
                    state <= IDLE;
                  end
                end
                default: begin
                  state <= IDLE;
                end
              endcase
            end
          end

        endmodule
        """
    )


def _simple_fsm_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          wire done;
          wire [{msb}:0] state_value;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .done(done),
            .state_value(state_value)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            @(negedge clk);
            start = 1'b1;
            repeat (5) @(posedge clk);
            if (done !== 1'b1) begin
              $display("TEST_FAIL fsm did not reach done");
              $finish;
            end
            @(negedge clk);
            start = 1'b0;
            repeat (2) @(posedge clk);
            if (done !== 1'b0) begin
              $display("TEST_FAIL fsm did not return to idle");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _ram_read_write_rtl(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire we,
            input wire [1:0] addr,
            input wire [{msb}:0] wdata,
            output reg [{msb}:0] rdata
        );

          reg [{msb}:0] mem [0:3];
          integer i;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              rdata <= {width}'d0;
              for (i = 0; i < 4; i = i + 1) begin
                mem[i] <= {width}'d0;
              end
            end else begin
              if (we) begin
                mem[addr] <= wdata;
              end
              rdata <= mem[addr];
            end
          end

        endmodule
        """
    )


def _ram_read_write_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg we;
          reg [1:0] addr;
          reg [{msb}:0] wdata;
          wire [{msb}:0] rdata;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .we(we),
            .addr(addr),
            .wdata(wdata),
            .rdata(rdata)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            we = 1'b0;
            addr = 2'd0;
            wdata = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            addr = 2'd2;
            wdata = {width}'d99;
            we = 1'b1;
            @(negedge clk);
            we = 1'b0;
            @(negedge clk);
            if (rdata !== {width}'d99) begin
              $display("TEST_FAIL expected rdata=99 got %0d", rdata);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _predicted_qor(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    resource_shape = _resource_shape(request)
    assumptions = {
        "data_width": request.width,
        "task_type": request.task_type,
        "single_clock": True,
        "no_vendor_ip": True,
        "estimate_type": "pre_synthesis_model_prediction",
    }
    if request.task_type == "counter":
        assumptions["counter_width"] = request.width
    return {
        "project_name": request.project_name,
        "target": {
            "platform": platform.name,
            "vendor": platform.vendor,
            "toolchain": platform.toolchain,
        },
        "predicted": {
            "lut": resource_shape["lut"],
            "ff": resource_shape["ff"],
            "bram": resource_shape["bram"],
            "dsp": resource_shape["dsp"],
            "fmax_mhz": min(500.0, platform.clock_hz / 1_000_000 * 3),
            "confidence": 0.65,
        },
        "assumptions": assumptions,
    }


def _default_description(request: ProjectRequest) -> str:
    descriptions = {
        "counter": f"Generate a {request.width}-bit synchronous counter with enable and active-low reset.",
        "fifo": f"Generate a {request.width}-bit synchronous FIFO with depth 4.",
        "simple_fsm": "Generate a simple three-state FSM with start and done handshake.",
        "ram_read_write": f"Generate a {request.width}-bit by 4-entry synchronous RAM read/write block.",
    }
    return descriptions[request.task_type]


def _interface(request: ProjectRequest, platform: PlatformProfile) -> dict[str, object]:
    common = {
        "clock": "clk",
        "reset": "rst_n",
        "reset_polarity": platform.reset_polarity,
    }
    if request.task_type == "counter":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "en", "width": 1},
                ],
                "outputs": [{"name": "count", "width": request.width}],
            }
        )
    elif request.task_type == "fifo":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "wr_en", "width": 1},
                    {"name": "rd_en", "width": 1},
                    {"name": "din", "width": request.width},
                ],
                "outputs": [
                    {"name": "dout", "width": request.width},
                    {"name": "full", "width": 1},
                    {"name": "empty", "width": 1},
                ],
            }
        )
    elif request.task_type == "simple_fsm":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                ],
                "outputs": [
                    {"name": "done", "width": 1},
                    {"name": "state_value", "width": max(2, request.width)},
                ],
            }
        )
    elif request.task_type == "ram_read_write":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "we", "width": 1},
                    {"name": "addr", "width": 2},
                    {"name": "wdata", "width": request.width},
                ],
                "outputs": [{"name": "rdata", "width": request.width}],
            }
        )
    return common


def _expected_behavior(request: ProjectRequest) -> str:
    expectations = {
        "counter": "count increments when en is high and holds when en is low",
        "fifo": "data written into the FIFO is read back in order",
        "simple_fsm": "FSM transitions from idle to run to done and back to idle",
        "ram_read_write": "data written to an address can be read back from the same address",
    }
    return expectations[request.task_type]


def _resource_shape(request: ProjectRequest) -> dict[str, int]:
    if request.task_type == "counter":
        return {"lut": max(1, request.width // 2), "ff": request.width, "bram": 0, "dsp": 0}
    if request.task_type == "fifo":
        return {"lut": max(4, request.width), "ff": request.width * 4 + 8, "bram": 0, "dsp": 0}
    if request.task_type == "simple_fsm":
        return {"lut": 6, "ff": max(2, request.width) + 3, "bram": 0, "dsp": 0}
    if request.task_type == "ram_read_write":
        return {"lut": max(4, request.width), "ff": request.width * 4 + request.width, "bram": 0, "dsp": 0}
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
