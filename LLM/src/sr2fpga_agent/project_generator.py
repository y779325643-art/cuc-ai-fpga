"""Deterministic V1 project generator for small RTL tasks."""

from __future__ import annotations

import json
from textwrap import dedent

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


SUPPORTED_TASK_TYPES = {
    "counter",
    "fifo",
    "simple_fsm",
    "ram_read_write",
    "uart_tx",
    "spi_master",
    "pwm_controller",
    "fir_filter",
    "streaming_valid_ready",
    "matrix_vector_mac",
}

TRANSITIONAL_PASSTHROUGH_TASK_TYPES = {
    "spi_master",
    "fir_filter",
    "matrix_vector_mac",
}


class ProjectGenerator:
    """Generate minimal Verilog RTL project packages."""

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        if request.task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
        if request.width <= 0:
            raise ValueError("width must be positive")

        rtl_files = _rtl_files(request)
        files = {
            "system_his.json": _to_json(_system_his(request, platform)),
            "manifest.json": _to_json(_manifest(request, platform, rtl_files)),
            **rtl_files,
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
        "architecture": _architecture(request),
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


def _architecture(request: ProjectRequest) -> dict[str, object]:
    submodules = {
        "counter": [],
        "fifo": [],
        "simple_fsm": [],
        "ram_read_write": [],
        "uart_tx": ["baud_tick_gen", "uart_tx_core"],
        "spi_master": ["spi_master_core"],
        "pwm_controller": ["pwm_timer", "pwm_channel"],
        "fir_filter": ["fir_filter_core"],
        "streaming_valid_ready": ["skid_buffer", "stream_stage"],
        "matrix_vector_mac": ["matrix_vector_mac_core"],
    }
    return {
        "style": "multi_module" if submodules[request.task_type] else "single_module",
        "top_module": "top",
        "submodules": submodules[request.task_type],
    }


def _manifest(
    request: ProjectRequest,
    platform: PlatformProfile,
    rtl_files: dict[str, str] | None = None,
) -> dict[str, object]:
    sources = list((rtl_files or {"rtl/top.v": ""}).keys())
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
        "sources": sources,
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


def _rtl_files(request: ProjectRequest) -> dict[str, str]:
    if request.task_type == "counter":
        return {"rtl/top.v": _counter_rtl(request.width)}
    if request.task_type == "fifo":
        return {"rtl/top.v": _fifo_rtl(request.width)}
    if request.task_type == "simple_fsm":
        return {"rtl/top.v": _simple_fsm_rtl(max(2, request.width))}
    if request.task_type == "ram_read_write":
        return {"rtl/top.v": _ram_read_write_rtl(request.width)}
    if request.task_type == "uart_tx":
        return _uart_tx_rtl_files(request.width)
    if request.task_type == "spi_master":
        return _spi_master_rtl_files(request.width)
    if request.task_type == "pwm_controller":
        return _pwm_controller_rtl_files(request.width)
    if request.task_type == "fir_filter":
        return _fir_filter_rtl_files(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_rtl_files(request.width)
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_rtl_files(request.width)
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")


def _rtl(request: ProjectRequest) -> str:
    return _rtl_files(request)["rtl/top.v"]


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
    if request.task_type == "uart_tx":
        return _uart_tx_testbench()
    if request.task_type == "pwm_controller":
        return _pwm_controller_testbench(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_testbench(request.width)
    if request.task_type in TRANSITIONAL_PASSTHROUGH_TASK_TYPES:
        return _passthrough_testbench(request.width)
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


def _passthrough_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg [{msb}:0] din;
          wire [{msb}:0] dout;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .din(din),
            .dout(dout)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            din = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            din = {width}'d165;
            #1;
            if (dout !== {width}'d165) begin
              $display("TEST_FAIL expected dout=165 got %0d", dout);
              $finish;
            end

            @(negedge clk);
            din = {width}'d90;
            #1;
            if (dout !== {width}'d90) begin
              $display("TEST_FAIL expected dout=90 got %0d", dout);
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _uart_tx_testbench() -> str:
    return dedent(
        """\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          reg [7:0] data;
          wire tx;
          wire busy;
          wire done;
          reg [7:0] expected_bits;
          integer i;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .data(data),
            .tx(tx),
            .busy(busy),
            .done(done)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            data = 8'd0;
            expected_bits = 8'hA5;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            data = 8'hA5;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            #1;
            if (tx !== 1'b0) begin
              $display("TEST_FAIL start bit expected 0 got %0b", tx);
              $finish;
            end
            if (busy !== 1'b1) begin
              $display("TEST_FAIL busy was not asserted");
              $finish;
            end

            for (i = 0; i < 8; i = i + 1) begin
              repeat (4) @(posedge clk);
              #1;
              if (tx !== expected_bits[i]) begin
                $display(
                  "TEST_FAIL data bit %0d expected %0b got %0b",
                  i,
                  expected_bits[i],
                  tx
                );
                $finish;
              end
            end

            repeat (4) @(posedge clk);
            #1;
            if (tx !== 1'b1) begin
              $display("TEST_FAIL stop bit expected 1 got %0b", tx);
              $finish;
            end

            repeat (4) @(posedge clk);
            #1;
            if (done !== 1'b1) begin
              $display("TEST_FAIL done was not asserted");
              $finish;
            end
            if (busy !== 1'b0) begin
              $display("TEST_FAIL busy did not clear");
              $finish;
            end
            @(posedge clk);
            #1;
            if (done !== 1'b0) begin
              $display("TEST_FAIL done was not one cycle");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _pwm_controller_testbench(width: int) -> str:
    msb = width - 1
    duty_value = 3 if width >= 3 else max(1, (1 << width) - 1)
    sample_cycles = 8 if width >= 3 else 1 << width
    expected_high = 3 if width >= 3 else duty_value
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg [{msb}:0] duty;
          wire pwm_out;
          integer high_count;
          integer i;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .duty(duty),
            .pwm_out(pwm_out)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            duty = {width}'d{duty_value};
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;

            high_count = 0;
            #1;
            if (pwm_out === 1'b1) begin
              high_count = high_count + 1;
            end
            for (i = 1; i < {sample_cycles}; i = i + 1) begin
              @(posedge clk);
              #1;
              if (pwm_out === 1'b1) begin
                high_count = high_count + 1;
              end
            end

            if (high_count != {expected_high}) begin
              $display("TEST_FAIL expected %0d high cycles got %0d", {expected_high}, high_count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _streaming_valid_ready_testbench(width: int) -> str:
    msb = width - 1
    mask = (1 << width) - 1
    first_value = 0x12 & mask
    second_value = 0xA5 & mask
    if first_value == second_value:
        second_value = (~first_value) & mask
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [{msb}:0] in_data;
          wire out_valid;
          reg out_ready;
          wire [{msb}:0] out_data;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_word;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              in_data = value;
              in_valid = 1'b1;
              while (in_ready !== 1'b1) begin
                @(negedge clk);
              end
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_word;
            input [{msb}:0] value;
            begin
              while (out_valid !== 1'b1) begin
                @(posedge clk);
              end
              #1;
              if (out_data !== value) begin
                $display("TEST_FAIL expected output %0d got %0d", value, out_data);
                $finish;
              end
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            in_data = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_word({width}'d{first_value});
            expect_word({width}'d{first_value});
            @(posedge clk);
            #1;

            out_ready = 1'b0;
            send_word({width}'d{second_value});
            repeat (2) @(posedge clk);
            #1;
            if (out_valid !== 1'b1) begin
              $display("TEST_FAIL stalled output was not held valid");
              $finish;
            end
            out_ready = 1'b1;
            expect_word({width}'d{second_value});
            @(posedge clk);
            #1;

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _simple_passthrough_multimodule(task_name: str, width: int, submodule_name: str) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] din,
            output wire [{msb}:0] dout
        );

          {submodule_name} u_core (
            .clk(clk),
            .rst_n(rst_n),
            .din(din),
            .dout(dout)
          );

        endmodule
        """
    )
    core = dedent(
        f"""\
        module {submodule_name} (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] din,
            output wire [{msb}:0] dout
        );

          assign dout = rst_n ? din : {{{width}{{clk}}}};

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        f"rtl/{task_name}_core.v": core,
    }


def _uart_tx_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        """\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [7:0] data,
            output wire tx,
            output wire busy,
            output wire done
        );

          wire baud_tick;

          baud_tick_gen u_baud_tick_gen (
            .clk(clk),
            .rst_n(rst_n),
            .enable(busy),
            .tick(baud_tick)
          );

          uart_tx_core u_uart_tx_core (
            .clk(clk),
            .rst_n(rst_n),
            .baud_tick(baud_tick),
            .start(start),
            .data(data),
            .tx(tx),
            .busy(busy),
            .done(done)
          );

        endmodule
        """
    )
    baud_tick_gen = dedent(
        """\
        module baud_tick_gen (
            input wire clk,
            input wire rst_n,
            input wire enable,
            output wire tick
        );

          reg [1:0] div_count;

          assign tick = enable && (div_count == 2'd3);

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              div_count <= 2'd0;
            end else if (enable) begin
              div_count <= div_count + 2'd1;
            end else begin
              div_count <= 2'd0;
            end
          end

        endmodule
        """
    )
    uart_tx_core = dedent(
        """\
        module uart_tx_core (
            input wire clk,
            input wire rst_n,
            input wire baud_tick,
            input wire start,
            input wire [7:0] data,
            output reg tx,
            output reg busy,
            output reg done
        );

          localparam [1:0] IDLE = 2'd0;
          localparam [1:0] DATA = 2'd1;
          localparam [1:0] STOP = 2'd2;
          localparam [1:0] CLEANUP = 2'd3;

          reg [1:0] state;
          reg [2:0] bit_index;
          reg [7:0] shifter;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              state <= IDLE;
              bit_index <= 3'd0;
              shifter <= 8'd0;
              tx <= 1'b1;
              busy <= 1'b0;
              done <= 1'b0;
            end else begin
              done <= 1'b0;
              case (state)
                IDLE: begin
                  tx <= 1'b1;
                  busy <= 1'b0;
                  bit_index <= 3'd0;
                  if (start) begin
                    shifter <= data;
                    tx <= 1'b0;
                    busy <= 1'b1;
                    state <= DATA;
                  end
                end
                DATA: begin
                  if (baud_tick) begin
                    tx <= shifter[0];
                    shifter <= {1'b0, shifter[7:1]};
                    if (bit_index == 3'd7) begin
                      bit_index <= 3'd0;
                      state <= STOP;
                    end else begin
                      bit_index <= bit_index + 3'd1;
                    end
                  end
                end
                STOP: begin
                  if (baud_tick) begin
                    tx <= 1'b1;
                    state <= CLEANUP;
                  end
                end
                CLEANUP: begin
                  if (baud_tick) begin
                    tx <= 1'b1;
                    busy <= 1'b0;
                    done <= 1'b1;
                    state <= IDLE;
                  end
                end
                default: begin
                  state <= IDLE;
                  tx <= 1'b1;
                  busy <= 1'b0;
                end
              endcase
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/baud_tick_gen.v": baud_tick_gen,
        "rtl/uart_tx_core.v": uart_tx_core,
    }


def _spi_master_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("spi_master", width, "spi_master_core")


def _pwm_controller_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] duty,
            output wire pwm_out
        );

          wire [{msb}:0] counter;

          pwm_timer #(
            .WIDTH({width})
          ) u_pwm_timer (
            .clk(clk),
            .rst_n(rst_n),
            .counter(counter)
          );

          pwm_channel #(
            .WIDTH({width})
          ) u_pwm_channel (
            .counter(counter),
            .duty(duty),
            .pwm_out(pwm_out)
          );

        endmodule
        """
    )
    pwm_timer = dedent(
        """\
        module pwm_timer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            output reg [WIDTH-1:0] counter
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              counter <= {WIDTH{1'b0}};
            end else begin
              counter <= counter + {{(WIDTH-1){1'b0}}, 1'b1};
            end
          end

        endmodule
        """
    )
    pwm_channel = dedent(
        """\
        module pwm_channel #(
            parameter WIDTH = 8
        ) (
            input wire [WIDTH-1:0] counter,
            input wire [WIDTH-1:0] duty,
            output wire pwm_out
        );

          assign pwm_out = (counter < duty);

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/pwm_timer.v": pwm_timer,
        "rtl/pwm_channel.v": pwm_channel,
    }


def _fir_filter_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("fir_filter", width, "fir_filter_core")


def _streaming_valid_ready_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [{msb}:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [{msb}:0] out_data
        );

          wire skid_valid;
          wire skid_ready;
          wire [{msb}:0] skid_data;

          skid_buffer #(
            .WIDTH({width})
          ) u_skid_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .out_valid(skid_valid),
            .out_ready(skid_ready),
            .out_data(skid_data)
          );

          stream_stage #(
            .WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(skid_valid),
            .in_ready(skid_ready),
            .in_data(skid_data),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_data(out_data)
          );

        endmodule
        """
    )
    skid_buffer = dedent(
        """\
        module skid_buffer #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output wire out_valid,
            input wire out_ready,
            output wire [WIDTH-1:0] out_data
        );

          reg valid_r;
          reg [WIDTH-1:0] data_r;

          assign in_ready = !valid_r || out_ready;
          assign out_valid = valid_r;
          assign out_data = data_r;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_r <= 1'b0;
              data_r <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              valid_r <= in_valid;
              if (in_valid) begin
                data_r <= in_data;
              end
            end
          end

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [WIDTH-1:0] in_data,
            output reg out_valid,
            input wire out_ready,
            output reg [WIDTH-1:0] out_data
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              out_data <= {WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                out_data <= in_data;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/skid_buffer.v": skid_buffer,
        "rtl/stream_stage.v": stream_stage,
    }


def _matrix_vector_mac_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("matrix_vector_mac", width, "matrix_vector_mac_core")


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
        "uart_tx": "Generate an 8-bit UART transmitter with baud tick generation.",
        "spi_master": f"Generate a transitional {request.width}-bit SPI master multi-module package.",
        "pwm_controller": f"Generate a {request.width}-bit PWM controller with timer and channel modules.",
        "fir_filter": f"Generate a transitional {request.width}-bit FIR filter multi-module package.",
        "streaming_valid_ready": (
            f"Generate a {request.width}-bit valid-ready streaming pipeline with buffering."
        ),
        "matrix_vector_mac": f"Generate a transitional {request.width}-bit matrix-vector MAC multi-module package.",
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
    elif request.task_type == "uart_tx":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                    {"name": "data", "width": 8},
                ],
                "outputs": [
                    {"name": "tx", "width": 1},
                    {"name": "busy", "width": 1},
                    {"name": "done", "width": 1},
                ],
            }
        )
    elif request.task_type == "pwm_controller":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "duty", "width": request.width},
                ],
                "outputs": [{"name": "pwm_out", "width": 1}],
            }
        )
    elif request.task_type == "streaming_valid_ready":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "in_valid", "width": 1},
                    {"name": "in_data", "width": request.width},
                    {"name": "out_ready", "width": 1},
                ],
                "outputs": [
                    {"name": "in_ready", "width": 1},
                    {"name": "out_valid", "width": 1},
                    {"name": "out_data", "width": request.width},
                ],
            }
        )
    elif request.task_type in TRANSITIONAL_PASSTHROUGH_TASK_TYPES:
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "din", "width": request.width},
                ],
                "outputs": [{"name": "dout", "width": request.width}],
            }
        )
    return common


