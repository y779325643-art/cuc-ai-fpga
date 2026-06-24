module stream_stage #(parameter WIDTH=8) (
    input clk, rst_n,
    input [WIDTH-1:0] s_tdata,
    input s_tvalid,
    output s_tready,
    output reg [WIDTH-1:0] m_tdata,
    output reg m_tvalid,
    input m_tready
);
assign s_tready = !m_tvalid | (m_tready & m_tvalid);
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        m_tvalid <= 1'b0;
    end else begin
        if (s_tvalid & s_tready) begin
            m_tdata <= s_tdata;
            m_tvalid <= 1'b1;
        end else if (m_tready & m_tvalid) begin
            m_tvalid <= 1'b0;
        end
    end
end
endmodule
