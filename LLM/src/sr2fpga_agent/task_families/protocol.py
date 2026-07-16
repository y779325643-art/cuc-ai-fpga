"""Stable family metadata for protocol and interface generator tasks."""

from textwrap import dedent

TASK_FAMILY_IDS = {
    "fifo": "sync_fifo",
    "uart_tx": "uart_tx",
    "uart_rx": "uart_rx",
    "uart_fifo_loopback": "uart_fifo_loopback",
    "spi_master": "spi_master",
}


def fifo_rtl(width: int) -> str:
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


def fifo_testbench(width: int) -> str:
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

          task write_word;
            input [{msb}:0] value;
            begin
              @(negedge clk);
              din = value;
              wr_en = 1'b1;
              @(negedge clk);
              wr_en = 1'b0;
              #1;
            end
          endtask

          task read_expect;
            input [{msb}:0] expected;
            begin
              @(negedge clk);
              rd_en = 1'b1;
              @(negedge clk);
              rd_en = 1'b0;
              #1;
              if (dout !== expected) begin
                $display("TEST_FAIL expected dout=%0d got %0d", expected, dout);
                $finish;
              end
            end
          endtask

          initial begin
            rst_n = 1'b0;
            wr_en = 1'b0;
            rd_en = 1'b0;
            din = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_word({width}'d10);
            write_word({width}'d11);
            write_word({width}'d12);
            write_word({width}'d13);
            if (full !== 1'b1) begin
              $display("TEST_FAIL fifo should be full after four writes");
              $finish;
            end

            write_word({width}'d99);
            @(negedge clk);
            rd_en = 1'b1;
            @(negedge clk);
            rd_en = 1'b0;
            #1;
            if (dout !== {width}'d10) begin
              $display("TEST_FAIL overflow guard changed stored data");
              $finish;
            end
            read_expect({width}'d11);
            read_expect({width}'d12);
            read_expect({width}'d13);

            if (empty !== 1'b1) begin
              $display("TEST_FAIL fifo should be empty after four reads");
              $finish;
            end
            @(negedge clk);
            rd_en = 1'b1;
            @(negedge clk);
            rd_en = 1'b0;
            write_word({width}'d77);
            @(negedge clk);
            rd_en = 1'b1;
            @(negedge clk);
            rd_en = 1'b0;
            #1;
            if (dout !== {width}'d77) begin
              $display("TEST_FAIL underflow guard advanced read pointer");
              $finish;
            end

            write_word({width}'d21);
            @(negedge clk);
            din = {width}'d22;
            wr_en = 1'b1;
            rd_en = 1'b1;
            @(negedge clk);
            wr_en = 1'b0;
            rd_en = 1'b0;
            #1;
            if (dout !== {width}'d21 || empty !== 1'b0 || full !== 1'b0) begin
              $display("TEST_FAIL simultaneous push-pop changed occupancy");
              $finish;
            end
            read_expect({width}'d22);
            if (empty !== 1'b1) begin
              $display("TEST_FAIL simultaneous push-pop left wrong count");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def uart_tx_testbench() -> str:
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
            expected_bits = 8'h96;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            data = 8'h96;
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


def uart_tx_rtl_files(width: int) -> dict[str, str]:
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


def uart_rx_testbench() -> str:
    return dedent(
        """\
        `timescale 1ns/1ps

        module tb_top;
          localparam integer CLKS_PER_BIT = 4;
          reg clk;
          reg rst_n;
          reg rx;
          wire [7:0] data;
          wire data_valid;
          wire framing_error;
          reg [7:0] received [0:2];
          integer received_count;
          integer framing_error_count;
          integer i;

          top #(.CLKS_PER_BIT(CLKS_PER_BIT)) uut (
            .clk(clk),
            .rst_n(rst_n),
            .rx(rx),
            .data(data),
            .data_valid(data_valid),
            .framing_error(framing_error)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          always @(posedge clk) begin
            if (data_valid) begin
              received[received_count] = data;
              received_count = received_count + 1;
            end
            if (framing_error)
              framing_error_count = framing_error_count + 1;
          end

            task send_frame;
            input [7:0] value;
            input bad_stop;
            input phase_offset;
            begin
              if (phase_offset) begin
                @(negedge clk);
                repeat (1) @(negedge clk);
              end else begin
                @(negedge clk);
              end
              rx = 1'b0;
              repeat (CLKS_PER_BIT) @(posedge clk);
              for (i = 0; i < 8; i = i + 1) begin
                rx = value[i];
                repeat (CLKS_PER_BIT) @(posedge clk);
              end
              rx = bad_stop ? 1'b0 : 1'b1;
              repeat (CLKS_PER_BIT) @(posedge clk);
              rx = 1'b1;
            end
          endtask

          task send_false_start;
            begin
              repeat (2) @(posedge clk);
              @(negedge clk);
              rx = 1'b0;
              repeat (2) @(negedge clk);
              rx = 1'b1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            rx = 1'b1;
            received_count = 0;
            framing_error_count = 0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_false_start();
            repeat (40) @(posedge clk);
            if (received_count !== 0 || framing_error_count !== 0) begin
              $display("TEST_FAIL false start was accepted");
              $finish;
            end

            send_frame(8'h00, 1'b0, 1'b0);
            send_frame(8'hff, 1'b0, 1'b0);
            send_frame(8'h96, 1'b0, 1'b1);
            repeat (2) @(posedge clk);
            if (received_count !== 3 || received[0] !== 8'h00 || received[1] !== 8'hff || received[2] !== 8'h96) begin
              $display("TEST_FAIL RX bytes, back-to-back frames, or phase offset were decoded incorrectly");
              $finish;
            end

            send_frame(8'h3c, 1'b1, 1'b0);
            repeat (2) @(posedge clk);
            if (framing_error_count !== 1 || received_count !== 3) begin
              $display("TEST_FAIL malformed stop bit was not rejected");
              $finish;
            end

            fork
              send_frame(8'h69, 1'b0, 1'b0);
              begin
                repeat (5) @(posedge clk);
                rst_n = 1'b0;
                repeat (2) @(posedge clk);
                rst_n = 1'b1;
              end
            join
            repeat (2) @(posedge clk);
            if (received_count !== 3) begin
              $display("TEST_FAIL reset during frame emitted stale data");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def uart_rx_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        """\
        module top #(
            parameter CLKS_PER_BIT = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire rx,
            output wire [7:0] data,
            output wire data_valid,
            output wire framing_error
        );

          uart_rx_core #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx_core (
            .clk(clk),
            .rst_n(rst_n),
            .rx(rx),
            .data(data),
            .data_valid(data_valid),
            .framing_error(framing_error)
          );

        endmodule
        """
    )
    uart_rx_core = dedent(
        """\
        module uart_rx_core #(
            parameter CLKS_PER_BIT = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire rx,
            output reg [7:0] data,
            output reg data_valid,
            output reg framing_error
        );

          localparam [15:0] CLKS_PER_BIT_16 = CLKS_PER_BIT;
          localparam [15:0] HALF_CLKS_PER_BIT = CLKS_PER_BIT_16 / 2;
          localparam [1:0] IDLE = 2'd0;
          localparam [1:0] START = 2'd1;
          localparam [1:0] DATA = 2'd2;
          localparam [1:0] STOP = 2'd3;

          reg [1:0] state;
          reg [15:0] sample_count;
          reg [2:0] bit_index;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              state <= IDLE;
              sample_count <= 16'd0;
              bit_index <= 3'd0;
              data <= 8'd0;
              data_valid <= 1'b0;
              framing_error <= 1'b0;
            end else begin
              data_valid <= 1'b0;
              framing_error <= 1'b0;
              case (state)
                IDLE: begin
                  sample_count <= 16'd0;
                  bit_index <= 3'd0;
                  if (!rx)
                    state <= START;
                end
                START: begin
                  if (sample_count == HALF_CLKS_PER_BIT - 16'd1) begin
                    sample_count <= 16'd0;
                    if (!rx) begin
                      bit_index <= 3'd0;
                      state <= DATA;
                    end else begin
                      state <= IDLE;
                    end
                  end else begin
                    sample_count <= sample_count + 16'd1;
                  end
                end
                DATA: begin
                  if (sample_count == CLKS_PER_BIT_16 - 16'd1) begin
                    sample_count <= 16'd0;
                    data[bit_index] <= rx;
                    if (bit_index == 3'd7)
                      state <= STOP;
                    else
                      bit_index <= bit_index + 3'd1;
                  end else begin
                    sample_count <= sample_count + 16'd1;
                  end
                end
                STOP: begin
                  if (sample_count == CLKS_PER_BIT_16 - 16'd1) begin
                    sample_count <= 16'd0;
                    state <= IDLE;
                    if (rx)
                      data_valid <= 1'b1;
                    else
                      framing_error <= 1'b1;
                  end else begin
                    sample_count <= sample_count + 16'd1;
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
    return {
        "rtl/top.v": top,
        "rtl/uart_rx_core.v": uart_rx_core,
    }


def uart_fifo_loopback_testbench() -> str:
    return dedent(
        """\
        `timescale 1ns/1ps

        module tb_top;
          localparam integer CLKS_PER_BIT = 4;
          reg clk;
          reg rst_n;
          reg rx;
          reg tx_enable;
          wire tx;

          top #(.CLKS_PER_BIT(CLKS_PER_BIT)) uut (
            .clk(clk),
            .rst_n(rst_n),
            .rx(rx),
            .tx(tx),
            .tx_enable(tx_enable)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_uart_byte;
            input [7:0] value;
            integer bit_index;
            begin
              @(negedge clk);
              rx = 1'b0;
              repeat (CLKS_PER_BIT) @(posedge clk);
              for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                rx = value[bit_index];
                repeat (CLKS_PER_BIT) @(posedge clk);
              end
              rx = 1'b1;
              repeat (CLKS_PER_BIT) @(posedge clk);
            end
          endtask

          task expect_tx_byte;
            input [7:0] expected;
            reg [7:0] observed;
            integer bit_index;
            begin
              @(negedge tx);
              repeat (CLKS_PER_BIT + (CLKS_PER_BIT / 2)) @(posedge clk);
              for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                observed[bit_index] = tx;
                repeat (CLKS_PER_BIT) @(posedge clk);
              end
              if (tx !== 1'b1 || observed !== expected) begin
                $display("TEST_FAIL expected TX byte=%h got=%h", expected, observed);
                $finish;
              end
            end
          endtask

          initial begin
            rst_n = 1'b0;
            rx = 1'b1;
            tx_enable = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_uart_byte(8'h12);
            send_uart_byte(8'h34);
            send_uart_byte(8'h56);
            send_uart_byte(8'h78);

            fork
              begin
                tx_enable = 1'b1;
                send_uart_byte(8'h9a);
                send_uart_byte(8'hbc);
              end
              begin
                expect_tx_byte(8'h12);
                expect_tx_byte(8'h34);
                expect_tx_byte(8'h56);
                expect_tx_byte(8'h78);
                expect_tx_byte(8'h9a);
                expect_tx_byte(8'hbc);
              end
            join

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def uart_fifo_loopback_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        """\
        module top #(
            parameter CLKS_PER_BIT = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire rx,
            output wire tx,
            input wire tx_enable
        );

          wire [7:0] rx_data;
          wire rx_data_valid;
          wire rx_framing_error;
          wire [7:0] fifo_dout;
          wire fifo_full;
          wire fifo_empty;
          wire tx_busy;
          reg fifo_rd_en;
          reg tx_start;
          reg [7:0] tx_data;

          uart_rx_core #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx_core (
            .clk(clk),
            .rst_n(rst_n),
            .rx(rx),
            .data(rx_data),
            .data_valid(rx_data_valid),
            .framing_error(rx_framing_error)
          );

          sync_fifo_core u_sync_fifo_core (
            .clk(clk),
            .rst_n(rst_n),
            .wr_en(rx_data_valid && !fifo_full && !rx_framing_error),
            .din(rx_data),
            .rd_en(fifo_rd_en),
            .dout(fifo_dout),
            .full(fifo_full),
            .empty(fifo_empty)
          );

          uart_tx_core #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_tx_core (
            .clk(clk),
            .rst_n(rst_n),
            .start(tx_start),
            .data(tx_data),
            .tx(tx),
            .busy(tx_busy)
          );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              fifo_rd_en <= 1'b0;
              tx_start <= 1'b0;
              tx_data <= 8'd0;
            end else begin
              fifo_rd_en <= 1'b0;
              tx_start <= 1'b0;
              if (tx_enable && !fifo_empty && !tx_busy && !tx_start) begin
                fifo_rd_en <= 1'b1;
                tx_start <= 1'b1;
                tx_data <= fifo_dout;
              end
            end
          end

        endmodule
        """
    )
    fifo = dedent(
        """\
        module sync_fifo_core (
            input wire clk,
            input wire rst_n,
            input wire wr_en,
            input wire [7:0] din,
            input wire rd_en,
            output wire [7:0] dout,
            output wire full,
            output wire empty
        );

          reg [7:0] mem [0:3];
          reg [1:0] wr_ptr;
          reg [1:0] rd_ptr;
          reg [2:0] count;

          assign dout = mem[rd_ptr];
          assign full = (count == 3'd4);
          assign empty = (count == 3'd0);

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              wr_ptr <= 2'd0;
              rd_ptr <= 2'd0;
              count <= 3'd0;
            end else begin
              if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 2'd1;
              end
              if (rd_en && !empty)
                rd_ptr <= rd_ptr + 2'd1;
              case ({wr_en && !full, rd_en && !empty})
                2'b10: count <= count + 3'd1;
                2'b01: count <= count - 3'd1;
                default: count <= count;
              endcase
            end
          end

        endmodule
        """
    )
    tx_core = dedent(
        """\
        module uart_tx_core #(
            parameter CLKS_PER_BIT = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [7:0] data,
            output reg tx,
            output reg busy
        );

          localparam [15:0] CLKS_PER_BIT_16 = CLKS_PER_BIT;
          localparam [1:0] IDLE = 2'd0;
          localparam [1:0] START = 2'd1;
          localparam [1:0] DATA = 2'd2;
          localparam [1:0] STOP = 2'd3;

          reg [1:0] state;
          reg [15:0] bit_count;
          reg [2:0] bit_index;
          reg [7:0] shifter;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              state <= IDLE;
              bit_count <= 16'd0;
              bit_index <= 3'd0;
              shifter <= 8'd0;
              tx <= 1'b1;
              busy <= 1'b0;
            end else begin
              case (state)
                IDLE: begin
                  tx <= 1'b1;
                  busy <= 1'b0;
                  bit_count <= 16'd0;
                  if (start) begin
                    shifter <= data;
                    tx <= 1'b0;
                    busy <= 1'b1;
                    state <= START;
                  end
                end
                START: begin
                  if (bit_count == CLKS_PER_BIT_16 - 16'd1) begin
                    bit_count <= 16'd0;
                    bit_index <= 3'd0;
                    tx <= shifter[0];
                    state <= DATA;
                  end else begin
                    bit_count <= bit_count + 16'd1;
                  end
                end
                DATA: begin
                  if (bit_count == CLKS_PER_BIT_16 - 16'd1) begin
                    bit_count <= 16'd0;
                    if (bit_index == 3'd7) begin
                      tx <= 1'b1;
                      state <= STOP;
                    end else begin
                      bit_index <= bit_index + 3'd1;
                      tx <= shifter[bit_index + 3'd1];
                    end
                  end else begin
                    bit_count <= bit_count + 16'd1;
                  end
                end
                STOP: begin
                  if (bit_count == CLKS_PER_BIT_16 - 16'd1) begin
                    bit_count <= 16'd0;
                    busy <= 1'b0;
                    tx <= 1'b1;
                    state <= IDLE;
                  end else begin
                    bit_count <= bit_count + 16'd1;
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
    return {
        "rtl/top.v": top,
        "rtl/uart_rx_core.v": uart_rx_rtl_files(width)["rtl/uart_rx_core.v"],
        "rtl/sync_fifo_core.v": fifo,
        "rtl/uart_tx_core.v": tx_core,
    }


def spi_master_testbench() -> str:
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
          integer sclk_edge_count;

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

          always @(posedge sclk) begin
            if (!cs_n) begin
              sclk_edge_count = sclk_edge_count + 1;
            end
          end

          initial begin
            rst_n = 1'b0;
            start = 1'b0;
            tx_data = 8'd0;
            miso_pattern = 8'h3C;
            miso_bit = 7;
            sclk_edge_count = 0;
            miso = miso_pattern[7];
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            @(negedge clk);
            tx_data = 8'h96;
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
            if (sclk_edge_count != 8) begin
              $display("TEST_FAIL expected 8 SCLK rising edges got %0d", sclk_edge_count);
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


def spi_master_rtl_files(width: int) -> dict[str, str]:
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
                  end
                end else begin
                  sclk <= 1'b0;
                  if (bit_index == 3'd7) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                    cs_n <= 1'b1;
                  end else begin
                    bit_index <= bit_index + 3'd1;
                    mosi <= tx_shift[7];
                    tx_shift <= {tx_shift[6:0], 1'b0};
                  end
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
