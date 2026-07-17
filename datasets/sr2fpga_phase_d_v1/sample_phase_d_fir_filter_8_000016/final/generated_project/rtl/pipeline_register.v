module pipeline_register #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire s_axis_tvalid,
    output wire s_axis_tready,
    input wire [DATA_WIDTH-1:0] s_axis_tdata,
    output wire m_axis_tvalid,
    input wire m_axis_tready,
    output wire [DATA_WIDTH-1:0] m_axis_tdata
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
  reg [DATA_WIDTH-1:0] data_reg;
  reg valid_reg;

  always @(posedge clk) begin
     if (!rst_n) begin
        valid_reg <= 1'b0;
        data_reg <= {DATA_WIDTH{1'b0}};
     end else begin
        if (s_axis_tvalid && s_axis_tready) begin
           data_reg <= s_axis_tdata;
        end
        if (s_axis_tvalid && s_axis_tready) begin
           valid_reg <= 1'b1;
        end else if (valid_reg && m_axis_tready) begin
           valid_reg <= 1'b0;
        end
     end
  end

  assign s_axis_tready = !valid_reg || m_axis_tready;
  assign m_axis_tvalid = valid_reg;
  assign m_axis_tdata = data_reg;
  // SR2FPGA_BEHAVIOR_END
endmodule
