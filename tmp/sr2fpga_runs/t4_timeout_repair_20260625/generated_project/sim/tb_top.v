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

   reg [7:0] in0_seq [0:2];
   reg [7:0] in1_seq [0:2];
   reg [7:0] expected [0:2];
   integer i;
   integer timeout;
   parameter TIMEOUT_CYCLES = 100;

   initial begin
      in0_seq[0] = 8'd1;
      in0_seq[1] = 8'd2;
      in0_seq[2] = 8'd3;
      in1_seq[0] = 8'd4;
      in1_seq[1] = 8'd5;
      in1_seq[2] = 8'd6;
      expected[0] = 8'd5;
      expected[1] = 8'd12;
      expected[2] = 8'd21;

      clk = 0;
      rst_n = 0;
      in0_valid = 0;
      in1_valid = 0;
      out_ready = 1;
      #20 rst_n = 1;
      #10;
      for (i=0; i<3; i=i+1) begin
         // Assert valid and data
         @(posedge clk);
         in0_valid = 1;
         in0_data = in0_seq[i];
         in1_valid = 1;
         in1_data = in1_seq[i];
         // Wait until handshake occurs
         timeout = TIMEOUT_CYCLES;
         while (!in0_ready || !in1_ready) begin
            @(posedge clk);
            timeout = timeout - 1;
            if (timeout == 0) begin
               $display("TEST_FAIL: timeout waiting for handshake at index %0d", i);
               $finish;
            end
         end
         // Handshake happened at this clock edge, deassert on next cycle
         @(posedge clk);
         in0_valid = 0;
         in1_valid = 0;
         // Wait for out_valid
         timeout = TIMEOUT_CYCLES;
         while (!out_valid) begin
            @(posedge clk);
            timeout = timeout - 1;
            if (timeout == 0) begin
               $display("TEST_FAIL: timeout waiting for out_valid at index %0d", i);
               $finish;
            end
         end
         // Check output
         if (out_data !== expected[i]) begin
            $display("TEST_FAIL: mismatch at %0d, expected %d, got %d", i, expected[i], out_data);
            $finish;
         end
      end
      #10;
      $display("TEST_PASS");
      $finish;
   end
endmodule
