module host_config_bank #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire cfg_valid,
    output wire cfg_ready,
    input wire [2:0] cfg_addr,
    input wire [DATA_WIDTH-1:0] cfg_data,
    output reg [DATA_WIDTH-1:0] weight0,
    output reg [DATA_WIDTH-1:0] bias0,
    output reg [DATA_WIDTH-1:0] weight1,
    output reg [DATA_WIDTH-1:0] bias1,
    output reg [DATA_WIDTH-1:0] alpha,
    output reg enable
);

  assign cfg_ready = 1'b1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      weight0 <= {DATA_WIDTH{1'b0}};
      bias0 <= {DATA_WIDTH{1'b0}};
      weight1 <= {DATA_WIDTH{1'b0}};
      bias1 <= {DATA_WIDTH{1'b0}};
      alpha <= {DATA_WIDTH{1'b0}};
      enable <= 1'b0;
    end else if (cfg_valid && cfg_ready) begin
      case (cfg_addr)
        3'd0: bias0 <= cfg_data;
        3'd1: bias0 <= cfg_data;
        3'd2: weight1 <= cfg_data;
        3'd3: bias1 <= cfg_data;
        3'd4: alpha <= cfg_data;
        3'd5: enable <= cfg_data[0];
        default: enable <= enable;
      endcase
    end
  end

endmodule
