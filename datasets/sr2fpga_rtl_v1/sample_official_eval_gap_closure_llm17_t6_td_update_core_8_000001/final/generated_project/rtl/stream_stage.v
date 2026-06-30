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
    reg out_valid_r;
    reg [DATA_WIDTH-1:0] td_error_r;
    reg [DATA_WIDTH-1:0] updated_value_r;
    assign out_valid = out_valid_r;
    assign td_error_out = td_error_r;
    assign updated_value_out = updated_value_r;
    assign in_ready = out_ready | !out_valid_r;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_r <= 1'b0;
        td_error_r <= 0;
        updated_value_r <= 0;
      end else begin
        if (in_valid && in_ready) begin
          out_valid_r <= 1'b1;
          td_error_r <= td_error;
          updated_value_r <= updated_value;
        end else if (out_ready && out_valid_r) begin
          out_valid_r <= 1'b0;
        end
      end
    end
endmodule
