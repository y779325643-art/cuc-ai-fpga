`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [7:0] in_data;
  reg frame_start;
  reg frame_end;
  reg [7:0] expected_crc;
  wire out_valid;
  reg out_ready;
  wire [7:0] crc_value;
  wire crc_match;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .frame_start(frame_start),
    .frame_end(frame_end),
    .expected_crc(expected_crc),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .crc_value(crc_value),
    .crc_match(crc_match)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task send_byte;
    input [7:0] value;
    input start_i;
    input end_i;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      in_data = value;
      frame_start = start_i;
      frame_end = end_i;
      @(negedge clk);
      if (in_ready !== 1'b1) begin
        $display("TEST_FAIL input was not ready");
        $finish;
      end
      in_valid = 1'b0;
      in_data = 8'd0;
      frame_start = 1'b0;
      frame_end = 1'b0;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = 8'd0;
    frame_start = 1'b0;
    frame_end = 1'b0;
    expected_crc = 8'h7c;
    out_ready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    send_byte(8'h12, 1'b1, 1'b0);
    send_byte(8'h34, 1'b0, 1'b0);
    send_byte(8'h56, 1'b0, 1'b1);

    @(posedge clk);
    #1;
    if (out_valid !== 1'b1) begin
      $display("TEST_FAIL out_valid was not asserted");
      $finish;
    end
    if (crc_value !== 8'h7c) begin
      $display("TEST_FAIL expected crc=7c got %0h", crc_value);
      $finish;
    end
    if (crc_match !== 1'b1) begin
      $display("TEST_FAIL crc_match was not asserted");
      $finish;
    end
    @(posedge clk);
    #1;
    if (out_valid !== 1'b0) begin
      $display("TEST_FAIL out_valid did not clear after ready");
      $finish;
    end
    $display("TEST_PASS");
    $finish;
  end
endmodule
