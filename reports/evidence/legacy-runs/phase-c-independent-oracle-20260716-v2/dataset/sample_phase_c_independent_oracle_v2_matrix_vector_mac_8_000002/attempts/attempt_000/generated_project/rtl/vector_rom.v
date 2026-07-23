module vector_rom (
    input wire [1:0] addr,
    output reg signed [2:0] coefficient
);

  always @* begin
    case (addr)
      2'd0: coefficient = 3'sd2;
      2'd1: coefficient = -3'sd1;
      2'd2: coefficient = 3'sd3;
      default: coefficient = 3'sd1;
    endcase
  end

endmodule
