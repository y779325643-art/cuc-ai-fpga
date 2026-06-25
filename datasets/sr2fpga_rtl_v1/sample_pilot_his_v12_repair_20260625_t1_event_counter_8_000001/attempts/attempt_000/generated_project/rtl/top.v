////////////////////////////////////////////////////////////////////////////////
// top.v
// Integration wrapper for event counter project
////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps

module top (
    input  wire clk,
    input  wire rst_n,
    input  wire event_in,
    output wire [7:0] count,
    output wire count_valid
);

    // Internal wire from event_gate to counter_core
    wire event_pulse;

    // Instantiate event_gate
    event_gate u_event_gate (
        .clk             (clk),
        .rst_n           (rst_n),
        .event_in        (event_in),
        .event_pulse_out (event_pulse)
    );

    // Instantiate counter_core
    counter_core u_counter (
        .clk             (clk),
        .rst_n           (rst_n),
        .event_pulse_in  (event_pulse),
        .count           (count),
        .count_valid     (count_valid)
    );

endmodule
