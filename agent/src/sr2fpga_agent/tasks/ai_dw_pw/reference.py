"""Hand-authored RTL control implementation, separate from evaluator oracle.

These fixed-profile behavior bodies are engineering controls. The generic PC
emitter must never insert them or infer their arithmetic from intent text.
"""

from .task import DW_WEIGHTS, DW_BIAS, PW_WEIGHTS, PW_BIAS, OUTPUT_DENOMINATORS, OUTPUT_ZEROS


def _lookup(name: str, values: tuple | list) -> str:
    return (f"function integer {name}(input integer index);\nbegin\ncase(index)\n" +
            "\n".join(f"{i}: {name} = {v};" for i, v in enumerate(values)) +
            f"\ndefault: {name} = 0;\nendcase\nend\nendfunction\n")


ROUND = """
function integer round_even(input integer value, input integer divisor);
integer magnitude, quotient, remainder;
begin
  magnitude = value < 0 ? -value : value;
  // This fixed public profile uses only divisors 2,4,8. Explicit constant
  // branches avoid inferring a generic signed division/remainder datapath.
  case(divisor)
    2: begin quotient = magnitude >> 1; remainder = magnitude & 1; end
    4: begin quotient = magnitude >> 2; remainder = magnitude & 3; end
    8: begin quotient = magnitude >> 3; remainder = magnitude & 7; end
    default: begin quotient = 0; remainder = 0; end
  endcase
  if ((2*remainder > divisor) || ((2*remainder == divisor) && quotient[0]))
    quotient = quotient + 1;
  round_even = value < 0 ? -quotient : quotient;
end
endfunction
function integer clamp8(input integer value);
begin
  if(value < -128) clamp8 = -128;
  else if(value > 127) clamp8 = 127;
  else clamp8 = value;
end
endfunction
"""


