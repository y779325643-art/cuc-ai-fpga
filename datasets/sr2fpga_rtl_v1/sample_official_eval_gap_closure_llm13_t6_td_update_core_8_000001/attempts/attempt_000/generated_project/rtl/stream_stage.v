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
    reg valid_reg;
    reg [DATA_WIDTH-1:0] td_error_reg, updated_value_reg;
    assign in_ready = !valid_reg;
    assign out_valid = valid_reg;
    assign td_error_out = td_error_reg;
    assign updated_value_out = updated_value_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        valid_reg <= 1'b0;
        td_error_reg <= {DATA_WIDTH{1'b0}};
        updated_value_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (in_valid && in_ready) begin
          valid_reg <= 1'b1;
          td_error_reg <= td_error;
          updated_value_reg <= updated_value;
        end else if (valid_reg && out_ready) begin
          valid_reg <= 1'b0;
        end
      end
    end
endmodule
