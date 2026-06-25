module tb_top;
    reg clk, rst_n;
    reg [7:0] in_data;
    reg in_valid;
    wire in_ready;
    wire [7:0] out0_data, out1_data;
    wire out0_valid, out1_valid;
    reg out0_ready, out1_ready;
    integer i;
    integer pass;
    integer count_sent;
    integer count_recv0, count_recv1;
    reg [7:0] expected0[0:1023];
    reg [7:0] expected1[0:1023];
    integer head0, head1;
    integer errors;
    top dut(
        .clk(clk),
        .rst_n(rst_n),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out0_data(out0_data),
        .out0_valid(out0_valid),
        .out0_ready(out0_ready),
        .out1_data(out1_data),
        .out1_valid(out1_valid),
        .out1_ready(out1_ready)
    );
    always #5 clk = ~clk;
    initial begin
        clk = 0;
        rst_n = 0;
        in_valid = 0;
        out0_ready = 0;
        out1_ready = 0;
        count_sent = 0;
        count_recv0 = 0;
        count_recv1 = 0;
        head0 = 0;
        head1 = 0;
        errors = 0;
        @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);
        for (i = 0; i < 50; i = i + 1) begin
            in_data = $random % 256;
            in_valid = 1;
            out0_ready = $random % 2;
            out1_ready = $random % 2;
            @(posedge clk);
            while (!in_ready) begin
                out0_ready = $random % 2;
                out1_ready = $random % 2;
                @(posedge clk);
            end
            expected0[count_sent] = in_data;
            expected1[count_sent] = in_data;
            count_sent = count_sent + 1;
            in_valid = 0;
            @(posedge clk);
        end
        repeat(100) @(posedge clk);
        if (errors == 0 && count_recv0 == count_sent && count_recv1 == count_sent) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end
        $finish;
    end
    always @(posedge clk) begin
        if (out0_valid && out0_ready) begin
            if (head0 >= count_sent) begin
                $display("ERROR: unexpected output0 data");
                errors = errors + 1;
            end else if (out0_data !== expected0[head0]) begin
                $display("ERROR: output0 data mismatch at %0d: expected %0d, got %0d", head0, expected0[head0], out0_data);
                errors = errors + 1;
            end
            head0 = head0 + 1;
            count_recv0 = count_recv0 + 1;
        end
    end
    always @(posedge clk) begin
        if (out1_valid && out1_ready) begin
            if (head1 >= count_sent) begin
                $display("ERROR: unexpected output1 data");
                errors = errors + 1;
            end else if (out1_data !== expected1[head1]) begin
                $display("ERROR: output1 data mismatch at %0d: expected %0d, got %0d", head1, expected1[head1], out1_data);
                errors = errors + 1;
            end
            head1 = head1 + 1;
            count_recv1 = count_recv1 + 1;
        end
    end
endmodule
