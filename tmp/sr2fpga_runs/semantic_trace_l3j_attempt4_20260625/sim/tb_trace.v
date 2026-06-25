`timescale 1ns/1ps

module tb_trace;
    parameter DATA_WIDTH = 8;

    reg clk;
    reg rst_n;
    reg in0_valid;
    wire in0_ready;
    reg [DATA_WIDTH-1:0] in0_data;
    reg in1_valid;
    wire in1_ready;
    reg [DATA_WIDTH-1:0] in1_data;
    wire out_valid;
    reg out_ready;
    wire [DATA_WIDTH-1:0] out_data;

    integer cycle;
    integer i;
    integer input0_count;
    integer input1_count;
    integer join_count;
    integer acc_count;
    integer output_count;
    integer num_packets;
    reg [DATA_WIDTH-1:0] seq0 [0:2];
    reg [DATA_WIDTH-1:0] seq1 [0:2];
    reg [DATA_WIDTH-1:0] expected_stream [0:5];

    top #(.DATA_WIDTH(DATA_WIDTH)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .in0_valid(in0_valid),
        .in0_ready(in0_ready),
        .in0_data(in0_data),
        .in1_valid(in1_valid),
        .in1_ready(in1_ready),
        .in1_data(in1_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_data(out_data)
    );

    always #5 clk = ~clk;

    always @(posedge clk) begin
        cycle = cycle + 1;
        if (rst_n) begin
            if (in0_valid && in0_ready) begin
                $display("TRACE input_accept cycle=%0d lane=0 idx=%0d data=%0d", cycle, input0_count, in0_data);
                input0_count = input0_count + 1;
            end
            if (in1_valid && in1_ready) begin
                $display("TRACE input_accept cycle=%0d lane=1 idx=%0d data=%0d", cycle, input1_count, in1_data);
                input1_count = input1_count + 1;
            end
            if (dut.join_valid && dut.join_ready) begin
                $display("TRACE join_output cycle=%0d idx=%0d data=%0d", cycle, join_count, dut.join_data);
                join_count = join_count + 1;
            end
            if (dut.acc_valid && dut.acc_ready) begin
                $display("TRACE acc_output cycle=%0d idx=%0d data=%0d", cycle, acc_count, dut.acc_data);
                acc_count = acc_count + 1;
            end
            if (out_valid && out_ready) begin
                if (output_count < 6) begin
                    $display(
                        "TRACE output cycle=%0d idx=%0d expected=%0d actual=%0d",
                        cycle,
                        output_count,
                        expected_stream[output_count],
                        out_data
                    );
                end else begin
                    $display("TRACE output cycle=%0d idx=%0d expected=-1 actual=%0d", cycle, output_count, out_data);
                end
                output_count = output_count + 1;
            end
        end
    end

    initial begin
        clk = 0;
        rst_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        in0_data = 0;
        in1_data = 0;
        out_ready = 1;
        cycle = 0;
        input0_count = 0;
        input1_count = 0;
        join_count = 0;
        acc_count = 0;
        output_count = 0;
        num_packets = 3;

        seq0[0] = 8'd1;
        seq0[1] = 8'd2;
        seq0[2] = 8'd3;
        seq1[0] = 8'd4;
        seq1[1] = 8'd5;
        seq1[2] = 8'd6;
        expected_stream[0] = 8'd5;
        expected_stream[1] = 8'd12;
        expected_stream[2] = 8'd21;
        expected_stream[3] = 8'd5;
        expected_stream[4] = 8'd12;
        expected_stream[5] = 8'd21;

        #15 rst_n = 1;
        #20;

        for (i = 0; i < num_packets; i = i + 1) begin
            @(negedge clk);
            in0_valid = 1;
            in1_valid = 1;
            in0_data = seq0[i];
            in1_data = seq1[i];
            @(posedge clk);
            wait(out_valid);
            #1;
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;
        end

        @(negedge clk);
        rst_n = 0;
        in0_valid = 0;
        in1_valid = 0;
        out_ready = 1;
        #20 rst_n = 1;
        #20;

        for (i = 0; i < num_packets; i = i + 1) begin
            @(negedge clk);
            in0_valid = 1;
            in1_valid = 1;
            in0_data = seq0[i];
            in1_data = seq1[i];
            out_ready = 0;
            if (i == 0) begin
                #30 out_ready = 1;
            end else begin
                #15 out_ready = 1;
            end
            @(posedge clk);
            wait(out_valid);
            #1;
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;
            out_ready = 0;
        end

        #100;
        $finish;
    end
endmodule
