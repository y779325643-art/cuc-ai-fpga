module event_gate (
    input wire clk,
    input wire rst_n,
    input wire event_valid,
    output reg count_en
);
    reg event_valid_d;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            event_valid_d <= 1'b0;
            count_en <= 1'b0;
        end else begin
            event_valid_d <= event_valid;
            count_en <= event_valid & ~event_valid_d;
        end
    end
endmodule
