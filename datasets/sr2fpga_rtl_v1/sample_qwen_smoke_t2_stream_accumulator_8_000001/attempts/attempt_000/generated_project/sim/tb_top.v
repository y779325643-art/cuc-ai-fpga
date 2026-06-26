`timescale 1ns / 1ps
module tb_top();

  reg clk = 0;
  reg rst_n = 0;
  
  // Input signals
  reg s_axis_valid = 0;
  reg [7:0] s_axis_data = 0;
  reg m_axis_ready = 0;
  
  // Output signals
  wire s_axis_ready;
  wire m_axis_valid;
  wire [7:0] m_axis_data;
  
  // Test variables
  integer cycle_count = 0;
  integer error_count = 0;
  
  // DUT instance
  qwen_smoke_t2_stream_accumulator_8_000001 dut (
    .clk(clk),
    .rst_n(rst_n),
    .s_axis_valid(s_axis_valid),
    .s_axis_ready(s_axis_ready),
    .s_axis_data(s_axis_data),
    .m_axis_valid(m_axis_valid),
    .m_axis_ready(m_axis_ready),
    .m_axis_data(m_axis_data)
  );
  
  // Clock generation
  always #5 clk = ~clk; // 10ns period = 100MHz
  
  // Helper tasks
  task apply_reset;
  begin
    rst_n = 0;
    repeat(3) @(posedge clk);
    rst_n = 1;
    $display("Reset applied at time %t", $time);
  end
  endtask
  
  task send_sample;
    input [7:0] data;
  begin
    s_axis_data <= data;
    s_axis_valid <= 1;
    wait(s_axis_ready == 1);
    @(negedge clk);  // Wait for handshake
    s_axis_valid <= 0;
    $display("Sent sample: %d at time %t", data, $time);
  end
  endtask
  
  task wait_for_output;
    input [7:0] expected;
    input integer timeout_cycles;
  begin
    integer timeout_counter = 0;
    m_axis_ready <= 1;
    while (m_axis_valid != 1 && timeout_counter < timeout_cycles) begin
      timeout_counter = timeout_counter + 1;
      @(posedge clk);
    end
    
    if (timeout_counter >= timeout_cycles) begin
      $display("ERROR: Timeout waiting for output at time %t", $time);
      error_count = error_count + 1;
    end else begin
      // Check output after posedge clk settles
      #1;
      if (m_axis_data !== expected) begin
        $display("ERROR: Expected %d, got %d at time %t", expected, m_axis_data, $time);
        error_count = error_count + 1;
      end else begin
        $display("SUCCESS: Got expected output %d at time %t", m_axis_data, $time);
      end
    end
    m_axis_ready <= 0;
  end
  endtask
  
  initial begin
    $display("Starting test at time %t", $time);
    
    // Apply reset
    apply_reset();
    
    // Wait for reset to complete
    repeat(2) @(posedge clk);
    
    // Test 1: Single sample accumulation
    $display("\n--- Test 1: Single sample accumulation ---");
    send_sample(8'd42);
    wait_for_output(8'd42, 10);
    
    // Test 2: Multiple sample accumulation
    $display("\n--- Test 2: Multiple sample accumulation ---");
    send_sample(8'd10);
    wait_for_output(8'd52, 10);  // 42 + 10 = 52
    
    send_sample(8'd20);
    wait_for_output(8'd72, 10);  // 52 + 20 = 72
    
    send_sample(8'd30);
    wait_for_output(8'd102, 10);  // 72 + 30 = 102
    
    // Test 3: Overflow behavior
    $display("\n--- Test 3: Overflow behavior ---");
    send_sample(8'd155);  // This should cause overflow: 102 + 155 = 257, which is 1 in 8-bit
    wait_for_output(8'd1, 10);  // 257 % 256 = 1
    
    // Test 4: Back-to-back transfers
    $display("\n--- Test 4: Back-to-back transfers ---");
    s_axis_data <= 8'd5;
    s_axis_valid <= 1;
    wait(s_axis_ready == 1);
    @(negedge clk);
    
    s_axis_data <= 8'd10;
    s_axis_valid <= 1;
    wait(s_axis_ready == 1);
    @(negedge clk);
    s_axis_valid <= 0;
    
    // Now check outputs
    m_axis_ready <= 1;
    wait(m_axis_valid == 1);
    #1;
    if (m_axis_data !== 8'd6) begin  // Previous value was 1, now 1+5=6
      $display("ERROR: Expected 6 for first back-to-back output, got %d", m_axis_data);
      error_count = error_count + 1;
    end else begin
      $display("SUCCESS: First back-to-back output correct: %d", m_axis_data);
    end
    
    wait(m_axis_valid == 1);
    #1;
    if (m_axis_data !== 8'd16) begin  // Previous was 6, now 6+10=16
      $display("ERROR: Expected 16 for second back-to-back output, got %d", m_axis_data);
      error_count = error_count + 1;
    end else begin
      $display("SUCCESS: Second back-to-back output correct: %d", m_axis_data);
    end
    m_axis_ready <= 0;
    
    // Final checks
    repeat(5) @(posedge clk);
    
    if (error_count == 0) begin
      $display("\nTEST_PASS: All tests passed");
    end else begin
      $display("\nTEST_FAIL: %d errors detected", error_count);
    end
    
    $finish;
  end
  
  // Timeout protection
  initial begin
    #10000;
    if (error_count == 0) begin
      $display("\nTEST_TIMEOUT: Simulation ended without completion");
    end
    $finish;
  end
  
endmodule
