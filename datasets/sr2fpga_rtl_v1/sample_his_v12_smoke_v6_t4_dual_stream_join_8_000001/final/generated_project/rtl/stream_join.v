`timescale 1ns / 1ps

module stream_join #(parameter WIDTH = 8) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in0_data,
    input  wire in0_valid,
    output wire in0_ready,
    input  wire [WIDTH-1:0] in1_data,
    input  wire in1_valid,
    output wire in1_ready,
    output wire [WIDTH*2-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    // State machine for joining
    localparam [1:0] IDLE = 2'd0,
                     OUTPUT = 2'd1;
    // Note: WAIT_IN0 and WAIT_IN1 not used; we wait for both simultaneously

    reg [1:0] state;
    reg [WIDTH-1:0] reg0, reg1;
    reg join_valid_internal;

    assign in0_ready = (state == IDLE) ? ~join_valid_internal : 1'b0;
    assign in1_ready = (state == IDLE) ? ~join_valid_internal : 1'b0;
    assign out_data = {reg1, reg0}; // concatenation: in1 is high byte, in0 low byte
    assign out_valid = join_valid_internal;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            reg0 <= {WIDTH{1'b0}};
            reg1 <= {WIDTH{1'b0}};
            join_valid_internal <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    if (in0_valid && in1_valid) begin
                        reg0 <= in0_data;
                        reg1 <= in1_data;
                        join_valid_internal <= 1'b1;
                        state <= OUTPUT;
                    end
                end
                OUTPUT: begin
                    if (out_ready) begin
                        join_valid_internal <= 1'b0;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end

endmodule
