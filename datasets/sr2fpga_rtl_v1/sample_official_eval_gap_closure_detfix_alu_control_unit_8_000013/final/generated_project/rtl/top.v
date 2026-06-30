module top (
    input wire clk,
    input wire rst_n,
    input wire valid,
    output wire ready,
    input wire [2:0] op,
    input wire [7:0] lhs,
    input wire [7:0] rhs,
    output wire result_valid,
    output wire [7:0] result,
    output wire zero,
    output wire carry,
    output wire negative
);

  wire [2:0] decoded_op;
  wire [7:0] alu_result;
  wire alu_carry;

  assign ready = 1'b1;

  control_decode u_control_decode (
    .op(op),
    .decoded_op(decoded_op)
  );

  alu_core #(
    .WIDTH(8)
  ) u_alu_core (
    .op(decoded_op),
    .lhs(lhs),
    .rhs(rhs),
    .result(alu_result),
    .carry(alu_carry)
  );

  status_flags #(
    .WIDTH(8)
  ) u_status_flags (
    .clk(clk),
    .rst_n(rst_n),
    .valid(valid),
    .alu_result(alu_result),
    .alu_carry(alu_carry),
    .result_valid(result_valid),
    .result(result),
    .zero(zero),
    .carry(carry),
    .negative(negative)
  );

endmodule
