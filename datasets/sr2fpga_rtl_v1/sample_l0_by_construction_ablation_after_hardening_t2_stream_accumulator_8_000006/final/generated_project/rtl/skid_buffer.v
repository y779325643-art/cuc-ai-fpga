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
    reg stored_valid;
    reg [DATA_WIDTH-1:0] stored_data;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        stored_valid <= 0;
        stored_data  <= 0;
      end else begin
        if (out_ready) begin
          stored_valid <= 0;   // consumed
        end
        if (in_valid && (out_ready || !stored_valid)) begin
          stored_data  <= in_data;
          stored_valid <= 1;
        end
      end
    end

    assign in_ready  = out_ready || !stored_valid;
    assign out_valid = stored_valid;
    assign out_data  = stored_data;
endmodule
