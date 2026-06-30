module top (
    input clk,
    input reset_n,
    input event_valid,
    output [7:0] count
);
wire count_en;

event_gate u_gate (
    .clk(clk),
    .reset_n(reset_n),
    .event_valid(event_valid),
    .count_en(count_en)
);

counter_core u_counter (
    .clk(clk),
    .reset_n(reset_n),
    .en(count_en),
    .count(count)
);
endmodule
