"""Stable family metadata for basic deterministic generator tasks."""

from textwrap import dedent

TASK_FAMILY_IDS = {
    "counter": "binary_bcd_counter",
    "simple_fsm": "simple_fsm",
    "ram_read_write": "single_dual_port_ram",
}


def counter_rtl(width: int) -> str:
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


def counter_testbench(width: int) -> str:
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
              $display("TEST_FAIL signal=count cycle=4 expected=4 actual=%0d", count);
              $finish;
            end
            en = 1'b0;
            repeat (2) @(posedge clk);
            if (count !== {width}'d4) begin
              $display("TEST_FAIL signal=count cycle=6 expected=4 actual=%0d", count);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def simple_fsm_rtl(width: int) -> str:
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


def simple_fsm_testbench(width: int) -> str:
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
            repeat (6) @(posedge clk);
            @(negedge clk);
            if (done !== 1'b1) begin
              $display("TEST_FAIL fsm did not reach done");
              $finish;
            end
            start = 1'b0;
            repeat (2) @(posedge clk);
            @(negedge clk);
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


def ram_read_write_rtl(width: int) -> str:
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


def ram_read_write_testbench(width: int) -> str:
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

            // Write-first behavior is not allowed: the synchronous read returns
            // the old word on the write edge.
            @(negedge clk);
            addr = 2'd0;
            wdata = {width}'d17;
            we = 1'b1;
            @(negedge clk);
            if (rdata !== {width}'d0) begin
              $display("TEST_FAIL ram read_during_write expected=0 actual=%0d", rdata);
              $finish;
            end
            we = 1'b0;
            @(negedge clk);
            if (rdata !== {width}'d17) begin
              $display("TEST_FAIL ram sync_read expected=17 actual=%0d", rdata);
              $finish;
            end

            // Changing the address must not change rdata until a clock edge.
            addr = 2'd1;
            #1;
            if (rdata !== {width}'d17) begin
              $display("TEST_FAIL ram async_read_detected expected=17 actual=%0d", rdata);
              $finish;
            end
            @(negedge clk);
            if (rdata !== {width}'d0) begin
              $display("TEST_FAIL ram address1 expected=0 actual=%0d", rdata);
              $finish;
            end

            // Address 2 must be independent from address 0.
            @(negedge clk);
            addr = 2'd2;
            wdata = {width}'d99;
            we = 1'b1;
            @(negedge clk);
            we = 1'b0;
            @(negedge clk);
            if (rdata !== {width}'d99) begin
              $display("TEST_FAIL ram address2 expected=99 actual=%0d", rdata);
              $finish;
            end
            addr = 2'd0;
            @(negedge clk);
            if (rdata !== {width}'d17) begin
              $display("TEST_FAIL ram address0_preserved expected=17 actual=%0d", rdata);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )
