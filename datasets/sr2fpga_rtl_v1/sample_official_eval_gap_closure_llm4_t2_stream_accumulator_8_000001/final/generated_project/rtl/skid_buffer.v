module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    localparam BUF_EMPTY = 1'b0;
    localparam BUF_FULL  = 1'b1;
    reg [DATA_WIDTH-1:0] data_reg;
    reg valid_reg;
    reg state;
    assign out_data = data_reg;
    assign out_valid = valid_reg;
    assign in_ready = (state == BUF_EMPTY) ? 1'b1 : out_ready;
    always @(posedge clk) begin
      if (!rst_n) begin
        data_reg <= 0;
        valid_reg <= 1'b0;
        state <= BUF_EMPTY;
      end else begin
        if (in_valid & in_ready) begin
          data_reg <= in_data;
          valid_reg <= 1'b1;
          state <= BUF_FULL;
        end else if (out_ready & valid_reg) begin
          valid_reg <= 1'b0;
          state <= BUF_EMPTY;
        end
      end
    end
  localparam EMPTY = 0;
  localparam FULL = 0;
endmodule
