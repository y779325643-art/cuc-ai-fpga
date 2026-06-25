module tb_top;

parameter DATA_WIDTH = 8;
parameter CLK_PERIOD = 10;

reg clk;
reg rst_n;
reg [DATA_WIDTH-1:0] in0_data, in1_data;
reg in0_valid, in1_valid;
wire in0_ready, in1_ready;
wire [DATA_WIDTH-1:0] out_data;
wire out_valid;
reg out_ready;

top #(DATA_WIDTH) dut (
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

initial clk = 0;
always #(CLK_PERIOD/2) clk = ~clk;

integer test_pass;
integer cycle_count;
integer i;
reg [DATA_WIDTH-1:0] expected_acc;

initial begin
    test_pass = 1;
    rst_n = 0;
    in0_valid = 0;
    in1_valid = 0;
    out_ready = 1;
    in0_data = 0;
    in1_data = 0;
    expected_acc = 0;
    #(CLK_PERIOD*2) rst_n = 1;
    #(CLK_PERIOD*2);

    // Test 1: simple join accumulate
    $display("Starting Test 1: simple_join_accumulate");
    for (i=0; i<10; i=i+1) begin
        @(negedge clk);
        in0_data = i;
        in1_data = i+10;
        in0_valid = 1;
        in1_valid = 1;
        expected_acc = expected_acc + (i + (i+10));
        #(CLK_PERIOD*4);
        if (out_valid && out_data !== expected_acc) begin
            $display("ERROR: Test 1, i=%0d: expected out_data=%0d, got %0d", i, expected_acc, out_data);
            test_pass = 0;
        end
        #(CLK_PERIOD);
    end

    // Test 2: backpressure
    $display("Starting Test 2: backpressure");
    rst_n = 0;
    #(CLK_PERIOD*2);
    rst_n = 1;
    #(CLK_PERIOD*2);
    expected_acc = 0;
    for (i=0; i<5; i=i+1) begin
        @(negedge clk);
        in0_data = i;
        in1_data = i*2;
        in0_valid = 1;
        in1_valid = 1;
        expected_acc = expected_acc + (i + i*2);
        if (i % 2 == 0) begin
            out_ready = 1;
        end else begin
            out_ready = 0;
        end
        cycle_count = 0;
        while (cycle_count < 20 && !(out_valid && out_ready)) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
        end
        if (cycle_count == 20) begin
            $display("ERROR: Test 2 timeout at i=%0d", i);
            test_pass = 0;
        end
        @(negedge clk);
        if (out_data !== expected_acc) begin
            $display("ERROR: Test 2, i=%0d: expected out_data=%0d, got %0d", i, expected_acc, out_data);
            test_pass = 0;
        end
    end

    #(CLK_PERIOD*10);
    if (test_pass) begin
        $display("TEST_PASS");
    end else begin
        $display("TEST_FAIL");
    end
    $finish;
end

endmodule
