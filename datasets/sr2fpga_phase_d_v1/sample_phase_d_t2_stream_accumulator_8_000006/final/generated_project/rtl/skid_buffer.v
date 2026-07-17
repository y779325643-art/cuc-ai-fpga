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
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] input_buffer_data_reg;
    reg input_buffer_occupancy_fsm;

    wire input_buffer_empty;
    wire input_buffer_full;
    wire input_accept;
    wire output_accept;

    assign input_buffer_empty = (input_buffer_occupancy_fsm == 1'b0);
    assign input_buffer_full = (input_buffer_occupancy_fsm == 1'b1);
    assign in_ready = input_buffer_empty || out_ready;
    assign out_valid = input_buffer_full || in_valid;
    assign out_data = input_buffer_full ? input_buffer_data_reg : in_data;
    assign input_accept = in_valid && in_ready;
    assign output_accept = out_valid && out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        input_buffer_occupancy_fsm <= 1'b0;
        input_buffer_data_reg <= {DATA_WIDTH{1'b0}};
      end else begin
        case ({input_accept, output_accept})
          2'b00: begin
            input_buffer_occupancy_fsm <= input_buffer_occupancy_fsm;
            input_buffer_data_reg <= input_buffer_data_reg;
          end
          2'b01: begin
            input_buffer_occupancy_fsm <= 1'b0;
            input_buffer_data_reg <= input_buffer_data_reg;
          end
          2'b10: begin
            input_buffer_occupancy_fsm <= 1'b1;
            input_buffer_data_reg <= in_data;
          end
          2'b11: begin
            input_buffer_occupancy_fsm <= 1'b0;
            input_buffer_data_reg <= input_buffer_data_reg;
          end
          default: begin
            input_buffer_occupancy_fsm <= 1'b0;
            input_buffer_data_reg <= {DATA_WIDTH{1'b0}};
          end
        endcase
      end
    end

    wire _unused_input_buffer_state_flags = &{1'b0, input_buffer_empty, input_buffer_full};
  // SR2FPGA_BEHAVIOR_END
  localparam empty = 0;
  localparam full = 0;
  wire _unused_fsm_states = &{1'b0, (empty == empty), (full == full)};
endmodule
