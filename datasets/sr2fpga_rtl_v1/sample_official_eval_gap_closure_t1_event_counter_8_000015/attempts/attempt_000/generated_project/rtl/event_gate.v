module event_gate (
    input wire clk,
    input wire rst_n,
    input wire event_valid,
    output wire count_en
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    assign count_en = event_valid;
endmodule
