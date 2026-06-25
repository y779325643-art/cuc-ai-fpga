// stream_join.v - Joins two input streams into one output stream
// Output is the sum of both inputs.
`timescale 1ns/1ps

module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    reset_n,
    input  wire [DATA_WIDTH-1:0]   in0_data,
    input  wire                    in0_valid,
    output wire                    in0_ready,
    input  wire [DATA_WIDTH-1:0]   in1_data,
    input  wire                    in1_valid,
    output wire                    in1_ready,
    output wire [DATA_WIDTH-1:0]   out_data,
    output reg                     out_valid,
    input  wire                    out_ready
);

    // FSM state
    reg join_state;
    localparam IDLE = 0;
    localparam JOIN = 1;

    // Registers for output
    reg [DATA_WIDTH-1:0] out_data_reg;

    // Combinational outputs
    assign in0_ready = (join_state == IDLE) & ~out_valid;
    assign in1_ready = (join_state == IDLE) & ~out_valid;
    assign out_data = out_data_reg;

    // FSM and output logic
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            join_state <= IDLE;
            out_valid <= 1'b0;
            out_data_reg <= 0;
        end else begin
            case (join_state)
                IDLE: begin
                    if (in0_valid && in1_valid && !out_valid) begin
                        out_data_reg <= in0_data + in1_data;
                        out_valid <= 1'b1;
                        join_state <= JOIN;
                    end
                end
                JOIN: begin
                    if (out_ready) begin
                        out_valid <= 1'b0;
                        join_state <= IDLE;
                    end
                end
            endcase
        end
    end

endmodule
