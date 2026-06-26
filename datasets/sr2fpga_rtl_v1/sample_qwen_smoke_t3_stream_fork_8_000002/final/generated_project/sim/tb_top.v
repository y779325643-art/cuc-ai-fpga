`timescale 1ns/1ps
module tb_top();

  parameter DATA_WIDTH = 8;
  parameter TCLK = 10;
  
  reg clk = 0;
  reg rst_n = 0;
  
  reg s_valid = 0;
  wire s_ready;
  reg [DATA_WIDTH-1:0] s_data = 0;
  
  wire m0_valid;
  reg m0_ready = 0;
  wire [DATA_WIDTH-1:0] m0_data;
  
  wire m1_valid;
  reg m1_ready = 0;
  wire [DATA_WIDTH-1:0] m1_data;
  
  integer i;
  integer error_count = 0;
  
  top #(
    .DATA_WIDTH(DATA_WIDTH)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .s_valid(s_valid),
    .s_ready(s_ready),
    .s_data(s_data),
    .m0_valid(m0_valid),
    .m0_ready(m0_ready),
    .m0_data(m0_data),
    .m1_valid(m1_valid),
    .m1_ready(m1_ready),
    .m1_data(m1_data)
  );
  
  always #(TCLK/2) clk = ~clk;
  
  // Helper tasks
  task apply_reset;
  begin
    rst_n = 0;
    repeat(4) @(posedge clk);
    rst_n = 1;
    repeat(2) @(posedge clk);
  end
  endtask
  
  task send_data;
    input [DATA_WIDTH-1:0] data;
  begin
    s_data = data;
    s_valid = 1;
    wait(s_ready == 1);
    @(negedge clk);  // Wait for handshake to complete
    s_valid = 0;
  end
  endtask
  
  task wait_for_output;
    input [DATA_WIDTH-1:0] expected_data;
    input integer timeout_cycles;
  begin
    integer count;
    count = 0;
    m0_ready = 1;
    m1_ready = 1;
    
    while((~m0_valid || ~m1_valid) && count < timeout_cycles) begin
      count = count + 1;
      @(posedge clk);
    end
    
    if(count >= timeout_cycles) begin
      $display("ERROR: Timeout waiting for output");
      error_count = error_count + 1;
    end else begin
      // Check outputs after handshake
      @(posedge clk);
      if(m0_data !== expected_data || m1_data !== expected_data) begin
        $display("ERROR: Expected %h, got m0=%h, m1=%h", expected_data, m0_data, m1_data);
        error_count = error_count + 1;
      end
      
      // Deassert ready after handshake
      m0_ready = 0;
      m1_ready = 0;
    end
  end
  endtask
  
  initial begin
    $display("Starting testbench for stream fork...");
    
    // Apply reset
    apply_reset();
    
    // Test 1: Single transfer
    $display("\nTest 1: Single transfer");
    send_data(8'hAA);
    wait_for_output(8'hAA, 10);
    
    // Test 2: Burst transfer
    $display("\nTest 2: Burst transfer");
    for(i = 0; i < 5; i = i + 1) begin
      send_data(i + 1);
      wait_for_output(i + 1, 10);
    end
    
    // Test 3: Backpressure test - block one output
    $display("\nTest 3: Backpressure test");
    m0_ready = 0;  // Block output 0
    m1_ready = 1;  // Allow output 1
    s_data = 8'hFF;
    s_valid = 1;
    
    // Wait several cycles to ensure input doesn't proceed
    repeat(5) @(posedge clk);
    
    // Verify input is stalled
    if(s_ready !== 0) begin
      $display("ERROR: Input should be stalled due to backpressure");
      error_count = error_count + 1;
    end
    
    // Now allow both outputs
    m0_ready = 1;
    wait_for_output(8'hFF, 10);
    
    // Test 4: Continuous burst with backpressure
    $display("\nTest 4: Continuous burst with backpressure");
    fork
      begin
        for(i = 0; i < 10; i = i + 1) begin
          send_data(i + 10);
        end
      end
      begin
        for(i = 0; i < 6; i = i + 1) begin
          wait_for_output(i + 10, 20);
        end
        // Introduce backpressure
        m1_ready = 0;
        repeat(3) @(posedge clk);
        m1_ready = 1;
        for(i = 6; i < 10; i = i + 1) begin
          wait_for_output(i + 10, 20);
        end
      end
    join
    
    // Final checks
    repeat(5) @(posedge clk);
    
    if(error_count == 0) begin
      $display("TEST_PASS");
    end else begin
      $display("TEST_FAIL: %d errors detected", error_count);
    end
    
    $finish;
  end
  
endmodule
