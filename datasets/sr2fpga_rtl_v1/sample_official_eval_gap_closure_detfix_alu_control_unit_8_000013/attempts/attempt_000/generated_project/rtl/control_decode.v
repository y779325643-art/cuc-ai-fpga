module control_decode (
    input wire [2:0] op,
    output wire [2:0] decoded_op
);

  assign decoded_op = op;

endmodule
