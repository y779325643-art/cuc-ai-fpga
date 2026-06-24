module tb_top;

    reg clk;
    reg rst_n;
    reg in_valid;
    reg [7:0] in_data;
    wire [7:0] sum;
    wire skid_ready;

    top u_top (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .sum(sum),
        .skid_ready(skid_ready)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        rst_n = 0;
        in_valid = 0;
        in_data = 0;
        #10;
        rst_n = 1;
        #10;

        // Test: send values 3, 5, 2
        @(posedge clk);
        in_valid = 1;
        in_data = 8'd3;
        @(posedge clk);
        in_data = 8'd5;
        @(posedge clk);
        in_data = 8'd2;
        @(posedge clk);
        in_valid = 0;

        // Wait some cycles for pipeline
        #100;

        if (sum == 8'd10) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end
        $finish;
    end

endmodule