def reference_behavior_bodies() -> dict[str, str]:
    """Internal pin convention is the generic emitter's declared interface."""
    dw = _lookup("weight", tuple(v for kernel in DW_WEIGHTS for row in kernel for v in row))
    dw += _lookup("bias", DW_BIAS) + ROUND + """
reg signed [7:0] image [0:59];
reg signed [7:0] intermediate [0:59];
reg [1:0] state, channel, row;
reg [2:0] col;
reg [1:0] kernel_row, kernel_col;
reg [5:0] received, calculated, sent;
integer ih, iw;
reg signed [8:0] sample_value;
// Public-input/weight range analysis bounds |DW acc| <=1446, |PW acc| <=759.
// Sixteen bits preserve every mathematical partial/final sum without overflow.
reg signed [15:0] accumulator, next_accumulator, quantized;
assign p_rx_ready = (state == 0);
assign p_tx_valid = (state == 2);
always @* begin
  p_tx_payload = 18'd0;
  if(state == 2) begin
    if(!sent[0]) p_tx_payload = {2'b11, intermediate[(sent>>1)*3+1], intermediate[(sent>>1)*3]};
    else p_tx_payload = {2'b01, 8'd0, intermediate[(sent>>1)*3+2]};
  end
end
always @(posedge d_d_clock) begin
  if(!d_d_reset) begin
    state <= 0; received <= 0; calculated <= 0; sent <= 0;
    channel <= 0; row <= 0; col <= 0;
    kernel_row <= 0; kernel_col <= 0; accumulator <= 0;
  end else begin
    case(state)
      0: if(p_rx_valid && p_rx_ready) begin
        if(!received[0]) begin
          image[(received>>1)*3] <= $signed(p_rx_payload[7:0]);
          image[(received>>1)*3+1] <= $signed(p_rx_payload[15:8]);
        end else image[(received>>1)*3+2] <= $signed(p_rx_payload[7:0]);
        if(received == 39) begin
          state <= 1; calculated <= 0; received <= 0;
          channel <= 0; row <= 0; col <= 0;
          kernel_row <= 0; kernel_col <= 0; accumulator <= bias(0);
        end
        else received <= received+1;
      end
      1: begin
        // One shared image read and kernel MAC per clock. No unrolled bank
        // of nine dynamic frame-memory read ports is required by the task.
        ih = row+kernel_row-1; iw = col+kernel_col-1;
        if(ih < 0 || ih >= 4 || iw < 0 || iw >= 5) sample_value = -3;
        else sample_value = $signed(image[(ih*5+iw)*3+channel]);
        next_accumulator = accumulator + (sample_value+3)*weight(channel*9+kernel_row*3+kernel_col);
        if(kernel_row == 2 && kernel_col == 2) begin
          quantized = clamp8(round_even(next_accumulator,2)+2);
          if(quantized < 2) quantized = 2;
          intermediate[calculated] <= quantized;
          kernel_row <= 0; kernel_col <= 0;
          if(calculated == 59) begin state <= 2; sent <= 0; end
          else begin
            calculated <= calculated+1;
            if(channel == 2) begin
              channel <= 0; accumulator <= bias(0);
              if(col == 4) begin col <= 0; row <= row+1; end
              else col <= col+1;
            end else begin channel <= channel+1; accumulator <= bias(channel+1); end
          end
        end else begin
          accumulator <= next_accumulator;
          if(kernel_col == 2) begin kernel_col <= 0; kernel_row <= kernel_row+1; end
          else kernel_col <= kernel_col+1;
        end
      end
      2: if(p_tx_ready) begin
        if(sent == 39) begin state <= 0; sent <= 0; end
        else sent <= sent+1;
      end
      default: begin
        state <= 0; received <= 0; calculated <= 0; sent <= 0;
        channel <= 0; row <= 0; col <= 0;
        kernel_row <= 0; kernel_col <= 0; accumulator <= 0;
      end
    endcase
  end
end
"""
    pw = _lookup("weight", tuple(v for row in PW_WEIGHTS for v in row))
    pw += _lookup("bias", PW_BIAS) + _lookup("divisor", OUTPUT_DENOMINATORS)
    pw += _lookup("zero_point", OUTPUT_ZEROS) + ROUND + """
reg signed [7:0] inputs [0:2];
reg signed [7:0] outputs [0:4];
reg [1:0] state, sent;
reg received;
integer o, c;
reg signed [15:0] accumulator;
assign p_rx_ready = (state == 0);
assign p_tx_valid = (state == 2);
always @* begin
  p_tx_payload = 18'd0;
  if(state == 2) begin
    if(sent == 0) p_tx_payload = {2'b11, outputs[1], outputs[0]};
    else if(sent == 1) p_tx_payload = {2'b11, outputs[3], outputs[2]};
    else p_tx_payload = {2'b01, 8'd0, outputs[4]};
  end
end
always @(posedge d_d_clock) begin
  if(!d_d_reset) begin state <= 0; received <= 0; sent <= 0; end
  else begin
    case(state)
      0: if(p_rx_valid && p_rx_ready) begin
        if(received == 0) begin
          inputs[0] <= $signed(p_rx_payload[7:0]);
          inputs[1] <= $signed(p_rx_payload[15:8]); received <= 1;
        end else begin inputs[2] <= $signed(p_rx_payload[7:0]); received <= 0; state <= 1; end
      end
      1: begin
        for(o=0;o<5;o=o+1) begin
          accumulator = bias(o);
          for(c=0;c<3;c=c+1) accumulator = accumulator + ($signed(inputs[c])-2)*weight(o*3+c);
          outputs[o] <= clamp8(round_even(accumulator,divisor(o))+zero_point(o));
        end
        state <= 2; sent <= 0;
      end
      2: if(p_tx_ready) begin
        if(sent == 2) begin state <= 0; sent <= 0; end
        else sent <= sent+1;
      end
      default: begin state <= 0; received <= 0; sent <= 0; end
    endcase
  end
end
"""
    return {"DepthwiseStage": dw, "PointwiseStage": pw}


def render_reference_project() -> dict[str, str]:
    """Explicit engineering control wrapper, independent of generic PC emission."""
    files = {}
    for name, body in reference_behavior_bodies().items():
        files[f"{name}.sv"] = (f"module {name}(input wire d_d_clock,input wire d_d_reset,"
            "input wire [17:0] p_rx_payload,input wire p_rx_valid,output wire p_rx_ready,"
            "output reg [17:0] p_tx_payload,output wire p_tx_valid,input wire p_tx_ready);\n" + body + "\nendmodule\n")
    files["AiDwPwDev.sv"] = """module AiDwPwDev(input wire clk,input wire rst_n,
input wire [17:0] in_payload,input wire in_valid,output wire in_ready,
output wire [17:0] out_payload,output wire out_valid,input wire out_ready);
wire [17:0] intermediate; wire mid_valid,mid_ready;
DepthwiseStage dw(.d_d_clock(clk),.d_d_reset(rst_n),.p_rx_payload(in_payload),
.p_rx_valid(in_valid),.p_rx_ready(in_ready),.p_tx_payload(intermediate),
.p_tx_valid(mid_valid),.p_tx_ready(mid_ready));
PointwiseStage pw(.d_d_clock(clk),.d_d_reset(rst_n),.p_rx_payload(intermediate),
.p_rx_valid(mid_valid),.p_rx_ready(mid_ready),.p_tx_payload(out_payload),
.p_tx_valid(out_valid),.p_tx_ready(out_ready));
endmodule
"""
    return files
