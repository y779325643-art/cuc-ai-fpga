module skid_buffer (
  input  wire        clk,
  input  wire        rst_n,
  input  wire        in_valid,
  input  wire [7:0]  in_data,
  output wire        in_ready,
  output wire        out_valid,
  output wire [7:0]  out_data,
  input  wire        out_ready
);

  reg         valid_reg;
  reg  [7:0]  data_reg;

  // in_ready: we can accept new data if downstream ready or we have no valid data stored
  assign in_ready = out_ready || !valid_reg;

  // out_valid: either we have stored data or new data is available (bypass)
  assign out_valid = valid_reg || in_valid;

  // out_data: select stored or bypass
  assign out_data = valid_reg ? data_reg : in_data;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_reg <= 1'b0;
    end else begin
      // consume stored data when downstream ready and we are not bypassing new
      if (out_ready && valid_reg)
        valid_reg <= 1'b0;

      // store new data if it can not be bypassed
      if (in_valid && in_ready) begin
        if (out_ready && !valid_reg) begin
          // bypass: data passes straight to output, nothing to store
        end else begin
          data_reg  <= in_data;
          valid_reg <= 1'b1;
        end
      end
    end
  end

endmodule
