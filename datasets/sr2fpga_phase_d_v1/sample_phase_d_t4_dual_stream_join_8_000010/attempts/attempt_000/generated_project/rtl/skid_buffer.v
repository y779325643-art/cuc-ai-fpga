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
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [DATA_WIDTH-1:0] in0_skid_storage;
    reg storage_valid_reg;

    wire input_accept;
    wire output_accept;
    wire bypass_path;

    assign in_ready = (~storage_valid_reg) | out_ready;
    assign out_valid = storage_valid_reg | in_valid;
    assign bypass_path = ~storage_valid_reg;
    assign out_data = storage_valid_reg ? in0_skid_storage : in_data;

    assign input_accept = in_valid & in_ready;
    assign output_accept = out_valid & out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        storage_valid_reg <= 1'b0;
        in0_skid_storage <= {DATA_WIDTH{1'b0}};
      end else begin
        if (output_accept) begin
          storage_valid_reg <= 1'b0;
        end

        if (input_accept & ~output_accept) begin
          storage_valid_reg <= 1'b1;
          in0_skid_storage <= in_data;
        end else if (input_accept & output_accept & ~bypass_path) begin
          storage_valid_reg <= 1'b1;
          in0_skid_storage <= in_data;
        end
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
