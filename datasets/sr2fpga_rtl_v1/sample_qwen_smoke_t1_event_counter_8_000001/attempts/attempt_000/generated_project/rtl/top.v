// top.v - Integration wrapper for 8-bit event counter
// System-HIS v1.2 compliant

module top #(
    parameter DATA_WIDTH = 8
)(
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  event_in,
    output wire [DATA_WIDTH-1:0] count_out
);

    wire gated_event_wire;

    event_gate u_event_gate (
        .clk         (clk),
        .rst_n       (rst_n),
        .event_in    (event_in),
        .gated_event (gated_event_wire)
    );

    counter_core #(
        .DATA_WIDTH (DATA_WIDTH)
    ) u_counter (
        .clk   (clk),
        .rst_n (rst_n),
        .inc   (gated_event_wire),
        .count (count_out)
    );

endmodule