def _expected_behavior(request: ProjectRequest) -> str:
    expectations = {
        "counter": "count increments when en is high and holds when en is low",
        "fifo": "data written into the FIFO is read back in order",
        "simple_fsm": "FSM transitions from idle to run to done and back to idle",
        "ram_read_write": "data written to an address can be read back from the same address",
        "uart_tx": "start launches an 8-bit LSB-first UART frame with start and stop bits",
        "spi_master": "transitional core passes din through to dout",
        "pwm_controller": "pwm_out is high when the free-running counter is below duty",
        "fir_filter": "transitional core passes din through to dout",
        "streaming_valid_ready": "valid-ready transfers preserve data order across stalls",
        "matrix_vector_mac": "transitional core passes din through to dout",
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
    if request.task_type == "uart_tx":
        return {"lut": max(12, request.width * 2), "ff": request.width + 16, "bram": 0, "dsp": 0}
    if request.task_type == "spi_master":
        return {"lut": max(16, request.width * 2), "ff": request.width * 2 + 16, "bram": 0, "dsp": 0}
    if request.task_type == "pwm_controller":
        return {"lut": max(8, request.width), "ff": request.width * 2, "bram": 0, "dsp": 0}
    if request.task_type == "fir_filter":
        return {"lut": max(20, request.width * 3), "ff": request.width * 3, "bram": 0, "dsp": 2}
    if request.task_type == "streaming_valid_ready":
        return {"lut": max(10, request.width), "ff": request.width * 2 + 4, "bram": 0, "dsp": 0}
    if request.task_type == "matrix_vector_mac":
        return {"lut": max(24, request.width * 4), "ff": request.width * 4, "bram": 0, "dsp": 2}
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
