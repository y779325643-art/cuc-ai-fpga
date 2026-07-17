module stream_join #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    input wire [DATA_WIDTH-1:0] in0_data,
    input wire in1_valid,
    input wire [DATA_WIDTH-1:0] in1_data,
    input wire out_ready,
    output wire in0_ready,
    output wire in1_ready,
    output wire out_valid,
    output wire [2*DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg state;
  reg [2*DATA_WIDTH-1:0] joined_data;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      state <= 1'b0;
      joined_data <= 0;
    end else begin
      case (state)
        1'b0: begin
          if (in0_valid && in1_valid && out_ready) begin
            joined_data <= in0_data + in1_data;
            state <= 1'b1;
          end
        end
        1'b1: begin
          if (out_ready) begin
            state <= 1'b0;
          end
        end
      endcase
    end
  end

  always_comb begin
    in0_ready = (state == 1'b0) && in1_valid && out_ready;
    in1_ready = (state == 1'b0) && in0_valid && out_ready;
    out_valid = (state == 1'b1);
    out_data  = joined_data;
  end
  // SR2FPGA_BEHAVIOR_END
  localparam IDLE = 0;
  localparam JOIN = 0;
  wire _unused_fsm_states = &{1'b0, (IDLE == IDLE), (JOIN == JOIN)};
endmodule
