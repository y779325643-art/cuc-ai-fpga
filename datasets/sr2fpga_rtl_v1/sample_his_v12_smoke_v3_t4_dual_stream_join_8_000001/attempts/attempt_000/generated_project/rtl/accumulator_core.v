module accumulator_core #(parameter WIDTH=8) (
    input clk, rst_n,
    input [WIDTH-1:0] s_tdata,
    input s_tvalid,
    output s_tready,
    output [WIDTH-1:0] m_tdata,
    output m_tvalid,
    input m_tready
);
reg [WIDTH-1:0] accum_val;
assign s_tready = 1'b1;
assign m_tdata = accum_val;
assign m_tvalid = 1'b1;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        accum_val <= 0;
    end else if (s_tvalid) begin
        accum_val <= accum_val + s_tdata;
    end
end
endmodule
