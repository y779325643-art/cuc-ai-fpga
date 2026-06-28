`timescale 1ns / 1ps

module tb_top;

    // Parameters
    parameter NUM_DATA = 10;
    parameter MAX_CYCLES = 500;

    // DUT signals
    reg clk;
    reg nreset;
    reg in_valid;
    reg [7:0] in_data;
    wire in_ready;
    wire out0_valid;
    wire [7:0] out0_data;
    reg out0_ready;
    wire out1_valid;
    wire [7:0] out1_data;
    reg out1_ready;

    // Testbench variables
    reg [7:0] test_data [0:NUM_DATA-1];
    reg [7:0] out0_received [0:NUM_DATA-1];
    reg [7:0] out1_received [0:NUM_DATA-1];
    integer out0_cnt, out1_cnt;
    integer send_idx;
    integer cycle_cnt;
    integer i;
    reg send_done;
    reg out0_done, out1_done;

    // DUT instantiation
    top u_top (
        .clk(clk),
        .nreset(nreset),
        .in_valid(in_valid),
        .in_data(in_data),
        .in_ready(in_ready),
        .out0_valid(out0_valid),
        .out0_data(out0_data),
        .out0_ready(out0_ready),
        .out1_valid(out1_valid),
        .out1_data(out1_data),
        .out1_ready(out1_ready)
    );

    // Clock generator (100 MHz)
    always #5 clk = ~clk;

    // Initialization
    initial begin
        clk = 0;
        nreset = 0;
        in_valid = 0;
        in_data = 0;
        out0_ready = 1;
        out1_ready = 1;
        send_idx = 0;
        out0_cnt = 0;
        out1_cnt = 0;
        cycle_cnt = 0;
        send_done = 0;
        out0_done = 0;
        out1_done = 0;

        // Initialize test data
        test_data[0] = 8'hA5;
        test_data[1] = 8'h5A;
        test_data[2] = 8'hFF;
        test_data[3] = 8'h00;
        test_data[4] = 8'h33;
        test_data[5] = 8'hCC;
        test_data[6] = 8'h12;
        test_data[7] = 8'h34;
        test_data[8] = 8'h56;
        test_data[9] = 8'h78;

        // Release reset after a few cycles
        #20 nreset = 1;
    end

    // Cycle counter
    always @(posedge clk) begin
        if (nreset) begin
            cycle_cnt <= cycle_cnt + 1;
        end else begin
            cycle_cnt <= 1;
        end
        if (cycle_cnt > MAX_CYCLES) begin
            $display("TEST_FAIL: Timeout reached");
            $finish;
        end
    end

    // Input driver (negedge clk to avoid races)
    always @(negedge clk or negedge nreset) begin
        if (!nreset) begin
            in_valid <= 0;
            send_idx <= 0;
            send_done <= 0;
        end else begin
            if (!send_done) begin
                if (send_idx < NUM_DATA) begin
                    in_valid <= 1;
                    if (in_ready) begin
                        in_data <= test_data[send_idx];
                        send_idx <= send_idx + 1;
                    end
                end else begin
                    in_valid <= 0;
                    send_done <= 1;
                end
            end else begin
                in_valid <= 0;
            end
        end
    end

    // Random back-pressure generators (toggle every few cycles)
    reg [3:0] backpressure_cnt0;
    reg [3:0] backpressure_cnt1;

    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            out0_ready <= 1;
            out1_ready <= 1;
            backpressure_cnt0 <= 0;
            backpressure_cnt1 <= 0;
        end else begin
            // out0 ready toggles based on counter
            if (backpressure_cnt0 == 3) begin
                out0_ready <= ~out0_ready;
                backpressure_cnt0 <= 0;
            end else begin
                backpressure_cnt0 <= backpressure_cnt0 + 1;
            end
            // out1 ready toggles with different timing
            if (backpressure_cnt1 == 5) begin
                out1_ready <= ~out1_ready;
                backpressure_cnt1 <= 0;
            end else begin
                backpressure_cnt1 <= backpressure_cnt1 + 1;
            end
        end
    end

    // Output monitors (sample on negedge after DUT updates)
    always @(negedge clk or negedge nreset) begin
        if (!nreset) begin
            out0_cnt <= 0;
            out1_cnt <= 0;
            out0_done <= 0;
            out1_done <= 0;
            for (i = 0; i < NUM_DATA; i = i + 1) begin
                out0_received[i] = 0;
                out1_received[i] = 0;
            end
        end else if (!out0_done) begin
            if (out0_valid && out0_ready) begin
                out0_received[out0_cnt] <= out0_data;
                out0_cnt <= out0_cnt + 1;
                if (out0_cnt == NUM_DATA-1) out0_done <= 1;
            end
        end
    end

    always @(negedge clk or negedge nreset) begin
        if (!nreset) begin
            out1_cnt <= 0;
            out1_done <= 0;
        end else if (!out1_done) begin
            if (out1_valid && out1_ready) begin
                out1_received[out1_cnt] <= out1_data;
                out1_cnt <= out1_cnt + 1;
                if (out1_cnt == NUM_DATA-1) out1_done <= 1;
            end
        end
    end

    // Check condition
    always @(posedge clk) begin
        if (out0_done && out1_done && send_done) begin
            // Compare sequences
            for (i = 0; i < NUM_DATA; i = i + 1) begin
                if (out0_received[i] !== test_data[i]) begin
                    $display("TEST_FAIL: out0 data mismatch at index %0d, expected %0h got %0h", i, test_data[i], out0_received[i]);
                    $finish;
                end
                if (out1_received[i] !== test_data[i]) begin
                    $display("TEST_FAIL: out1 data mismatch at index %0d, expected %0h got %0h", i, test_data[i], out1_received[i]);
                    $finish;
                end
            end
            $display("TEST_PASS");
            $finish;
        end
    end

endmodule
