module stream_stage #(parameter DATA_WIDTH=8) (
    input wire clk,
    input wire rst_n,
    input wire s_valid,
    output reg s_ready,
    input wire [DATA_WIDTH-1:0] s_data,
    output reg m_valid,
    input wire m_ready,
    output reg [DATA_WIDTH-1:0] m_data
);

reg [DATA_WIDTH-1:0] pipe_data;
reg pipe_valid;

always @* begin
    s_ready = !pipe_valid || m_ready;
    m_valid = pipe_valid;
    m_data = pipe_data;
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pipe_data <= 0;
        pipe_valid <= 0;
    end else begin
        if (s_valid && s_ready) begin
            pipe_data <= s_data;
            pipe_valid <= 1;
        end else if (m_valid && m_ready) begin
            pipe_valid <= 0;
        end
    end
end

endmodule
