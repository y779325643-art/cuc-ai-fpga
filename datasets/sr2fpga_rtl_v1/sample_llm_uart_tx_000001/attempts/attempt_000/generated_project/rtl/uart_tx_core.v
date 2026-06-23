module uart_tx_core (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [7:0] data,
    input wire baud_tick,
    output reg tx,
    output reg busy
);
    localparam IDLE = 0,
               START = 1,
               DATA = 2,
               STOP = 3;
    reg [1:0] state, next_state;
    reg [3:0] bit_index;
    reg [7:0] shift_reg;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            tx <= 1;
            busy <= 0;
            bit_index <= 0;
            shift_reg <= 0;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    tx <= 1;
                    busy <= 0;
                    if (start) begin
                        shift_reg <= data;
                        bit_index <= 0;
                    end
                end
                START: begin
                    tx <= 0;
                    busy <= 1;
                end
                DATA: begin
                    tx <= shift_reg[0];
                    shift_reg <= {1'b0, shift_reg[7:1]}; // LSB first
                    busy <= 1;
                end
                STOP: begin
                    tx <= 1;
                    busy <= 1;
                end
            endcase
        end
    end
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: if (start) next_state = START;
            START: if (baud_tick) next_state = DATA;
            DATA: if (baud_tick) begin
                if (bit_index == 7) begin
                    next_state = STOP;
                end else begin
                    bit_index = bit_index + 1;
                end
            end
            STOP: if (baud_tick) next_state = IDLE;
        endcase
    end
endmodule
