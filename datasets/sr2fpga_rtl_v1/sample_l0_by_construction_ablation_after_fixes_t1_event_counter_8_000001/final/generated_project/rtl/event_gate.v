module event_gate (
    input clk,
    input reset_n,
    input event_valid,
    output reg count_en
);
always @(posedge clk or negedge reset_n) begin
    if (!reset_n) count_en <= 1'b0;
    else count_en <= event_valid;
end
endmodule
