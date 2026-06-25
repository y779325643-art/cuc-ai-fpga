module stream_join #(parameter W=8) (
    input clk, rst_n,
    input in0_valid, input [W-1:0] in0_data,
    output reg in0_ready,
    input in1_valid, input [W-1:0] in1_data,
    output reg in1_ready,
    output reg out_valid, output reg [W-1:0] out_data,
    input out_ready
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_valid <= 0;
            in0_ready <= 1;
            in1_ready <= 1;
        end else begin
            if (!out_valid || out_ready) begin
                if (in0_valid && in1_valid) begin
                    out_valid <= 1;
                    out_data <= in0_data + in1_data;
                    in0_ready <= 1;
                    in1_ready <= 1;
                end else begin
                    out_valid <= 0;
                    in0_ready <= 1;
                    in1_ready <= 1;
                end
            end else begin
                in0_ready <= 0;
                in1_ready <= 0;
            end
        end
    end
endmodule
