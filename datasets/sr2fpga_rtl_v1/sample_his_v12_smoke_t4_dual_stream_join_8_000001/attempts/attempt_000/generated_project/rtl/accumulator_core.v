module accumulator_core #(
    parameter DATA_WIDTH = 8
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire [DATA_WIDTH-1:0] data_in,
    input  wire                  valid_in,
    output wire                  ready_out,
    output reg  [DATA_WIDTH-1:0] data_out,
    output reg                   valid_out,
    input  wire                  ready_in
);

reg [DATA_WIDTH-1:0] accum;
reg accum_valid;

assign ready_out = ~accum_valid || (valid_out && ready_in);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        accum <= {DATA_WIDTH{1'b0}};
        accum_valid <= 1'b0;
        data_out <= {DATA_WIDTH{1'b0}};
        valid_out <= 1'b0;
    end else begin
        // Input stage
        if (valid_in && ready_out) begin
            if (~accum_valid) begin
                accum <= data_in;
                accum_valid <= 1'b1;
            end else begin
                accum <= accum + data_in;
            end
        end
        // Output stage
        if (ready_in) begin
            if (accum_valid) begin
                data_out <= accum;
                valid_out <= 1'b1;
                accum_valid <= 1'b0;
                accum <= {DATA_WIDTH{1'b0}};
            end else begin
                valid_out <= 1'b0;
            end
        end else begin
            // hold output
        end
    end
end

endmodule
