module tb_top;
    reg clk;
    reg reset_n;
    reg in_valid;
    reg [7:0] in_data;
    wire [15:0] sum;

    top u_top (
        .clk(clk),
        .reset_n(reset_n),
        .in_valid(in_valid),
        .in_data(in_data),
        .sum(sum)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        reset_n = 0;
        in_valid = 0;
        in_data = 0;
        #10 reset_n = 1;
        #5;
        @(posedge clk);
        in_valid = 1; in_data = 10;
        @(posedge clk);
        in_valid = 1; in_data = 20;
        @(posedge clk);
        in_valid = 1; in_data = 30;
        @(posedge clk);
        in_valid = 1; in_data = 40;
        @(posedge clk);
        in_valid = 0;
        repeat (5) @(posedge clk);
        if (sum === 100) begin
            $display("TEST_PASS");
        end else begin
            $display("TEST_FAIL");
        end
        $finish;
    end
endmodule
