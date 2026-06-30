module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire [None-1:0] clk,
    input wire [None-1:0] rst_n,
    input wire [None-1:0] in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire [None-1:0] in_ready,
    output wire [None-1:0] out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire [None-1:0] out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    localparam IDLE   = 1'b0;
    localparam OUTPUT = 1'b1;
    reg [DATA_WIDTH-1:0] data_reg;
    reg                  valid_reg;
    reg                  state;

    assign in_ready  = !valid_reg || out_ready;
    assign out_valid = valid_reg;
    assign out_data  = data_reg;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        data_reg  <= {DATA_WIDTH{1'b0}};
        valid_reg <= 1'b0;
        state     <= IDLE;
      end else begin
        if (out_ready && valid_reg) begin
          valid_reg <= 1'b0;
        end
        if (in_valid && in_ready) begin
          data_reg  <= in_data;
          valid_reg <= 1'b1;
        end
        state <= valid_reg ? OUTPUT : IDLE;
      end
    end
endmodule
