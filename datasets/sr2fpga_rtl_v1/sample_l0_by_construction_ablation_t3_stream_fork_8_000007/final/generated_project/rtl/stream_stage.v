module stream_stage (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
    reg out_valid_r;
    reg [DATA_WIDTH-1:0] out_data_r;

    assign out_valid = out_valid_r;
    assign out_data = out_data_r;
    assign in_ready = !out_valid_r || out_ready;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_r <= 1'b0;
      end else begin
        if (in_ready) begin
          out_valid_r <= in_valid;
          out_data_r  <= in_data;
        end
      end
    end
endmodule
