module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    input wire out_ready,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg [DATA_WIDTH-1:0] data_reg;
  reg [DATA_WIDTH-1:0] skid_reg;
  reg [1:0] state;
  localparam EMPTY = 2'd0;
  localparam ONE   = 2'd1;
  localparam TWO   = 2'd2;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      state <= EMPTY;
      data_reg <= '0;
      skid_reg <= '0;
    end else begin
      case (state)
        EMPTY: begin
          if (in_valid && in_ready) begin
            data_reg <= in_data;
            state <= ONE;
          end
        end
        ONE: begin
          if (out_ready && in_valid && in_ready) begin
            data_reg <= in_data;
          end else if (out_ready) begin
            state <= EMPTY;
          end else if (in_valid && in_ready) begin
            skid_reg <= in_data;
            state <= TWO;
          end
        end
        TWO: begin
          if (out_ready) begin
            data_reg <= skid_reg;
            state <= ONE;
          end
        end
        default: state <= EMPTY;
      endcase
    end
  end

  always_comb begin
    in_ready  = (state != TWO);
    out_valid = (state != EMPTY);
    out_data  = data_reg;
  end
  // SR2FPGA_BEHAVIOR_END
endmodule
