"""Hand-authored stateful RTL control; the generic emitter never inserts it."""

from .task import EXP_LUT


def reference_behavior_bodies() -> dict[str, str]:
    lookup = ("function [8:0] exp_weight(input [4:0] delta);\nbegin\ncase(delta)\n" +
              "\n".join(f"{index}: exp_weight = {value};" for index, value in enumerate(EXP_LUT)) +
              "\ndefault: exp_weight = 0;\nendcase\nend\nendfunction\n")
    body = lookup + """
// INT8/D3 bounds: |dot| <=49152 and |37*dot| <=1818624.
// Power-of-two score scaling never infers a variable divider.
function signed [4:0] score_quant(input signed [21:0] value);
reg [21:0] magnitude;
reg [11:0] quotient;
reg [9:0] remainder;
reg signed [12:0] signed_result;
begin
 magnitude = value[21] ? -value : value;
 quotient = magnitude[21:10];
 remainder = magnitude[9:0];
 if(remainder > 10'd512 || (remainder == 10'd512 && quotient[0])) quotient = quotient+1'b1;
 signed_result = value[21] ? -$signed({1'b0,quotient}) : $signed({1'b0,quotient});
 if(signed_result < -13'sd8) score_quant = -5'sd8;
 else if(signed_result > 13'sd8) score_quant = 5'sd8;
 else score_quant = signed_result[4:0];
end
endfunction
// At most4 weights of at most256: denominator<=1024 and AV is in
// [-131072,130048]. Magnitude is UNSIGNED18, preserving abs(-131072).
// This single bounded divider is shared across every head/channel.
function signed [7:0] ratio_round(input signed [17:0] value, input [10:0] divisor);
reg [17:0] magnitude, quotient;
reg [10:0] remainder;
reg [11:0] twice_remainder;
reg signed [18:0] signed_result;
begin
 magnitude = value[17] ? -value : value;
 quotient = magnitude / divisor;
 remainder = magnitude % divisor;
 twice_remainder = {1'b0,remainder} << 1;
 if(twice_remainder > {1'b0,divisor} ||
    (twice_remainder == {1'b0,divisor} && quotient[0])) quotient = quotient+1'b1;
 signed_result = value[17] ? -$signed({1'b0,quotient}) : $signed({1'b0,quotient});
 if(signed_result < -19'sd128) ratio_round = -8'sd128;
 else if(signed_result > 19'sd127) ratio_round = 8'sd127;
 else ratio_round = signed_result[7:0];
end
endfunction
reg signed [7:0] query_buffer [0:11];
reg signed [7:0] key_buffer [0:5];
reg signed [7:0] value_buffer [0:5];
reg signed [7:0] key_cache [0:23];
reg signed [7:0] value_cache [0:23];
reg signed [7:0] results [0:11];
reg [2:0] valid_length, k_count, v_count, sent;
reg [3:0] q_count;
reg [2:0] state;
reg [1:0] head_index, token_index, channel_index;
reg signed [16:0] dot_accumulator;
reg signed [17:0] av_accumulator;
reg signed [4:0] max_score;
reg [10:0] denominator;
reg signed [4:0] score [0:3];
reg [8:0] weight [0:3];
integer d;
wire signed [15:0] qk_product = $signed(query_buffer[head_index*3+channel_index]) *
                               $signed(key_cache[token_index*6+(head_index>>1)*3+channel_index]);
wire signed [16:0] dot_next = dot_accumulator + {qk_product[15],qk_product};
wire signed [21:0] dot_wide = {{5{dot_next[16]}},dot_next};
wire signed [21:0] scaled_dot = (dot_wide << 5) + (dot_wide << 2) + dot_wide;
wire signed [4:0] next_score = score_quant(scaled_dot);
wire [4:0] delta = max_score-score[token_index];
wire [8:0] current_weight = exp_weight(delta);
wire signed [17:0] av_product = $signed({1'b0,weight[token_index]}) *
                               $signed(value_cache[token_index*6+(head_index>>1)*3+channel_index]);
wire signed [17:0] av_next = av_accumulator+av_product;
assign p_q_ready = state == 0 && q_count < 8 && valid_length < 4;
assign p_k_ready = state == 0 && k_count < 4 && valid_length < 4;
assign p_v_ready = state == 0 && v_count < 4 && valid_length < 4;
assign p_context_valid = state == 6;
always @* begin
 p_context_payload = 18'd0;
 if(state == 6) begin
  if(!sent[0]) p_context_payload = {2'b11,results[(sent>>1)*3+1],results[(sent>>1)*3]};
  else p_context_payload = {2'b01,8'd0,results[(sent>>1)*3+2]};
 end
end
always @(posedge d_d_clock) begin
 if(!d_d_reset) begin
  valid_length <= 0; q_count <= 0; k_count <= 0; v_count <= 0; state <= 0; sent <= 0;
  head_index <= 0; token_index <= 0; channel_index <= 0;
  dot_accumulator <= 0; av_accumulator <= 0; denominator <= 0; max_score <= -5'sd8;
 end else begin
  case(state)
   0: begin
    if(p_q_valid && p_q_ready) begin
     if(!q_count[0]) begin
      query_buffer[(q_count>>1)*3] <= $signed(p_q_payload[7:0]);
      query_buffer[(q_count>>1)*3+1] <= $signed(p_q_payload[15:8]);
     end else query_buffer[(q_count>>1)*3+2] <= $signed(p_q_payload[7:0]);
     q_count <= q_count+1;
    end
    if(p_k_valid && p_k_ready) begin
     if(!k_count[0]) begin
      key_buffer[(k_count>>1)*3] <= $signed(p_k_payload[7:0]);
      key_buffer[(k_count>>1)*3+1] <= $signed(p_k_payload[15:8]);
     end else key_buffer[(k_count>>1)*3+2] <= $signed(p_k_payload[7:0]);
     k_count <= k_count+1;
    end
    if(p_v_valid && p_v_ready) begin
     if(!v_count[0]) begin
      value_buffer[(v_count>>1)*3] <= $signed(p_v_payload[7:0]);
      value_buffer[(v_count>>1)*3+1] <= $signed(p_v_payload[15:8]);
     end else value_buffer[(v_count>>1)*3+2] <= $signed(p_v_payload[7:0]);
     v_count <= v_count+1;
    end
    if(q_count == 8 && k_count == 4 && v_count == 4) state <= 1;
   end
   1: begin
    for(d=0;d<6;d=d+1) begin
     key_cache[valid_length*6+d] <= key_buffer[d];
     value_cache[valid_length*6+d] <= value_buffer[d];
    end
    valid_length <= valid_length+1;
    head_index <= 0; token_index <= 0; channel_index <= 0; dot_accumulator <= 0; max_score <= -5'sd8;
    state <= 2;
   end
   2: begin
    if(channel_index == 2) begin
     score[token_index] <= next_score;
     if(next_score > max_score) max_score <= next_score;
     channel_index <= 0; dot_accumulator <= 0;
     if({1'b0,token_index}+3'd1 == valid_length) begin
      token_index <= 0; denominator <= 0; state <= 3;
     end else token_index <= token_index+1'b1;
    end else begin
     dot_accumulator <= dot_next;
     channel_index <= channel_index+1'b1;
    end
   end
   3: begin
    weight[token_index] <= current_weight;
    denominator <= denominator+{2'b0,current_weight};
    if({1'b0,token_index}+3'd1 == valid_length) begin
     token_index <= 0; channel_index <= 0; av_accumulator <= 0; state <= 4;
    end else token_index <= token_index+1'b1;
   end
   4: begin
    av_accumulator <= av_next;
    if({1'b0,token_index}+3'd1 == valid_length) begin
     token_index <= 0; state <= 5;
    end else token_index <= token_index+1'b1;
   end
   5: begin
    results[head_index*3+channel_index] <= ratio_round(av_accumulator,denominator);
    av_accumulator <= 0; token_index <= 0;
    if(channel_index == 2) begin
     channel_index <= 0;
     if(head_index == 3) begin sent <= 0; state <= 6; end
     else begin head_index <= head_index+1'b1; dot_accumulator <= 0; max_score <= -5'sd8; state <= 2; end
    end else begin channel_index <= channel_index+1'b1; state <= 4; end
   end
   6: if(p_context_ready) begin
    if(sent == 7) begin q_count <= 0; k_count <= 0; v_count <= 0; sent <= 0; state <= 0; end
    else sent <= sent+1;
   end
   default: begin valid_length <= 0; q_count <= 0; k_count <= 0; v_count <= 0; sent <= 0; state <= 0; end
  endcase
 end
end
"""
    return {"CachedDecodeAttention": body}


