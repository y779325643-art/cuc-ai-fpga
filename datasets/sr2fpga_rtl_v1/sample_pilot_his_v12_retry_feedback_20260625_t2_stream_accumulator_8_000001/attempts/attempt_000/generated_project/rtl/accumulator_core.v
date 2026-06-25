`timescale 1ns / 1ps
module accumulator_core (
    clk,
    rst_n,
    in_valid,
    in_ready,
    in_data,
    out_valid,
    out_ready,
    out_data
);
    parameter DATA_WIDTH = 8;

    input  wire                clk;
    input  wire                rst_n;
    input  wire                in_valid;
    output reg                 in_ready;
    input  wire [DATA_WIDTH-1:0] in_data;
    output reg                 out_valid;
    input  wire                out_ready;
    output reg  [DATA_WIDTH-1:0] out_data;

    reg [DATA_WIDTH-1:0] accum_reg;
    reg                  have_output;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            accum_reg  <= {DATA_WIDTH{1'b0}};
            have_output <= 1'b0;
            out_valid   <= 1'b0;
            out_data    <= {DATA_WIDTH{1'b0}};
            in_ready    <= 1'b1;
        end else begin
            // Default: in_ready ready if we can accept (either not having output or output will be taken)
            in_ready <= ~have_output | out_ready;

            // Input handshake
            if (in_valid && in_ready) begin
                accum_reg  <= accum_reg + in_data;
                have_output <= 1'b1;
            end

            // Output handshake: out_data is always accum_reg when have_output
            out_valid <= have_output;
            out_data  <= accum_reg;

            // If output transferred and no new input, have_output clears?
            // But if we didn't accept new input, have_output should remain because accum_reg still holds data.
            // So we need to keep have_output unless we accept a new input? Actually we want out_valid to be high as long as we have accumulated something.
            // The output data is always the current sum. So it's always valid after first accumulation.
            // But if out_ready is low, we cannot accept new input. So have_output stays high.
            // If out_ready is high and we transfer, the output data remains valid (unchanged). So have_output stays high.
            // However, to allow backpressure, we need to clear have_output only if we want to indicate we have nothing for output? But that would mean we lose the accumulated value.
            // The correct behavior: out_valid is always high after first accumulation until reset.
            // So we set have_output once and never clear.
            // But then in_ready would be out_ready after first input? That's correct.
            // So we simplify: have_output set on first valid input, and never cleared.
            // But what if we want to reset? Only on reset.
        end
    end

    // Additionally, we need to handle the case where out_ready is low and we have output: we cannot accept new input.
    // So in_ready = ~have_output | out_ready works.

    // However, we also need to update accum_reg only when input handshake occurs.

    // Also, we need to update out_data (comb) but we already assign in clocked block. For comb, we can assign directly.
    // But out_data should reflect accum_reg continuously.

    // Let's adjust: use always @* for out_data and out_valid.
    // But we used regs, so we can assign in always @* for out_data and out_valid.
    // Better: use comb for output.

    // Redesign: Use always @* for output.
    // But we already have clocked block. Let's split.

    // I'll rewrite cleaner.

endmodule

// Let's rewrite accumulator_core properly.

module accumulator_core (
    clk,
    rst_n,
    in_valid,
    in_ready,
    in_data,
    out_valid,
    out_ready,
    out_data
);
    parameter DATA_WIDTH = 8;

    input  wire                clk;
    input  wire                rst_n;
    input  wire                in_valid;
    output wire                in_ready;
    input  wire [DATA_WIDTH-1:0] in_data;
    output wire                out_valid;
    input  wire                out_ready;
    output wire [DATA_WIDTH-1:0] out_data;

    reg [DATA_WIDTH-1:0] accum_reg;
    reg                  started;

    wire accept_input = in_valid & in_ready;
    wire transfer_out = out_valid & out_ready;

    assign in_ready = ~started | out_ready;
    assign out_valid = started;
    assign out_data = accum_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            accum_reg <= {DATA_WIDTH{1'b0}};
            started <= 1'b0;
        end else begin
            if (accept_input) begin
                accum_reg <= accum_reg + in_data;
                started <= 1'b1;
            end
        end
    end

endmodule
