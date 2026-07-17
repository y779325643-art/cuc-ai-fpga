module stream_stage #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire signed [DATA_WIDTH-1:0] td_error,
    input wire signed [DATA_WIDTH-1:0] updated_value,
    output reg out_valid,
    input wire out_ready,
    output reg signed [DATA_WIDTH-1:0] td_error_out,
    output reg signed [DATA_WIDTH-1:0] updated_value_out
);

  assign in_ready = !out_valid || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      td_error_out <= {DATA_WIDTH{1'b0}};
      updated_value_out <= {DATA_WIDTH{1'b0}};
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        td_error_out <= td_error;
        updated_value_out <= updated_value;
      end
    end
  end

endmodule
