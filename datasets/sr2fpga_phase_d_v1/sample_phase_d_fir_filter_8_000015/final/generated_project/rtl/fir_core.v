module fir_core #(parameter DATA_WIDTH = 8, parameter TAPS = 4) (
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    input wire valid_in,
    output wire ready_out,
    output wire [7:0] data_out,
    output wire valid_out
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    // Declare internal registers for delay line
    reg [DATA_WIDTH-1:0] delay_line [0:TAPS-1];
    reg [DATA_WIDTH-1:0] data_in_reg;
    reg valid_in_reg;

    // Output registers
    reg [DATA_WIDTH-1:0] data_out_reg;
    reg valid_out_reg;
    reg ready_out_reg;

    // Internal signals for computation
    reg [DATA_WIDTH*2-1:0] products [0:TAPS-1];
    reg [DATA_WIDTH*2+3:0] accumulator;

    // Coefficients array - using default 1,1,1,1 for 4-tap filter
    reg [DATA_WIDTH-1:0] coefficients [0:TAPS-1];

    // Initialize coefficients
    integer i;
    initial begin
      for (i = 0; i < TAPS; i = i + 1) begin
        coefficients[i] = 8'd1;  // Default coefficient value
      end
    end

    // Main processing logic
    always @(posedge clk) begin
      if (!rst_n) begin
        // Reset all delay elements
        integer j;
        for (j = 0; j < TAPS; j = j + 1) begin
          delay_line[j] <= {DATA_WIDTH{1'b0}};
        end
        data_out_reg <= {DATA_WIDTH{1'b0}};
        valid_out_reg <= 1'b0;
        ready_out_reg <= 1'b1;  // Ready to accept data when reset is released
        data_in_reg <= {DATA_WIDTH{1'b0}};
        valid_in_reg <= 1'b0;
      end else begin
        // Register inputs
        data_in_reg <= data_in;
        valid_in_reg <= valid_in;

        // Update delay line when valid input
        if (valid_in) begin
          // Shift delay line
          integer k;
          for (k = TAPS-1; k > 0; k = k - 1) begin
            delay_line[k] <= delay_line[k-1];
          end
          delay_line[0] <= data_in;
        end

        // Compute FIR output
        // First compute products
        integer m;
        for (m = 0; m < TAPS; m = m + 1) begin
          products[m] <= $signed(delay_line[m]) * $signed(coefficients[m]);
        end

        // Then accumulate products
        accumulator <= 0;
        integer n;
        for (n = 0; n < TAPS; n = n + 1) begin
          accumulator <= accumulator + $signed(products[n]);
        end

        // Output the accumulated result
        data_out_reg <= accumulator[DATA_WIDTH-1:0];

        // Valid output follows input with appropriate latency
        // Assuming 4 cycles for full computation (input -> delay -> multiply -> accumulate -> output)
        valid_out_reg <= valid_in_reg;  // This should reflect actual pipeline latency

        // Ready signal indicates we can accept new data
        ready_out_reg <= 1'b1;  // Always ready since we're streaming
      end
    end

    // Second stage to properly pipeline the output
    reg [DATA_WIDTH-1:0] data_out_reg2;
    reg valid_out_reg2;

    always @(posedge clk) begin
      if (!rst_n) begin
        data_out_reg2 <= {DATA_WIDTH{1'b0}};
        valid_out_reg2 <= 1'b0;
      end else begin
        data_out_reg2 <= data_out_reg;
        valid_out_reg2 <= valid_out_reg;
      end
    end

    // Third stage to match expected latency
    reg [DATA_WIDTH-1:0] data_out_reg3;
    reg valid_out_reg3;

    always @(posedge clk) begin
      if (!rst_n) begin
        data_out_reg3 <= {DATA_WIDTH{1'b0}};
        valid_out_reg3 <= 1'b0;
      end else begin
        data_out_reg3 <= data_out_reg2;
        valid_out_reg3 <= valid_out_reg2;
      end
    end

    // Final output stage
    always @(posedge clk) begin
      if (!rst_n) begin
        data_out <= {DATA_WIDTH{1'b0}};
        valid_out <= 1'b0;
      end else begin
        data_out <= data_out_reg3;
        valid_out <= valid_out_reg3;
      end
    end

    // Ready output is always high since we accept data every cycle
    assign ready_out = 1'b1;

    // Unused signal reduction to prevent warnings
    wire _unused_signals = &{1'b0, data_in_reg, valid_in_reg};
  // SR2FPGA_BEHAVIOR_END
endmodule
