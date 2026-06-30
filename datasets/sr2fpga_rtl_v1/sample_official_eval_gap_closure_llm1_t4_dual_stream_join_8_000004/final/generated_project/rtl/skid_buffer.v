module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    input wire out_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg                  skid_valid;
    reg [DATA_WIDTH-1:0] skid_data;

    assign out_valid = in_valid || skid_valid;
    assign out_data  = skid_valid ? skid_data : in_data;
    assign in_ready  = !skid_valid || out_ready;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        skid_valid <= 1'b0;
        skid_data  <= {DATA_WIDTH{1'b0}};
      end else begin
        if (out_ready) begin
          if (in_valid && skid_valid) begin
            skid_data <= in_data;
            // skid_valid remains 1
          end else if (skid_valid) begin
            skid_valid <= 1'b0;
          end else if (in_valid) begin
            // pass through, nothing to store
          end
        end else begin // out_ready is low
          if (in_valid) begin
            skid_valid <= 1'b1;
            skid_data <= in_data;
          end
        end
      end
    end
endmodule
