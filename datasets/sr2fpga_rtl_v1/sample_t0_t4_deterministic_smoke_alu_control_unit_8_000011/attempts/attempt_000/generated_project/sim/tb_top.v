`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg valid;
  wire ready;
  reg [2:0] op;
  reg [7:0] lhs;
  reg [7:0] rhs;
  wire result_valid;
  wire [7:0] result;
  wire zero;
  wire carry;
  wire negative;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .valid(valid),
    .ready(ready),
    .op(op),
    .lhs(lhs),
    .rhs(rhs),
    .result_valid(result_valid),
    .result(result),
    .zero(zero),
    .carry(carry),
    .negative(negative)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task expect_result;
    input [2:0] op_i;
    input [7:0] lhs_i;
    input [7:0] rhs_i;
    input [7:0] expected_result;
    input expected_zero;
    input expected_carry;
    input expected_negative;
    begin
      @(negedge clk);
      valid = 1'b1;
      op = op_i;
      lhs = lhs_i;
      rhs = rhs_i;
      @(negedge clk);
      valid = 1'b0;
      if (ready !== 1'b1) begin
        $display("TEST_FAIL ready was not asserted");
        $finish;
      end
      if (result_valid !== 1'b1) begin
        $display("TEST_FAIL result_valid was not asserted for op=%0d", op_i);
        $finish;
      end
      if (result !== expected_result) begin
        $display(
          "TEST_FAIL op=%0d expected result=%0h got %0h",
          op_i,
          expected_result,
          result
        );
        $finish;
      end
      if (zero !== expected_zero || carry !== expected_carry || negative !== expected_negative) begin
        $display("TEST_FAIL flags op=%0d zero=%0b carry=%0b negative=%0b", op_i, zero, carry, negative);
        $finish;
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    valid = 1'b0;
    op = 3'd0;
    lhs = 8'd0;
    rhs = 8'd0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    expect_result(3'b000, 8'hff, 8'h01, 8'h00, 1'b1, 1'b1, 1'b0);
    expect_result(3'b001, 8'h03, 8'h01, 8'h02, 1'b0, 1'b0, 1'b0);
    expect_result(3'b010, 8'haa, 8'h0f, 8'h0a, 1'b0, 1'b0, 1'b0);
    expect_result(3'b011, 8'ha0, 8'h0f, 8'haf, 1'b0, 1'b0, 1'b1);
    expect_result(3'b100, 8'hff, 8'h0f, 8'hf0, 1'b0, 1'b0, 1'b1);
    expect_result(3'b101, 8'h11, 8'h01, 8'h22, 1'b0, 1'b0, 1'b0);
    expect_result(3'b110, 8'h80, 8'h02, 8'h20, 1'b0, 1'b0, 1'b0);
    expect_result(3'b111, 8'h5a, 8'h00, 8'h5a, 1'b0, 1'b0, 1'b0);

    @(posedge clk);
    #1;
    if (result_valid !== 1'b0) begin
      $display("TEST_FAIL result_valid did not clear");
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
