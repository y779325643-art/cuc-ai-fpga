module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] td_error,
    input wire [DATA_WIDTH-1:0] updated_value,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] td_error_out,
    output wire [DATA_WIDTH-1:0] updated_value_out
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    // Internal state
    reg                  valid_r;
    reg [DATA_WIDTH-1:0] td_error_r;
    reg [DATA_WIDTH-1:0] updated_value_r;

    // Ready to accept new data when output buffer empty or downstream accepts current data
    assign in_ready = !valid_r || out_ready;

    // Outputs
    assign out_valid         = valid_r;
    assign td_error_out      = td_error_r;
    assign updated_value_out = updated_value_r;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        valid_r <= 1'b0;
      end else begin
        if (in_valid && in_ready) begin
          // capture new transaction
          td_error_r      <= td_error;
          updated_value_r <= updated_value;
          valid_r         <= 1'b1;
        end else if (valid_r && out_ready) begin
          // handshake complete, mark not valid
          valid_r <= 1'b0;
        end
      end
    end
endmodule
