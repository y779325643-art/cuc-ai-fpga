module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
    reg [DATA_WIDTH-1:0] data_reg;
    reg valid_reg;
    reg [DATA_WIDTH-1:0] skid_data;
    reg skid_valid;

    assign out_data = valid_reg ? data_reg : skid_data;
    assign out_valid = valid_reg || skid_valid;
    assign in_ready = !(valid_reg && skid_valid);

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        valid_reg <= 1'b0;
        skid_valid <= 1'b0;
      end else begin
        if (out_ready) begin
          if (skid_valid) begin
            valid_reg <= 1'b1;
            data_reg <= skid_data;
            skid_valid <= 1'b0;
          end else begin
            valid_reg <= 1'b0;
          end
        end
        if (in_valid && in_ready) begin
          if (valid_reg && !skid_valid) begin
            skid_valid <= 1'b1;
            skid_data <= in_data;
          end else if (!valid_reg) begin
            valid_reg <= 1'b1;
            data_reg <= in_data;
          end
        end
      end
    end
endmodule
