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
    reg  [DATA_WIDTH-1:0] main_data;
    reg  [DATA_WIDTH-1:0] skid_data;
    reg  main_valid;
    reg  skid_valid;

    assign out_data = main_data;
    assign out_valid = main_valid;
    assign in_ready = !skid_valid;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        main_valid <= 1'b0;
        skid_valid <= 1'b0;
        main_data <= {DATA_WIDTH{1'b0}};
        skid_data <= {DATA_WIDTH{1'b0}};
      end else begin
        if (out_ready && main_valid) begin
          if (skid_valid) begin
            main_data <= skid_data;
            skid_valid <= 1'b0;
          end else begin
            main_valid <= 1'b0;
          end
        end
        if (in_valid && in_ready) begin
          if (!main_valid) begin
            main_data <= in_data;
            main_valid <= 1'b1;
          end else begin
            skid_data <= in_data;
            skid_valid <= 1'b1;
          end
        end
      end
    end
endmodule
