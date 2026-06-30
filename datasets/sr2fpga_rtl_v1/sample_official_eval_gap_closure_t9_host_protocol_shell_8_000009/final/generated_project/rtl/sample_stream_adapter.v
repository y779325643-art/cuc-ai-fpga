module sample_stream_adapter #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [DATA_WIDTH-1:0] sample0,
    input wire [DATA_WIDTH-1:0] sample1,
    output reg tvalid,
    input wire tready,
    output reg [(2*DATA_WIDTH)-1:0] tdata,
    output reg tlast,
    output reg stream_done
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tvalid <= 1'b0;
      tdata <= {(2*DATA_WIDTH){1'b0}};
      tlast <= 1'b0;
      stream_done <= 1'b0;
    end else begin
      stream_done <= 1'b0;
      if (start && !tvalid) begin
        tvalid <= 1'b1;
        tdata <= {sample1, sample0};
        tlast <= 1'b1;
      end else if (tvalid && tready) begin
        tvalid <= 1'b0;
        tlast <= 1'b0;
        stream_done <= 1'b1;
      end
    end
  end

endmodule
