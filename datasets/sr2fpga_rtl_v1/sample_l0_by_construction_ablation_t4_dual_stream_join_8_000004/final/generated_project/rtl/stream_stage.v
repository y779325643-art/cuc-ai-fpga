module stream_stage (
  input  wire        clk,
  input  wire        rst_n,
  input  wire        in_valid,
  input  wire [7:0]  in_data,
  output wire        in_ready,
  output wire        out_valid,
  output wire [7:0]  out_data,
  input  wire        out_ready
);

  reg [7:0]  data_reg;
  reg        valid_reg;

  // we can accept if downstream ready or we have no valid data
  assign in_ready = out_ready || !valid_reg;

  assign out_valid = valid_reg;
  assign out_data  = data_reg;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_reg <= 1'b0;
    end else begin
      if (in_valid & in_ready) begin
        data_reg  <= in_data;
        valid_reg <= 1'b1;
      end else if (out_ready) begin
        // if output handshake without new input, clear valid
        valid_reg <= 1'b0;
      end
    end
  end

endmodule
