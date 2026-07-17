module fir_core #(parameter DATA_WIDTH = 8, parameter COEFF_WIDTH = 8, parameter TAP_COUNT = 4, parameter ACC_WIDTH = 18, parameter COEFF_0 = 1, parameter COEFF_1 = 2, parameter COEFF_2 = 2, parameter COEFF_3 = 1) (
    input wire clk,
    input wire rst_n,
    input wire sample_in_valid,
    output wire sample_in_ready,
    input wire [DATA_WIDTH-1:0] sample_in_data,
    output wire sample_out_valid,
    input wire sample_out_ready,
    output wire [DATA_WIDTH-1:0] sample_out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] fir_sample_delay_0;
    reg [DATA_WIDTH-1:0] fir_sample_delay_1;
    reg [DATA_WIDTH-1:0] fir_sample_delay_2;
    reg [DATA_WIDTH-1:0] fir_sample_delay_3;
    reg [DATA_WIDTH-1:0] fir_output_data_reg;
    reg fir_output_valid_reg;
    reg [2:0] fir_pipeline_fill_reg;
    reg [2:0] fir_accepted_sample_count;

    wire pipeline_can_advance;
    wire sample_accept;
    wire [ACC_WIDTH-1:0] sample_in_data_ext;
    wire [ACC_WIDTH-1:0] fir_sample_delay_0_ext;
    wire [ACC_WIDTH-1:0] fir_sample_delay_1_ext;
    wire [ACC_WIDTH-1:0] fir_sample_delay_2_ext;
    wire [ACC_WIDTH-1:0] fir_sample_delay_3_ext;
    wire [ACC_WIDTH-1:0] coeff_0_ext;
    wire [ACC_WIDTH-1:0] coeff_1_ext;
    wire [ACC_WIDTH-1:0] coeff_2_ext;
    wire [ACC_WIDTH-1:0] coeff_3_ext;
    wire [ACC_WIDTH-1:0] fir_mac_result;
    wire [DATA_WIDTH-1:0] fir_mac_result_trunc;

    assign pipeline_can_advance = (~fir_output_valid_reg) | sample_out_ready;
    assign sample_in_ready = pipeline_can_advance;
    assign sample_accept = sample_in_valid & sample_in_ready;

    assign sample_in_data_ext = {{(ACC_WIDTH-DATA_WIDTH){1'b0}}, sample_in_data};
    assign fir_sample_delay_0_ext = {{(ACC_WIDTH-DATA_WIDTH){1'b0}}, fir_sample_delay_0};
    assign fir_sample_delay_1_ext = {{(ACC_WIDTH-DATA_WIDTH){1'b0}}, fir_sample_delay_1};
    assign fir_sample_delay_2_ext = {{(ACC_WIDTH-DATA_WIDTH){1'b0}}, fir_sample_delay_2};
    assign fir_sample_delay_3_ext = {{(ACC_WIDTH-DATA_WIDTH){1'b0}}, fir_sample_delay_3};

    assign coeff_0_ext = ACC_WIDTH'(COEFF_0);
    assign coeff_1_ext = ACC_WIDTH'(COEFF_1);
    assign coeff_2_ext = ACC_WIDTH'(COEFF_2);
    assign coeff_3_ext = ACC_WIDTH'(COEFF_3);

    assign fir_mac_result = (sample_in_data_ext * coeff_0_ext) +
                            (fir_sample_delay_0_ext * coeff_1_ext) +
                            (fir_sample_delay_1_ext * coeff_2_ext) +
                            (fir_sample_delay_2_ext * coeff_3_ext);
    assign fir_mac_result_trunc = fir_mac_result[DATA_WIDTH-1:0];

    wire _unused_coeff_width = &{1'b0, COEFF_WIDTH[0]};
    wire _unused_tap_count = &{1'b0, TAP_COUNT[0]};
    wire _unused_oldest_sample = &{1'b0, fir_sample_delay_3_ext};

    generate
      if (ACC_WIDTH > DATA_WIDTH) begin : gen_unused_accumulator_high_bits
        wire _unused_accumulator_high_bits = &{1'b0, fir_mac_result[ACC_WIDTH-1:DATA_WIDTH]};
      end
    endgenerate

    assign sample_out_valid = fir_output_valid_reg;
    assign sample_out_data = fir_output_data_reg;

    always @(posedge clk) begin
      if (!rst_n) begin
        fir_sample_delay_0 <= {DATA_WIDTH{1'b0}};
        fir_sample_delay_1 <= {DATA_WIDTH{1'b0}};
        fir_sample_delay_2 <= {DATA_WIDTH{1'b0}};
        fir_sample_delay_3 <= {DATA_WIDTH{1'b0}};
        fir_output_data_reg <= {DATA_WIDTH{1'b0}};
        fir_output_valid_reg <= 1'b0;
        fir_pipeline_fill_reg <= 3'd0;
        fir_accepted_sample_count <= 3'd0;
      end else if (pipeline_can_advance) begin
        if (sample_accept) begin
          fir_sample_delay_0 <= sample_in_data;
          fir_sample_delay_1 <= fir_sample_delay_0;
          fir_sample_delay_2 <= fir_sample_delay_1;
          fir_sample_delay_3 <= fir_sample_delay_2;
          fir_output_data_reg <= fir_mac_result_trunc;
          fir_output_valid_reg <= 1'b1;
          if (fir_accepted_sample_count < 3'd4) begin
            fir_accepted_sample_count <= fir_accepted_sample_count + 3'd1;
            fir_pipeline_fill_reg <= fir_pipeline_fill_reg + 3'd1;
          end else begin
            fir_accepted_sample_count <= fir_accepted_sample_count;
            fir_pipeline_fill_reg <= fir_pipeline_fill_reg;
          end
        end else begin
          fir_output_valid_reg <= 1'b0;
          fir_output_data_reg <= fir_output_data_reg;
          fir_sample_delay_0 <= fir_sample_delay_0;
          fir_sample_delay_1 <= fir_sample_delay_1;
          fir_sample_delay_2 <= fir_sample_delay_2;
          fir_sample_delay_3 <= fir_sample_delay_3;
          fir_accepted_sample_count <= fir_accepted_sample_count;
          fir_pipeline_fill_reg <= fir_pipeline_fill_reg;
        end
      end else begin
        fir_sample_delay_0 <= fir_sample_delay_0;
        fir_sample_delay_1 <= fir_sample_delay_1;
        fir_sample_delay_2 <= fir_sample_delay_2;
        fir_sample_delay_3 <= fir_sample_delay_3;
        fir_output_data_reg <= fir_output_data_reg;
        fir_output_valid_reg <= fir_output_valid_reg;
        fir_accepted_sample_count <= fir_accepted_sample_count;
        fir_pipeline_fill_reg <= fir_pipeline_fill_reg;
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
