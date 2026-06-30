module top (
    input wire clk,
    input wire rst_n,
    input wire s_axi_awvalid,
    output wire s_axi_awready,
    input wire [3:0] s_axi_awaddr,
    input wire s_axi_wvalid,
    output wire s_axi_wready,
    input wire [7:0] s_axi_wdata,
    input wire s_axi_wstrb,
    output wire s_axi_bvalid,
    input wire s_axi_bready,
    input wire s_axi_arvalid,
    output wire s_axi_arready,
    input wire [3:0] s_axi_araddr,
    output wire s_axi_rvalid,
    input wire s_axi_rready,
    output wire [7:0] s_axi_rdata,
    output wire m_axis_tvalid,
    input wire m_axis_tready,
    output wire [15:0] m_axis_tdata,
    output wire m_axis_tlast,
    output wire irq
);

  wire write_valid;
  wire [3:0] write_addr;
  wire [7:0] write_data;
  wire read_valid;
  wire [3:0] read_addr;
  wire start_pulse;
  wire [7:0] sample0;
  wire [7:0] sample1;
  wire stream_done;
  wire irq_state;

  axi_lite_write_ctrl #(
    .DATA_WIDTH(8)
  ) u_axi_lite_write_ctrl (
    .clk(clk),
    .rst_n(rst_n),
    .awvalid(s_axi_awvalid),
    .awready(s_axi_awready),
    .awaddr(s_axi_awaddr),
    .wvalid(s_axi_wvalid),
    .wready(s_axi_wready),
    .wdata(s_axi_wdata),
    .wstrb(s_axi_wstrb),
    .bvalid(s_axi_bvalid),
    .bready(s_axi_bready),
    .write_valid(write_valid),
    .write_addr(write_addr),
    .write_data(write_data)
  );

  axi_lite_read_ctrl u_axi_lite_read_ctrl (
    .clk(clk),
    .rst_n(rst_n),
    .arvalid(s_axi_arvalid),
    .arready(s_axi_arready),
    .araddr(s_axi_araddr),
    .rvalid(s_axi_rvalid),
    .rready(s_axi_rready),
    .read_valid(read_valid),
    .read_addr(read_addr)
  );

  control_reg_bank #(
    .DATA_WIDTH(8)
  ) u_control_reg_bank (
    .clk(clk),
    .rst_n(rst_n),
    .write_valid(write_valid),
    .write_addr(write_addr),
    .write_data(write_data),
    .read_valid(read_valid),
    .read_addr(read_addr),
    .read_data(s_axi_rdata),
    .stream_done(stream_done),
    .start_pulse(start_pulse),
    .sample0(sample0),
    .sample1(sample1),
    .irq_state(irq_state)
  );

  sample_stream_adapter #(
    .DATA_WIDTH(8)
  ) u_sample_stream_adapter (
    .clk(clk),
    .rst_n(rst_n),
    .start(start_pulse),
    .sample0(sample0),
    .sample1(sample1),
    .tvalid(m_axis_tvalid),
    .tready(m_axis_tready),
    .tdata(m_axis_tdata),
    .tlast(m_axis_tlast),
    .stream_done(stream_done)
  );

  irq_status u_irq_status (
    .irq_in(irq_state),
    .irq_out(irq)
  );

endmodule
