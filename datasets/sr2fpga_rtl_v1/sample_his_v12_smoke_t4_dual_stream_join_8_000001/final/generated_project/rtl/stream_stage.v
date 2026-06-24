module stream_stage #(
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

reg [DATA_WIDTH-1:0] stage_data;
reg stage_valid;

assign ready_out = ~stage_valid || (valid_out && ready_in);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        stage_data <= {DATA_WIDTH{1'b0}};
        stage_valid <= 1'b0;
        data_out <= {DATA_WIDTH{1'b0}};
        valid_out <= 1'b0;
    end else begin
        // Load stage
        if (valid_in && ready_out) begin
            stage_data <= data_in;
            stage_valid <= 1'b1;
        end
        // Output handshake
        if (ready_in) begin
            if (stage_valid) begin
                data_out <= stage_data;
                valid_out <= 1'b1;
                stage_valid <= 1'b0;
            end else begin
                valid_out <= 1'b0;
            end
        end else begin
            // hold
        end
    end
end

endmodule