def render_reference_project() -> dict[str, str]:
    """Explicit wrapper, independent of PC construction, using the same public ABI."""
    ports = ["input wire d_d_clock", "input wire d_d_reset"]
    for name in ("q", "k", "v"):
        ports.extend((f"input wire [17:0] p_{name}_payload", f"input wire p_{name}_valid", f"output wire p_{name}_ready"))
    ports.extend(("output reg [17:0] p_context_payload", "output wire p_context_valid", "input wire p_context_ready"))
    files = {"CachedDecodeAttention.sv": "module CachedDecodeAttention(" + ",".join(ports) + ");\n" +
             reference_behavior_bodies()["CachedDecodeAttention"] + "\nendmodule\n"}
    top_ports = ["input wire clk", "input wire rst_n"]
    bindings = [".d_d_clock(clk)", ".d_d_reset(rst_n)"]
    for name in ("q", "k", "v"):
        top_ports.extend((f"input wire [17:0] {name}_payload", f"input wire {name}_valid", f"output wire {name}_ready"))
        bindings.extend(f".p_{name}_{role}({name}_{role})" for role in ("payload", "valid", "ready"))
    top_ports.extend(("output wire [17:0] context_payload", "output wire context_valid", "input wire context_ready"))
    bindings.extend(f".p_context_{role}(context_{role})" for role in ("payload", "valid", "ready"))
    files["LlmAttentionDev.sv"] = ("module LlmAttentionDev(" + ",".join(top_ports) + ");\n" +
        "CachedDecodeAttention attention(" + ",".join(bindings) + ");\nendmodule\n")
    return files
