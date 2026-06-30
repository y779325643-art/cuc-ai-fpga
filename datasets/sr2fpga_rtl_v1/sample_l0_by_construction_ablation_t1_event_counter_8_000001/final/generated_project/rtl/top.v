module top (
    input wire clk,
    input wire rst_n,
    input wire event_valid,
    output wire [7:0] count
);
    wire count_en;
    event_gate u_gate (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .count_en(count_en)
    );
    counter_core u_counter (
        .clk(clk),
        .rst_n(rst_n),
        .en(count_en),
        .count(count)
    );
endmodule
