`timescale 1ns / 1ps

module accumulator_core #(
    parameter DATA_WIDTH = 8
)(
    input  wire                clk,
    input  wire                reset_n,
    input  wire [DATA_WIDTH-1:0] in_data,
    input  wire                in_valid,
    input  wire                out_ready,
    output reg  [DATA_WIDTH-1:0] out_data,
    output reg                 out_valid,
    output wire                in_ready
);

    reg [DATA_WIDTH-1:0] acc_reg;
    reg [DATA_WIDTH-1:0] next_acc;
    reg next_valid;

    always @(posedge clk) begin
        if (!reset_n) begin
            acc_reg   <= {DATA_WIDTH{1'b0}};
            out_data  <= {DATA_WIDTH{1'b0}};
            out_valid <= 1'b0;
        end else begin
            // Update accumulator when input is accepted
            if (in_valid && in_ready) begin
                acc_reg <= acc_reg + in_data;
            end
            // Output register
            if (out_valid && out_ready) begin
                out_valid <= 1'b0;
            end
            if (next_valid) begin
                out_data  <= next_acc;
                out_valid <= 1'b1;
            end
        end
    end

    assign in_ready = !out_valid || out_ready;  // Can accept if output not valid or downstream ready

    // Next state combinational
    always @(*) begin
        if (in_valid && in_ready) begin
            next_acc   = acc_reg + in_data;
            next_valid = 1'b1;
        end else begin
            next_acc   = acc_reg;
            next_valid = 1'b0;
        end
    end

endmodule
