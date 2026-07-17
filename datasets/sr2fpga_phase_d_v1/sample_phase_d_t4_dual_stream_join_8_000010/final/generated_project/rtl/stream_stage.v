module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg out_stage_valid_fsm;
    reg [DATA_WIDTH-1:0] out_stage_data_reg;

    wire load_en;
    wire consume_en;

    assign in_ready = (~out_stage_valid_fsm) | out_ready;
    assign load_en = in_valid & in_ready;
    assign consume_en = out_valid & out_ready;
    assign out_valid = out_stage_valid_fsm;
    assign out_data = out_stage_data_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        out_stage_valid_fsm <= 1'b0;
        out_stage_data_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        if (load_en) begin
          out_stage_data_reg <= in_data;
          out_stage_valid_fsm <= 1'b1;
        end else if (consume_en) begin
          out_stage_valid_fsm <= 1'b0;
        end
      end
    end
  // SR2FPGA_BEHAVIOR_END
  localparam EMPTY = 0;
  localparam FULL = 0;
  wire _unused_fsm_states = &{1'b0, (EMPTY == EMPTY), (FULL == FULL)};
endmodule
