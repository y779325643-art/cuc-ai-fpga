module tb_top;

    reg clk;
    reg rst_n;
    reg [7:0] in0_data;
    reg in0_valid;
    wire in0_ready;
    reg [7:0] in1_data;
    reg in1_valid;
    wire in1_ready;
    reg clear;
    wire [7:0] out_data;
    wire out_valid;
    reg out_ready;

    integer errors;

    top #(.WIDTH(8)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .in0_data(in0_data),
        .in0_valid(in0_valid),
        .in0_ready(in0_ready),
        .in1_data(in1_data),
        .in1_valid(in1_valid),
        .in1_ready(in1_ready),
        .clear(clear),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );

    always #5 clk = ~clk;

    task check;
        input [7:0] expected;
        input [7:0] actual;
        input string msg;
        if (expected !== actual) begin
            $display("TEST_FAIL: %s expected %d, got %d", msg, expected, actual);
            errors = errors + 1;
        end else begin
            $display("TEST_PASS: %s", msg);
        end
    endtask

    initial begin
        clk = 0;
        errors = 0;
        rst_n = 0;
        in0_data = 0;
        in0_valid = 0;
        in1_data = 0;
        in1_valid = 0;
        clear = 0;
        out_ready = 1;

        #15;
        rst_n = 1;
        #10;

        // reset_check
        check(8'h00, out_data, "After reset, out_data should be 0");
        check(1'b0, out_valid, "After reset, out_valid should be 0");
        check(1'b1, in0_ready, "After reset, in0_ready should be 1");
        check(1'b1, in1_ready, "After reset, in1_ready should be 1");

        // basic_flow: drive two input samples
        @(posedge clk);
        in0_data = 8'h05;
        in0_valid = 1;
        in1_data = 8'h03;
        in1_valid = 1;
        @(posedge clk);
        in0_valid = 0;
        in1_valid = 0;
        @(posedge clk);
        #5;
        // After pipeline, output should be 0x05+0x03 = 0x08
        // But due to accumulator, it accumulates: first join sum added, then output stage.
        // The accumulator adds the join output to its register (initially 0), so after first handshake, acc_reg = 8.
        // Then out_stage latches it, and after another clock, it appears at output.
        // Wait for out_valid.
        wait(out_valid);
        #5;
        check(8'h08, out_data, "After first join, out_data should be 8");

        // second sample: add more
        @(posedge clk);
        in0_data = 8'h02;
        in0_valid = 1;
        in1_data = 8'h01;
        in1_valid = 1;
        @(posedge clk);
        in0_valid = 0;
        in1_valid = 0;
        wait(out_valid);
        #5;
        // accumulator was 8, now add 3 => 11
        check(8'h0B, out_data, "After second join, out_data should be 11");

        // clear_operation
        @(posedge clk);
        clear = 1;
        @(posedge clk);
        clear = 0;
        #10;
        // After clear, accumulator resets to 0, but output stage may still have old value? Actually, out_stage is a pipeline register after accumulator. The accumulator output goes to out_stage. When clear, acc_reg becomes 0 immediately on next clock, but out_stage still holds previous value until next handshake. We need to check later after another output handshake.
        // To check, we can drive another join and see output.
        @(posedge clk);
        in0_data = 8'h01;
        in0_valid = 1;
        in1_data = 8'h01;
        in1_valid = 1;
        @(posedge clk);
        in0_valid = 0;
        in1_valid = 0;
        wait(out_valid);
        #5;
        // accumulator should be 0+2 = 2
        check(8'h02, out_data, "After clear and new join, out_data should be 2");

        // backpressure
        @(posedge clk);
        out_ready = 0; // stall output
        in0_data = 8'h10;
        in0_valid = 1;
        in1_data = 8'h20;
        in1_valid = 1;
        @(posedge clk);
        // At this point, out_ready is 0, so join should not accept inputs, in0_ready and in1_ready should be low.
        check(1'b0, in0_ready, "When out_ready low, in0_ready should be low");
        check(1'b0, in1_ready, "When out_ready low, in1_ready should be low");
        @(posedge clk);
        out_ready = 1;
        // Now inputs should be accepted on next clock when out_ready goes high.
        @(posedge clk);
        wait(out_valid);
        #5;
        // accumulator was 2, now add 0x30 = 48 => 50
        check(8'h32, out_data, "After backpressure, out_data should be 50 (0x32)");

        if (errors == 0) begin
            $display("TEST_PASS: All tests passed.");
        end else begin
            $display("TEST_FAIL: %d errors occurred.", errors);
        end
        $finish;
    end

endmodule
