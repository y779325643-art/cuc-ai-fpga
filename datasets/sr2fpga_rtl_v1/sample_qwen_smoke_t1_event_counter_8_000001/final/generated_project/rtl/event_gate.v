// event_gate.v - Combinational event gate
// System-HIS v1.2 compliant

module event_gate (
    input  wire clk,
    input  wire rst_n,
    input  wire event_in,
    output wire gated_event
);

    // Combinational pass-through gate
    // Latency: 0 cycles, throughput: combinational
    assign gated_event = event_in;

endmodule
