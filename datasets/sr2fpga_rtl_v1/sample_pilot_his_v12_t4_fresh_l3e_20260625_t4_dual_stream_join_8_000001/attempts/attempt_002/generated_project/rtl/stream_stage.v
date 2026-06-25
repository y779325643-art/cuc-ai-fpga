module stream_stage #(
    parameter DATA_WIDTH = 8
) (
    input  wire                 clk,
    input  wire                 reset_n,
    input  wire                 in_valid,
    output reg                  in_ready,
    input  wire [DATA_WIDTH-1:0] in_data,
    output reg                  out_valid,
    input  wire                 out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

    reg [DATA_WIDTH-1:0] pipe_data;
    reg                  pipe_valid;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            in_ready <= 1'b0;
            out_valid <= 1'b0;
            out_data <= {DATA_WIDTH{1'b0}};
            pipe_valid <= 1'b0;
        end else begin
            in_ready <= !pipe_valid || (out_ready && pipe_valid);
            if (in_valid && in_ready) begin
                pipe_data <= in_data;
                pipe_valid <= 1'b1;
            end
            if (out_ready && pipe_valid) begin
                out_valid <= 1'b1;
                out_data <= pipe_data;
                pipe_valid <= 1'b0;
            end else if (pipe_valid) begin
                out_valid <= 1'b1;
                out_data <= pipe_data;
            end else begin
                out_valid <= 1'b0;
            end
        end
    end

endmodule
