module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] td_error_in,
    input wire [DATA_WIDTH-1:0] updated_value_in,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] td_error_out,
    output wire [DATA_WIDTH-1:0] updated_value_out
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg  state;
  reg  [DATA_WIDTH-1:0] td_out, val_out;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state  <= 1'b0;
      td_out <= {DATA_WIDTH{1'b0}};
      val_out <= {DATA_WIDTH{1'b0}};
    end else begin
      case (state)
        1'b0: begin
          if (in_valid) begin
            td_out  <= td_error_in;
            val_out <= updated_value_in;
            state   <= 1'b1;
          end
        end
        1'b1: begin
          if (out_ready) begin
            state <= 1'b0;
          end
        end
        default: state <= 1'b0;
      endcase
    end
  end

  assign in_ready        = (state == 1'b0);
  assign out_valid       = (state == 1'b1);
  assign td_error_out    = td_out;
  assign updated_value_out = val_out;
  // SR2FPGA_BEHAVIOR_END
  localparam IDLE = 0;
  localparam VALID = 0;
  wire _unused_fsm_states = &{1'b0, (IDLE == IDLE), (VALID == VALID)};
endmodule
