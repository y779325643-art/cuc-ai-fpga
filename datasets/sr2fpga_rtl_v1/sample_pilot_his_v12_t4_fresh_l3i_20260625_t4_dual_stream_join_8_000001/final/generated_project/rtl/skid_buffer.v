module skid_buffer #(parameter DATA_WIDTH=8) (
    input wire clk,
    input wire rst_n,
    input wire s_valid,
    output reg s_ready,
    input wire [DATA_WIDTH-1:0] s_data,
    output reg m_valid,
    input wire m_ready,
    output reg [DATA_WIDTH-1:0] m_data
);

reg [DATA_WIDTH-1:0] data_reg;
reg valid_reg;

// Combinatorial outputs
always @* begin
    s_ready = !valid_reg || m_ready;
    m_valid = valid_reg;
    m_data = data_reg;
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_reg <= 0;
        valid_reg <= 0;
    end else begin
        if (s_valid && s_ready) begin
            data_reg <= s_data;
            valid_reg <= 1;
        end else if (m_valid && m_ready) begin
            valid_reg <= 0;
        end
    end
end

endmodule
