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
        "spi_master": ["clock_divider", "spi_master_core"],
        "pwm_controller": ["pwm_timer", "pwm_channel"],
        "fir_filter": ["mac_unit", "fir_filter_core"],
        "streaming_valid_ready": ["skid_buffer", "stream_stage"],
        "matrix_vector_mac": ["vector_rom", "mac_unit", "dot_product_engine"],
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
    if request.task_type == "spi_master":
        return _spi_master_testbench()
    if request.task_type == "pwm_controller":
        return _pwm_controller_testbench(request.width)
    if request.task_type == "fir_filter":
        return _fir_filter_testbench(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_testbench(request.width)
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_testbench(request.width)
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


def _spi_master_testbench() -> str:
    return dedent(
        """\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          reg [7:0] tx_data;
          reg miso;
          wire [7:0] rx_data;
          wire busy;
          wire done;
          wire sclk;
          wire mosi;
          wire cs_n;

          reg [7:0] miso_pattern;
          integer miso_bit;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .tx_data(tx_data),
            .miso(miso),
            .rx_data(rx_data),
            .busy(busy),
            .done(done),
            .sclk(sclk),
            .mosi(mosi),
            .cs_n(cs_n)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          always @(negedge sclk or posedge cs_n) begin
            if (cs_n) begin
              miso_bit = 7;
              miso = miso_pattern[7];
            end else if (miso_bit > 0) begin
              miso_bit = miso_bit - 1;
              miso = miso_pattern[miso_bit];
            end
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            tx_data = 8'd0;
            miso_pattern = 8'h3C;
            miso_bit = 7;
            miso = miso_pattern[7];
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            tx_data = 8'hA5;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            #1;
            if (busy !== 1'b1 || cs_n !== 1'b0) begin
              $display("TEST_FAIL transfer did not start");
              $finish;
            end
            if (mosi !== 1'b1) begin
              $display("TEST_FAIL expected first MOSI bit 1 got %0b", mosi);
              $finish;
            end

            while (done !== 1'b1) begin
              @(posedge clk);
            end
            #1;
            if (cs_n !== 1'b1) begin
              $display("TEST_FAIL cs_n was not released");
              $finish;
            end
            if (rx_data !== 8'h3C) begin
              $display("TEST_FAIL expected rx_data=3c got %02h", rx_data);
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


def _fir_filter_testbench(width: int) -> str:
    msb = width - 1
    result_msb = width + 2
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg sample_valid;
          reg [{msb}:0] sample;
          wire result_valid;
          wire [{result_msb}:0] result;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample(sample),
            .result_valid(result_valid),
            .result(result)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_and_expect;
            input [{msb}:0] value;
            input [{result_msb}:0] expected;
            begin
              @(negedge clk);
              sample = value;
              sample_valid = 1'b1;
              @(posedge clk);
              #1;
              if (result_valid !== 1'b1) begin
                $display("TEST_FAIL result_valid was not asserted");
                $finish;
              end
              if (result !== expected) begin
                $display("TEST_FAIL expected result=%0d got %0d", expected, result);
                $finish;
              end
              @(negedge clk);
              sample_valid = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            sample_valid = 1'b0;
            sample = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_and_expect({width}'d1, {width + 3}'d1);
            send_and_expect({width}'d2, {width + 3}'d4);
            send_and_expect({width}'d3, {width + 3}'d8);

            @(posedge clk);
            #1;
            if (result_valid !== 1'b0) begin
              $display("TEST_FAIL result_valid did not clear");
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def _matrix_vector_mac_testbench(width: int) -> str:
    result_msb = width + 3
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg start;
          wire busy;
          wire done;
          wire [{result_msb}:0] result;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .busy(busy),
            .done(done),
            .result(result)
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
            @(negedge clk);
            start = 1'b0;
            while (done !== 1'b1) begin
              @(posedge clk);
            end
            #1;
            if (busy !== 1'b0) begin
              $display("TEST_FAIL busy did not clear");
              $finish;
            end
            if (result !== {width + 4}'d17) begin
              $display("TEST_FAIL expected result=17 got %0d", result);
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
    top = dedent(
        """\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [7:0] tx_data,
            input wire miso,
            output wire [7:0] rx_data,
            output wire busy,
            output wire done,
            output wire sclk,
            output wire mosi,
            output wire cs_n
        );

          wire spi_tick;

          clock_divider u_clock_divider (
            .clk(clk),
            .rst_n(rst_n),
            .enable(busy),
            .tick(spi_tick)
          );

          spi_master_core u_spi_master_core (
            .clk(clk),
            .rst_n(rst_n),
            .tick(spi_tick),
            .start(start),
            .tx_data(tx_data),
            .miso(miso),
            .rx_data(rx_data),
            .busy(busy),
            .done(done),
            .sclk(sclk),
            .mosi(mosi),
            .cs_n(cs_n)
          );

        endmodule
        """
    )
    clock_divider = dedent(
        """\
        module clock_divider (
            input wire clk,
            input wire rst_n,
            input wire enable,
            output wire tick
        );

          reg div_count;

          assign tick = enable && div_count;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              div_count <= 1'b0;
            end else if (enable) begin
              div_count <= ~div_count;
            end else begin
              div_count <= 1'b0;
            end
          end

        endmodule
        """
    )
    spi_master_core = dedent(
        """\
        module spi_master_core (
            input wire clk,
            input wire rst_n,
            input wire tick,
            input wire start,
            input wire [7:0] tx_data,
            input wire miso,
            output reg [7:0] rx_data,
            output reg busy,
            output reg done,
            output reg sclk,
            output reg mosi,
            output reg cs_n
        );

          reg [2:0] bit_index;
          reg [7:0] tx_shift;
          reg [6:0] rx_shift;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              bit_index <= 3'd0;
              tx_shift <= 8'd0;
              rx_shift <= 7'd0;
              rx_data <= 8'd0;
              busy <= 1'b0;
              done <= 1'b0;
              sclk <= 1'b0;
              mosi <= 1'b0;
              cs_n <= 1'b1;
            end else begin
              done <= 1'b0;
              if (!busy) begin
                sclk <= 1'b0;
                cs_n <= 1'b1;
                bit_index <= 3'd0;
                if (start) begin
                  busy <= 1'b1;
                  cs_n <= 1'b0;
                  tx_shift <= {tx_data[6:0], 1'b0};
                  rx_shift <= 7'd0;
                  mosi <= tx_data[7];
                end
              end else if (tick) begin
                if (sclk == 1'b0) begin
                  sclk <= 1'b1;
                  rx_shift <= {rx_shift[5:0], miso};
                  if (bit_index == 3'd7) begin
                    rx_data <= {rx_shift, miso};
                    busy <= 1'b0;
                    done <= 1'b1;
                    sclk <= 1'b0;
                    cs_n <= 1'b1;
                  end
                end else begin
                  sclk <= 1'b0;
                  bit_index <= bit_index + 3'd1;
                  mosi <= tx_shift[7];
                  tx_shift <= {tx_shift[6:0], 1'b0};
                end
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/clock_divider.v": clock_divider,
        "rtl/spi_master_core.v": spi_master_core,
    }


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
    msb = width - 1
    result_msb = width + 2
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            input wire [{msb}:0] sample,
            output wire result_valid,
            output wire [{result_msb}:0] result
        );

          // fir_filter_core contains the mac_unit tap helpers.
          fir_filter_core #(
            .WIDTH({width}),
            .RESULT_WIDTH({width + 3})
          ) u_fir_filter_core (
            .clk(clk),
            .rst_n(rst_n),
            .sample_valid(sample_valid),
            .sample(sample),
            .result_valid(result_valid),
            .result(result)
          );

        endmodule
        """
    )
    fir_filter_core = dedent(
        """\
        module fir_filter_core #(
            parameter WIDTH = 8,
            parameter RESULT_WIDTH = 11
        ) (
            input wire clk,
            input wire rst_n,
            input wire sample_valid,
            input wire [WIDTH-1:0] sample,
            output reg result_valid,
            output reg [RESULT_WIDTH-1:0] result
        );

          reg [WIDTH-1:0] sample_d0;
          reg [WIDTH-1:0] sample_d1;
          wire [RESULT_WIDTH-1:0] stage0;
          wire [RESULT_WIDTH-1:0] stage1;
          wire [RESULT_WIDTH-1:0] filtered_result;

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_new_sample (
            .sample(sample),
            .coefficient(2'd1),
            .accum({RESULT_WIDTH{1'b0}}),
            .result(stage0)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_previous_sample (
            .sample(sample_d0),
            .coefficient(2'd2),
            .accum(stage0),
            .result(stage1)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_oldest_sample (
            .sample(sample_d1),
            .coefficient(2'd1),
            .accum(stage1),
            .result(filtered_result)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sample_d0 <= {WIDTH{1'b0}};
              sample_d1 <= {WIDTH{1'b0}};
              result_valid <= 1'b0;
              result <= {RESULT_WIDTH{1'b0}};
            end else begin
              result_valid <= sample_valid;
              if (sample_valid) begin
                result <= filtered_result;
                sample_d1 <= sample_d0;
                sample_d0 <= sample;
              end
            end
          end

        endmodule
        """
    )
    mac_unit = dedent(
        """\
        module mac_unit #(
            parameter WIDTH = 8,
            parameter ACC_WIDTH = 11
        ) (
            input wire [WIDTH-1:0] sample,
            input wire [1:0] coefficient,
            input wire [ACC_WIDTH-1:0] accum,
            output wire [ACC_WIDTH-1:0] result
        );

          wire [ACC_WIDTH-1:0] extended_sample;
          wire [ACC_WIDTH-1:0] product_x1;
          wire [ACC_WIDTH-1:0] product_x2;

          assign extended_sample = {{(ACC_WIDTH-WIDTH){1'b0}}, sample};
          assign product_x1 = coefficient[0] ? extended_sample : {ACC_WIDTH{1'b0}};
          assign product_x2 = coefficient[1] ? (extended_sample << 1) : {ACC_WIDTH{1'b0}};
          assign result = accum + product_x1 + product_x2;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/fir_filter_core.v": fir_filter_core,
        "rtl/mac_unit.v": mac_unit,
    }


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
    result_msb = width + 3
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            output wire busy,
            output wire done,
            output wire [{result_msb}:0] result
        );

          // dot_product_engine contains mac_unit and vector_rom instances.
          dot_product_engine #(
            .WIDTH({width}),
            .RESULT_WIDTH({width + 4})
          ) u_dot_product_engine (
            .clk(clk),
            .rst_n(rst_n),
            .start(start),
            .busy(busy),
            .done(done),
            .result(result)
          );

        endmodule
        """
    )
    dot_product_engine = dedent(
        """\
        module dot_product_engine #(
            parameter WIDTH = 8,
            parameter RESULT_WIDTH = 12
        ) (
            input wire clk,
            input wire rst_n,
            input wire start,
            output reg busy,
            output reg done,
            output reg [RESULT_WIDTH-1:0] result
        );

          reg [1:0] index;
          reg [RESULT_WIDTH-1:0] accum;
          reg [WIDTH-1:0] vector_value;
          wire [1:0] coefficient;
          wire [RESULT_WIDTH-1:0] next_accum;

          vector_rom u_vector_rom (
            .addr(index),
            .coefficient(coefficient)
          );

          mac_unit #(
            .WIDTH(WIDTH),
            .ACC_WIDTH(RESULT_WIDTH)
          ) u_mac_unit (
            .sample(vector_value),
            .coefficient(coefficient),
            .accum(accum),
            .result(next_accum)
          );

          always @* begin
            case (index)
              2'd0: vector_value = {{(WIDTH-1){1'b0}}, 1'b1};
              2'd1: vector_value = {{(WIDTH-2){1'b0}}, 2'd2};
              2'd2: vector_value = {{(WIDTH-2){1'b0}}, 2'd3};
              default: vector_value = {{(WIDTH-3){1'b0}}, 3'd4};
            endcase
          end

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              index <= 2'd0;
              accum <= {RESULT_WIDTH{1'b0}};
              busy <= 1'b0;
              done <= 1'b0;
              result <= {RESULT_WIDTH{1'b0}};
            end else begin
              done <= 1'b0;
              if (!busy) begin
                index <= 2'd0;
                accum <= {RESULT_WIDTH{1'b0}};
                if (start) begin
                  busy <= 1'b1;
                end
              end else begin
                accum <= next_accum;
                if (index == 2'd3) begin
                  result <= next_accum;
                  busy <= 1'b0;
                  done <= 1'b1;
                  index <= 2'd0;
                end else begin
                  index <= index + 2'd1;
                end
              end
            end
          end

        endmodule
        """
    )
    mac_unit = dedent(
        """\
        module mac_unit #(
            parameter WIDTH = 8,
            parameter ACC_WIDTH = 12
        ) (
            input wire [WIDTH-1:0] sample,
            input wire [1:0] coefficient,
            input wire [ACC_WIDTH-1:0] accum,
            output wire [ACC_WIDTH-1:0] result
        );

          wire [ACC_WIDTH-1:0] extended_sample;
          wire [ACC_WIDTH-1:0] product_x1;
          wire [ACC_WIDTH-1:0] product_x2;

          assign extended_sample = {{(ACC_WIDTH-WIDTH){1'b0}}, sample};
          assign product_x1 = coefficient[0] ? extended_sample : {ACC_WIDTH{1'b0}};
          assign product_x2 = coefficient[1] ? (extended_sample << 1) : {ACC_WIDTH{1'b0}};
          assign result = accum + product_x1 + product_x2;

        endmodule
        """
    )
    vector_rom = dedent(
        """\
        module vector_rom (
            input wire [1:0] addr,
            output reg [1:0] coefficient
        );

          always @* begin
            case (addr)
              2'd0: coefficient = 2'd2;
              2'd1: coefficient = 2'd1;
              2'd2: coefficient = 2'd3;
              default: coefficient = 2'd1;
            endcase
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/dot_product_engine.v": dot_product_engine,
        "rtl/mac_unit.v": mac_unit,
        "rtl/vector_rom.v": vector_rom,
    }


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
        "spi_master": "Generate an 8-bit SPI master with clock division and shift engine.",
        "pwm_controller": f"Generate a {request.width}-bit PWM controller with timer and channel modules.",
        "fir_filter": f"Generate a {request.width}-bit three-tap FIR filter with MAC helpers.",
        "streaming_valid_ready": (
            f"Generate a {request.width}-bit valid-ready streaming pipeline with buffering."
        ),
        "matrix_vector_mac": f"Generate a {request.width}-bit fixed matrix-vector dot product engine.",
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
    elif request.task_type == "spi_master":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                    {"name": "tx_data", "width": 8},
                    {"name": "miso", "width": 1},
                ],
                "outputs": [
                    {"name": "rx_data", "width": 8},
                    {"name": "busy", "width": 1},
                    {"name": "done", "width": 1},
                    {"name": "sclk", "width": 1},
                    {"name": "mosi", "width": 1},
                    {"name": "cs_n", "width": 1},
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
    elif request.task_type == "fir_filter":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "sample_valid", "width": 1},
                    {"name": "sample", "width": request.width},
                ],
                "outputs": [
                    {"name": "result_valid", "width": 1},
                    {"name": "result", "width": request.width + 3},
                ],
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
    elif request.task_type == "matrix_vector_mac":
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "start", "width": 1},
                ],
                "outputs": [
                    {"name": "busy", "width": 1},
                    {"name": "done", "width": 1},
                    {"name": "result", "width": request.width + 4},
                ],
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
        "spi_master": "start launches an 8-bit MSB-first SPI transfer and captures MISO data",
        "pwm_controller": "pwm_out is high when the free-running counter is below duty",
        "fir_filter": "valid input samples produce a three-tap [1, 2, 1] FIR result",
        "streaming_valid_ready": "valid-ready transfers preserve data order across stalls",
        "matrix_vector_mac": "start computes the fixed four-element dot product and pulses done",
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
