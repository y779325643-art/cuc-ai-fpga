module pwm_channel #(
    parameter WIDTH = 8
) (
    input wire [WIDTH-1:0] counter,
    input wire [WIDTH-1:0] duty,
    output wire pwm_out
);

  assign pwm_out = (counter < duty);

endmodule
