module skid_buffer #(
    parameter WIDTH = 8,
    parameter DEPTH = 2
) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] in_data,
    input  wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input  wire out_ready
);

    reg [WIDTH-1:0] buf [0:DEPTH-1];
    reg [$clog2(DEPTH+1)-1:0] count;

    wire push = in_valid & in_ready;
    wire pop = out_valid & out_ready;

    assign in_ready = (count < DEPTH);
    assign out_valid = (count > 0);
    assign out_data = buf[0];

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
            for (i = 0; i < DEPTH; i = i + 1) buf[i] <= 0;
        end else begin
            if (push && !pop) begin
                buf[count] <= in_data;
                count <= count + 1;
            end else if (!push && pop) begin
                for (i = 0; i < DEPTH-1; i = i + 1) buf[i] <= buf[i+1];
                buf[DEPTH-1] <= 0;
                count <= count - 1;
            end else if (push && pop) begin
                for (i = 0; i < DEPTH-1; i = i + 1) buf[i] <= buf[i+1];
                buf[DEPTH-1] <= in_data;
                count <= count;
            end
        end
    end

endmodule
