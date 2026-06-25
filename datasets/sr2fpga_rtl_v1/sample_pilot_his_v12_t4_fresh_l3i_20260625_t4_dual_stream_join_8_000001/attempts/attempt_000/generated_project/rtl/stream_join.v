module stream_join #(parameter DATA_WIDTH=8) (
    input wire clk,
    input wire rst_n,
    input wire s0_valid,
    output reg s0_ready,
    input wire [DATA_WIDTH-1:0] s0_data,
    input wire s1_valid,
    output reg s1_ready,
    input wire [DATA_WIDTH-1:0] s1_data,
    output reg m_valid,
    input wire m_ready,
    output reg [DATA_WIDTH-1:0] m_data
);

localparam IDLE = 2'd0;
localparam SEND_0 = 2'd1;
localparam SEND_1 = 2'd2;

reg [1:0] state, next_state;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
    end else begin
        state <= next_state;
    end
end

always @* begin
    next_state = state;
    s0_ready = 0;
    s1_ready = 0;
    m_valid = 0;
    m_data = 0;
    
    case (state)
        IDLE: begin
            if (s0_valid && m_ready) begin
                next_state = SEND_0;
                s0_ready = 1;
                m_valid = 1;
                m_data = s0_data;
            end else if (s1_valid && m_ready) begin
                next_state = SEND_1;
                s1_ready = 1;
                m_valid = 1;
                m_data = s1_data;
            end
        end
        SEND_0: begin
            s0_ready = 1;
            m_valid = s0_valid;
            m_data = s0_data;
            if (s0_valid && m_ready) begin
                next_state = IDLE;
            end else if (!s0_valid) begin
                next_state = IDLE;
            end
        end
        SEND_1: begin
            s1_ready = 1;
            m_valid = s1_valid;
            m_data = s1_data;
            if (s1_valid && m_ready) begin
                next_state = IDLE;
            end else if (!s1_valid) begin
                next_state = IDLE;
            end
        end
        default: begin
            next_state = IDLE;
        end
    endcase
end

endmodule
