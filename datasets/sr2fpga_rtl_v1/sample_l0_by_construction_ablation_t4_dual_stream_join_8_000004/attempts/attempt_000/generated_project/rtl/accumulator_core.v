module accumulator_core (
  input  wire        clk,
  input  wire        rst_n,
  input  wire        sample_valid,
  input  wire [7:0]  sample_data,
  output wire        sample_ready,
  output wire [7:0]  sum,
  output wire        out_valid,
  input  wire        out_ready
);

  reg [7:0]  sum_reg;
  reg        valid_reg;

  // We can accept a new sample only when downstream is ready (output will be consumed)
  assign sample_ready = out_ready;

  assign sum       = sum_reg;
  assign out_valid = valid_reg;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum_reg   <= 0;
      valid_reg <= 1'b0;
    end else begin
      if (sample_valid & sample_ready) begin
        sum_reg   <= sum_reg + sample_data;
        valid_reg <= 1'b1;
      end else if (out_ready & valid_reg) begin
        // If no new sample, clear valid on output handshake
        valid_reg <= 1'b0;
      end
    end
  end

endmodule
