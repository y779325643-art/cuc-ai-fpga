`timescale 1ns / 1ps

module stream_stage #(parameter WIDTH = 8) (
    input  wire clk,
    input  wire rst_n,
    input  wire [WIDTH-1:0] data_in,
    input  wire valid_in,
    output wire ready_out,
    output wire [WIDTH-1:0] data_out,
    output wire valid_out,
    input  wire ready_in
);

    reg [WIDTH-1:0] pipeline_reg;
    reg valid_reg;

    assign ready_out = !valid_reg || ready_in;
    assign data_out = pipeline_reg;
    assign valid_out = valid_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipeline_reg <= {WIDTH{1'b0}};
            valid_reg <= 1'b0;
        end else begin
            if (valid_reg) begin
                if (ready_in) begin
                    valid_reg <= 1'b0;
                end
            end
            if (valid_in && ready_out) begin
                pipeline_reg <= data_in;
                valid_reg <= 1'b1;
            end
        end
    end

endmodule
