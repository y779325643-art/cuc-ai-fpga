`timescale 1ns/100ps

module tb_top;

reg clk;
reg rst_n;
reg [7:0] in0_data;
reg       in0_valid;
wire      in0_ready;
reg [7:0] in1_data;
reg       in1_valid;
wire      in1_ready;
wire [7:0] out_data;
wire      out_valid;
reg       out_ready;

// expected sequence of cumulative sums for test vectors: (1,1),(2,2),(3,3),(4,4),(5,5) => 2,4,6,8,10 => cumulative: 2,6,12,20,30
reg [7:0] expected_seq [0:4];  // unpacked array, no initializer
integer seq_idx;

// DUT
 top uut (
    .clk(clk),
    .rst_n(rst_n),
    .in0_data(in0_data),
    .in0_valid(in0_valid),
    .in0_ready(in0_ready),
    .in1_data(in1_data),
    .in1_valid(in1_valid),
    .in1_ready(in1_ready),
    .out_data(out_data),
    .out_valid(out_valid),
    .out_ready(out_ready)
);

// clock generation
always #5 clk = ~clk;

initial begin
    // initialize expected values
    expected_seq[0] = 8'd2;
    expected_seq[1] = 8'd6;
    expected_seq[2] = 8'd12;
    expected_seq[3] = 8'd20;
    expected_seq[4] = 8'd30;

    // initial conditions
    clk = 1'b0;
    rst_n = 1'b0;
    in0_valid = 1'b0;
    in0_data = 8'd0;
    in1_valid = 1'b0;
    in1_data = 8'd0;
    out_ready = 1'b1;   // keep output always ready

    #15 rst_n = 1'b1;   // release reset after a few cycles
    #10;

    // send test pairs
    send_pair(8'd1, 8'd1);
    send_pair(8'd2, 8'd2);
    send_pair(8'd3, 8'd3);
    send_pair(8'd4, 8'd4);
    send_pair(8'd5, 8'd5);

    // after sending all pairs, wait for output to complete
    // we will check output sequence as they arrive
    seq_idx = 0;
    // wait for all expected output transactions
    repeat (1000) begin
        @(posedge clk);
        if (out_valid) begin
            #1; // small delay to avoid simulation race
            if (seq_idx >= 5) begin
                $display("TEST_FAIL: unexpected extra output");
                $finish;
            end
            if (out_data !== expected_seq[seq_idx]) begin
                $display("TEST_FAIL: output mismatch at index %0d: expected %0d, got %0d", seq_idx, expected_seq[seq_idx], out_data);
                $finish;
            end
            $display("Output %0d: %0d correct", seq_idx, out_data);
            seq_idx = seq_idx + 1;
            if (seq_idx == 5) begin
                $display("TEST_PASS");
                $finish;
            end
        end
    end
    $display("TEST_FAIL: timeout");
    $finish;
end

// task to send a pair (a,b) with handshake
task send_pair;
    input [7:0] a;
    input [7:0] b;
    begin
        @(negedge clk);
        in0_valid = 1'b1;
        in0_data  = a;
        in1_valid = 1'b1;
        in1_data  = b;
        // wait until both inputs are accepted
        wait_handshake();
        @(negedge clk);
        in0_valid = 1'b0;
        in1_valid = 1'b0;
    end
endtask

// task to wait for the pair to be accepted by both skid buffers
task wait_handshake;
    integer count;
    begin
        count = 0;
        while (!(in0_ready || !in0_valid) && !(in1_ready || !in1_valid) && count < 1000) begin
            @(posedge clk);
            count = count + 1;
        end
        if (count == 1000) begin
            $display("TEST_FAIL: handshake timeout");
            $finish;
        end
        // wait one more cycle to ensure data is sampled before deasserting valid
        @(posedge clk);
    end
endtask

endmodule
