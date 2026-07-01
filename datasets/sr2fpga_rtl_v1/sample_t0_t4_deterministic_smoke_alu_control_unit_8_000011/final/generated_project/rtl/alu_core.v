module alu_core #(
    parameter WIDTH = 8
) (
    input wire [2:0] op,
    input wire [WIDTH-1:0] lhs,
    input wire [WIDTH-1:0] rhs,
    output reg [WIDTH-1:0] result,
    output reg carry
);

  wire [WIDTH:0] add_ext;
  wire [WIDTH:0] sub_ext;

  assign add_ext = {1'b0, lhs} + {1'b0, rhs};
  assign sub_ext = {1'b0, lhs} - {1'b0, rhs};

  always @* begin
    result = {WIDTH{1'b0}};
    carry = 1'b0;
    case (op)
      3'b000: begin
        result = add_ext[WIDTH-1:0];
        carry = add_ext[WIDTH];
      end
      3'b001: begin
        result = sub_ext[WIDTH-1:0];
        carry = sub_ext[WIDTH];
      end
      3'b010: result = lhs & rhs;
      3'b011: result = lhs | rhs;
      3'b100: result = lhs ^ rhs;
      3'b101: result = lhs << rhs[2:0];
      3'b110: result = lhs >> rhs[2:0];
      default: result = lhs;
    endcase
  end

endmodule
