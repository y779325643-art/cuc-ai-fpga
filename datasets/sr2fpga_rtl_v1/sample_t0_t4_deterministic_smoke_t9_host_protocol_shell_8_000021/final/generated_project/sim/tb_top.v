`timescale 1ns/1ps

module tb_top;
  reg clk;
  reg rst_n;
  reg s_axi_awvalid;
  wire s_axi_awready;
  reg [3:0] s_axi_awaddr;
  reg s_axi_wvalid;
  wire s_axi_wready;
  reg [7:0] s_axi_wdata;
  reg s_axi_wstrb;
  wire s_axi_bvalid;
  reg s_axi_bready;
  reg s_axi_arvalid;
  wire s_axi_arready;
  reg [3:0] s_axi_araddr;
  wire s_axi_rvalid;
  reg s_axi_rready;
  wire [7:0] s_axi_rdata;
  wire m_axis_tvalid;
  reg m_axis_tready;
  wire [15:0] m_axis_tdata;
  wire m_axis_tlast;
  wire irq;
  integer wait_cycles;

  top dut (
    .clk(clk),
    .rst_n(rst_n),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),
    .s_axi_rdata(s_axi_rdata),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tready(m_axis_tready),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tlast(m_axis_tlast),
    .irq(irq)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task axi_write;
    input [3:0] addr_i;
    input [7:0] data_i;
    begin
      @(negedge clk);
      s_axi_awvalid = 1'b1;
      s_axi_awaddr = addr_i;
      s_axi_wvalid = 1'b1;
      s_axi_wdata = data_i;
      s_axi_wstrb = 1'b1;
      s_axi_bready = 1'b1;
      while (!s_axi_awready || !s_axi_wready) begin
        @(negedge clk);
      end
      @(negedge clk);
      s_axi_awvalid = 1'b0;
      s_axi_wvalid = 1'b0;
      while (!s_axi_bvalid) begin
        @(negedge clk);
      end
      @(negedge clk);
      s_axi_bready = 1'b0;
    end
  endtask

  task axi_read_expect;
    input [3:0] addr_i;
    input [7:0] mask_i;
    input [7:0] expected_i;
    begin
      @(negedge clk);
      s_axi_arvalid = 1'b1;
      s_axi_araddr = addr_i;
      s_axi_rready = 1'b1;
      while (!s_axi_arready) begin
        @(negedge clk);
      end
      @(negedge clk);
      s_axi_arvalid = 1'b0;
      wait_cycles = 0;
      while (!s_axi_rvalid && wait_cycles < 16) begin
        @(posedge clk);
        #1;
        wait_cycles = wait_cycles + 1;
      end
      if (!s_axi_rvalid) begin
        $display("TEST_FAIL read response did not become valid");
        $finish;
      end
      if ((s_axi_rdata & mask_i) !== expected_i) begin
        $display("TEST_FAIL expected read masked %0h got %0h", expected_i, s_axi_rdata & mask_i);
        $finish;
      end
      @(negedge clk);
      s_axi_rready = 1'b0;
    end
  endtask

  initial begin
    rst_n = 1'b0;
    s_axi_awvalid = 1'b0;
    s_axi_awaddr = 4'h0;
    s_axi_wvalid = 1'b0;
    s_axi_wdata = 8'h00;
    s_axi_wstrb = 1'b0;
    s_axi_bready = 1'b0;
    s_axi_arvalid = 1'b0;
    s_axi_araddr = 4'h0;
    s_axi_rready = 1'b0;
    m_axis_tready = 1'b1;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;

    axi_write(4'h4, 8'h12);
    axi_write(4'h8, 8'h34);
    axi_write(4'h0, 8'h01);

    wait_cycles = 0;
    while (!m_axis_tvalid && wait_cycles < 16) begin
      @(posedge clk);
      #1;
      wait_cycles = wait_cycles + 1;
    end
    if (!m_axis_tvalid || m_axis_tdata !== 16'h3412 || m_axis_tlast !== 1'b1) begin
      $display("TEST_FAIL expected stream payload 0x3412 got valid=%0d data=%0h last=%0d",
               m_axis_tvalid, m_axis_tdata, m_axis_tlast);
      $finish;
    end
    repeat (2) @(posedge clk);
    #1;
    if (irq !== 1'b1) begin
      $display("TEST_FAIL expected irq set");
      $finish;
    end

    axi_read_expect(4'hc, 8'h06, 8'h06);
    axi_write(4'h0, 8'h02);
    axi_read_expect(4'hc, 8'h04, 8'h00);

    $display("TEST_PASS");
    $finish;
  end
  initial begin
    #100000;
    $display("TEST_FAIL timeout waiting for expected input/output behavior");
    $finish;
  end

endmodule
