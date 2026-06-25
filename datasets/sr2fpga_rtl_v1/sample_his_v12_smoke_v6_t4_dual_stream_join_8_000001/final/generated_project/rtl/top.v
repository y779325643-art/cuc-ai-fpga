`timescale 1ns / 1ps

module top #(parameter WIDTH = 8) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in0_data,
    input  wire in0_valid,
    output wire in0_ready,
    input  wire [WIDTH-1:0] in1_data,
    input  wire in1_valid,
    output wire in1_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    // Internal wires
    wire [WIDTH-1:0] buf0_data;
    wire buf0_valid;
    wire buf0_ready;
    wire [WIDTH-1:0] buf1_data;
    wire buf1_valid;
    wire buf1_ready;
    wire [WIDTH*2-1:0] join_data;
    wire join_valid;
    wire join_ready;
    wire [WIDTH-1:0] acc_data;
    wire acc_valid;
    wire acc_ready;
    wire [WIDTH-1:0] staged_data;
    wire staged_valid;
    wire staged_ready;

    // Control signals for join_count
    reg [7:0] join_count;
    wire inc_count;

    // Instantiations
    skid_buffer #(.WIDTH(WIDTH)) in0_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(in0_data),
        .valid_in(in0_valid),
        .ready_out(in0_ready),
        .data_out(buf0_data),
        .valid_out(buf0_valid),
        .ready_in(buf0_ready)
    );

    skid_buffer #(.WIDTH(WIDTH)) in1_buffer (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(in1_data),
        .valid_in(in1_valid),
        .ready_out(in1_ready),
        .data_out(buf1_data),
        .valid_out(buf1_valid),
        .ready_in(buf1_ready)
    );

    stream_join #(.WIDTH(WIDTH)) join_core (
        .clk(clk),
        .rst_n(rst_n),
        .in0_data(buf0_data),
        .in0_valid(buf0_valid),
        .in0_ready(buf0_ready),
        .in1_data(buf1_data),
        .in1_valid(buf1_valid),
        .in1_ready(buf1_ready),
        .out_data(join_data),
        .out_valid(join_valid),
        .out_ready(join_ready)
    );

    accumulator_core #(.WIDTH(WIDTH)) accumulator (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(join_data),
        .valid_in(join_valid),
        .ready_out(join_ready),
        .data_out(acc_data),
        .valid_out(acc_valid),
        .ready_in(acc_ready)
    );

    stream_stage #(.WIDTH(WIDTH)) out_stage (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(acc_data),
        .valid_in(acc_valid),
        .ready_out(acc_ready),
        .data_out(staged_data),
        .valid_out(staged_valid),
        .ready_in(out_ready)
    );

    // Outputs
    assign out_data = staged_data;
    assign out_valid = staged_valid;

    // join_count increment condition (from accumulator update)
    assign inc_count = acc_valid & acc_ready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            join_count <= 8'd0;
        end else if (inc_count) begin
            join_count <= join_count + 1;
        end
    end

endmodule
