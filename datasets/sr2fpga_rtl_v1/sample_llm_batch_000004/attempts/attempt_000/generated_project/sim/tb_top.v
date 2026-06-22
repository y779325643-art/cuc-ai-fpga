module tb_top;
    reg clk;
    reg rst_n;
    reg wr_en;
    reg [11:0] wr_data;
    reg [7:0] wr_addr;
    reg rd_en;
    reg [7:0] rd_addr;
    wire [11:0] rd_data;

    top uut (.*);

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst_n = 0;
        wr_en = 0;
        rd_en = 0;
        #20 rst_n = 1;
        #10;
        wr_en = 1;
        wr_addr = 8'h00;
        wr_data = 12'hABC;
        #10;
        wr_addr = 8'h01;
        wr_data = 12'h123;
        #10;
        wr_en = 0;
        #10;
        rd_en = 1;
        rd_addr = 8'h00;
        #10;
        if (rd_data !== 12'hABC) begin
            $display("ERROR: expected ABC, got %h", rd_data);
            $finish;
        end
        rd_addr = 8'h01;
        #10;
        if (rd_data !== 12'h123) begin
            $display("ERROR: expected 123, got %h", rd_data);
            $finish;
        end
        rd_en = 0;
        #10;
        $display("TEST_PASS");
        #10;
        $finish;
    end

    initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, tb_top);
    end
endmodule
