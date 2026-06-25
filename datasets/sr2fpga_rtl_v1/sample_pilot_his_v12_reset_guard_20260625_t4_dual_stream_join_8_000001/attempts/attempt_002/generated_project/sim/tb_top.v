module tb_top;
   reg clk, rst_n;
   reg [7:0] in0_data, in1_data;
   reg in0_valid, in1_valid;
   wire in0_ready, in1_ready;
   wire [7:0] out_data;
   wire out_valid;
   reg out_ready;

   top #(.DATA_WIDTH(8)) dut (.*);

   always #5 clk = ~clk;

   reg [7:0] in0_seq [0:2] = {8'd1, 8'd2, 8'd3};
   reg [7:0] in1_seq [0:2] = {8'd4, 8'd5, 8'd6};
   reg [7:0] expected [0:2] = {8'd5, 8'd12, 8'd21};
   integer i;

   initial begin
      clk = 0;
      rst_n = 0;
      in0_valid = 0;
      in1_valid = 0;
      out_ready = 1;
      #20 rst_n = 1;
      #10;
      for (i=0; i<3; i=i+1) begin
         @(posedge clk);
         in0_valid = 1;
         in0_data = in0_seq[i];
         in1_valid = 1;
         in1_data = in1_seq[i];
         // wait for output
         while (!out_valid) @(posedge clk);
         if (out_data !== expected[i]) begin
            $display("TEST_FAIL: mismatch at %0d, expected %d, got %d", i, expected[i], out_data);
            $finish;
         end
         in0_valid = 0;
         in1_valid = 0;
      end
      #10;
      $display("TEST_PASS");
      $finish;
   end
endmodule
