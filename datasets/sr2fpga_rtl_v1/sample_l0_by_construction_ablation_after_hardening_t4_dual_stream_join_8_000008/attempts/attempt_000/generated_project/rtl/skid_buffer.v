module skid_buffer #(parameter DATA_WIDTH = 0) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
    // Two-entry skid buffer
    reg out_valid_reg;
    reg [DATA_WIDTH-1:0] out_data_reg;
    reg buffer_full;
    reg [DATA_WIDTH-1:0] buffer_data;

    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;
    assign in_ready = !buffer_full;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_reg <= 1'b0;
        buffer_full <= 1'b0;
      end else begin
        if (out_ready || !out_valid_reg) begin
          if (buffer_full) begin
            out_data_reg <= buffer_data;
            out_valid_reg <= 1'b1;
            buffer_full <= 1'b0;
          end else if (in_valid && !buffer_full) begin
            out_data_reg <= in_data;
            out_valid_reg <= 1'b1;
          end else begin
            out_valid_reg <= 1'b0;
          end
        end else begin
          if (in_valid && !buffer_full) begin
            buffer_data <= in_data;
            buffer_full <= 1'b1;
          end
        end
      end
    end
endmodule
