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
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
