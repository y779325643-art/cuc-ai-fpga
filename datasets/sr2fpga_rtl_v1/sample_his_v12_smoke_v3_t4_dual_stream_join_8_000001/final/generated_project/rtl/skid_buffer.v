module skid_buffer #(parameter WIDTH=8) (
    input clk, rst_n,
    input [WIDTH-1:0] s_tdata,
    input s_tvalid,
    output s_tready,
    output [WIDTH-1:0] m_tdata,
    output m_tvalid,
    input m_tready
);
localparam DEPTH = 4;
reg [WIDTH-1:0] mem [0:DEPTH-1];
reg [1:0] wr_ptr, rd_ptr;
reg [2:0] count;

assign s_tready = (count < DEPTH);
assign m_tvalid = (count > 0);
assign m_tdata = mem[rd_ptr];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        wr_ptr <= 0;
        rd_ptr <= 0;
        count <= 0;
    end else begin
        if (s_tvalid && s_tready && m_tready && m_tvalid) begin
            // both write and read
            mem[wr_ptr] <= s_tdata;
            wr_ptr <= wr_ptr + 1;
            rd_ptr <= rd_ptr + 1;
            // count unchanged
        end else if (s_tvalid && s_tready) begin
            // write only
            mem[wr_ptr] <= s_tdata;
            wr_ptr <= wr_ptr + 1;
            count <= count + 1;
        end else if (m_tready && m_tvalid) begin
            // read only
            rd_ptr <= rd_ptr + 1;
            count <= count - 1;
        end
    end
end
endmodule
