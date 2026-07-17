module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire result_valid_i,
    output wire result_ready_o,
    input wire [DATA_WIDTH-1:0] td_error_i,
    input wire [DATA_WIDTH-1:0] updated_value_i,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] td_error_o,
    output wire [DATA_WIDTH-1:0] updated_value_o
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] output_td_error_reg;
    reg [DATA_WIDTH-1:0] output_updated_value_reg;
    reg output_valid_reg;
    reg output_stage_state_reg;

    wire output_can_load;

    assign output_can_load = (!output_valid_reg) || out_ready;
    assign result_ready_o = output_can_load;
    assign out_valid = output_valid_reg;
    assign td_error_o = output_td_error_reg;
    assign updated_value_o = output_updated_value_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        output_td_error_reg <= {DATA_WIDTH{1'b0}};
        output_updated_value_reg <= {DATA_WIDTH{1'b0}};
        output_valid_reg <= 1'b0;
        output_stage_state_reg <= IDLE;
      end else begin
        if (output_can_load) begin
          output_valid_reg <= result_valid_i;
          if (result_valid_i) begin
            output_td_error_reg <= td_error_i;
            output_updated_value_reg <= updated_value_i;
            output_stage_state_reg <= VALID;
          end else begin
            output_stage_state_reg <= IDLE;
          end
        end else begin
          output_valid_reg <= output_valid_reg;
          output_td_error_reg <= output_td_error_reg;
          output_updated_value_reg <= output_updated_value_reg;
          output_stage_state_reg <= VALID;
        end
      end
    end

    wire _unused_output_stage_state = output_stage_state_reg;
  // SR2FPGA_BEHAVIOR_END
  localparam IDLE = 0;
  localparam VALID = 0;
  wire _unused_fsm_states = &{1'b0, (IDLE == IDLE), (VALID == VALID)};
endmodule
