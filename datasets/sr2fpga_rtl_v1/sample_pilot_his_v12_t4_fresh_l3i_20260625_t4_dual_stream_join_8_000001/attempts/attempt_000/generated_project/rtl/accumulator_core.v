module accumulator_core #(parameter DATA_WIDTH=8) (
    input wire clk,
    input wire rst_n,
    input wire s_valid,
    output reg s_ready,
    input wire [DATA_WIDTH-1:0] s_data,
    output reg m_valid,
    input wire m_ready,
    output reg [DATA_WIDTH-1:0] m_data
);

reg [DATA_WIDTH-1:0] acc_reg;
reg acc_valid; // internal valid register not in contract but required

always @* begin
    s_ready = !acc_valid || m_ready;
    m_valid = acc_valid;
    m_data = acc_reg;
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        acc_reg <= 0;
        acc_valid <= 0;
    end else begin
        if (s_valid && s_ready) begin
            acc_reg <= acc_reg + s_data;
            acc_valid <= 1;
        end else if (m_valid && m_ready) begin
            acc_valid <= 0;
        end
    end
end

endmodule
