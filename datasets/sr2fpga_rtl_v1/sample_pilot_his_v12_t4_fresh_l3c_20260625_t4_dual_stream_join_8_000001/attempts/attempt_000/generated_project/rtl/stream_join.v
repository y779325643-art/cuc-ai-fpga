// stream_join.v - Joins two input streams into one output stream
// Output is the sum? Actually just passes through when both valid? 
// According to System-HIS, join_fsm controls: when both buffers have valid, join and output the sum? 
// But data flow says join_core.out_data drives accumulator.in_data. Join core simply forwards data?
// Possibly join core outputs in0_data? Assuming it forwards in0_data as joined data.
// We'll implement: When both inputs are valid and ready is high, output in0_data (or sum? But accumulator adds).
// Simpler: join core just outputs in0_data when both valid. Let's make it output the sum of in0 and in1? No, accumulator adds later.
// The join action: join_fsm transitions when both buffers valid. The join effect passes data. So out_data = in0_data? Or maybe out_data = in0_data + in1_data? But accumulator then adds again? That would double count.
// Check: data flow join_core.out_data -> accumulator.in_data. Accumulator accumulates (adds to reg). So join core should output the sum of in0 and in1? Then accumulator adds that sum to accumulator_reg, accumulating sums. That makes sense: each joined pair is summed, then that sum is accumulated. So join core outputs in0+in1.
// So stream_join outputs sum of two inputs.
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
