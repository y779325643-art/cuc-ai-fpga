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
