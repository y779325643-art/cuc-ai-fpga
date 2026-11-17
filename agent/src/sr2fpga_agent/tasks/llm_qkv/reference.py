"""Explicit hand-authored QKV control bodies; never inserted by the emitter."""

from __future__ import annotations

from .task import WEIGHTS, BIASES, OUTPUT_DENOMINATORS, OUTPUT_ZEROS, MODULES


def _lookup(name: str, values: tuple[int, ...]) -> str:
    return (f"function integer {name}(input integer index);\nbegin\ncase(index)\n" +
            "\n".join(f"{index}: {name} = {value};" for index, value in enumerate(values)) +
            f"\ndefault: {name}=0;\nendcase\nend\nendfunction\n")


ROUNDING = """
function integer rne(input integer value, input integer divisor);
integer magnitude, quotient, remainder;
begin
  magnitude = value < 0 ? -value : value;
  if(divisor == 2) begin quotient=magnitude >> 1; remainder=magnitude & 1; end
  else begin quotient=magnitude >> 2; remainder=magnitude & 3; end
  if(2*remainder > divisor || (2*remainder == divisor && quotient[0])) quotient=quotient+1;
  rne = value < 0 ? -quotient : quotient;
end
endfunction
function integer sat8(input integer value);
begin
  if(value < -128) sat8=-128;
  else if(value > 127) sat8=127;
  else sat8=value;
end
endfunction
"""

BROADCAST = """
reg holding;
reg [2:0] accepted;
reg [17:0] token;
assign p_rx_ready = !holding;
assign p_q_payload = token;
assign p_k_payload = token;
assign p_v_payload = token;
assign p_q_valid = holding && !accepted[0];
assign p_k_valid = holding && !accepted[1];
assign p_v_valid = holding && !accepted[2];
always @(posedge d_d_clock) begin
  if(!d_d_reset) begin holding<=0; accepted<=0; token<=0; end
  else if(!holding) begin
    if(p_rx_valid) begin token<=p_rx_payload; accepted<=0; holding<=1; end
  end else begin
    if(p_q_ready) accepted[0]<=1;
    if(p_k_ready) accepted[1]<=1;
    if(p_v_ready) accepted[2]<=1;
    if((accepted[0] || p_q_ready) && (accepted[1] || p_k_ready) && (accepted[2] || p_v_ready))
      holding<=0;
  end
end
"""


def _projection(branch: str, *, tokens_per_batch: int = 2) -> str:
    if type(tokens_per_batch) is not int or tokens_per_batch not in (1, 2):
        raise ValueError("the development control supports one or two tokens per internal batch")
    outputs = len(WEIGHTS[branch])
    beats = 2 * outputs // 3 * tokens_per_batch
    body = _lookup("weight", tuple(value for row in WEIGHTS[branch] for value in row))
    body += _lookup("bias", BIASES[branch]) + ROUNDING
    body += """
reg signed [7:0] image [0:INPUT_VALUES_MINUS_ONE];
reg signed [7:0] projected [0:TOTAL_OUTPUTS_MINUS_ONE];
reg [1:0] state;
integer received, sent, token_index, output_index, input_index, accumulator;
assign p_rx_ready = state == 0;
assign p_tx_valid = state == 2;
always @* begin
  p_tx_payload=18'd0;
  if(state == 2) begin
    if((sent & 1) == 0) p_tx_payload={2'b11,projected[(sent/2)*3+1],projected[(sent/2)*3]};
    else p_tx_payload={2'b01,8'd0,projected[(sent/2)*3+2]};
  end
end
always @(posedge d_d_clock) begin
  if(!d_d_reset) begin state<=0; received<=0; sent<=0; end
  else case(state)
    0: if(p_rx_valid && p_rx_ready) begin
      image[(received/3)*5+(received%3)*2] <= $signed(p_rx_payload[7:0]);
      if(received%3 != 2) image[(received/3)*5+(received%3)*2+1] <= $signed(p_rx_payload[15:8]);
      if(received == LAST_INPUT_BEAT) begin state<=1; received<=0; end
      else received<=received+1;
    end
    1: begin
      for(token_index=0;token_index<TOKENS_PER_BATCH;token_index=token_index+1) begin
        for(output_index=0;output_index<OUTPUT_DIM;output_index=output_index+1) begin
          accumulator=bias(output_index);
          for(input_index=0;input_index<5;input_index=input_index+1)
            accumulator=accumulator+($signed(image[token_index*5+input_index])+2)*weight(output_index*5+input_index);
          projected[token_index*OUTPUT_DIM+output_index] <= sat8(rne(accumulator,DIVISOR)+OUTPUT_ZERO);
        end
      end
      state<=2; sent<=0;
    end
    2: if(p_tx_ready) begin
      if(sent == LAST_BEAT) begin state<=0; sent<=0; end
      else sent<=sent+1;
    end
    default: begin state<=0; received<=0; sent<=0; end
  endcase
end
"""
    replacements = {"TOTAL_OUTPUTS_MINUS_ONE": tokens_per_batch * outputs - 1,
                    "INPUT_VALUES_MINUS_ONE": tokens_per_batch * 5 - 1,
                    "LAST_INPUT_BEAT": tokens_per_batch * 3 - 1,
                    "TOKENS_PER_BATCH": tokens_per_batch, "OUTPUT_DIM": outputs,
                    "DIVISOR": OUTPUT_DENOMINATORS[branch], "OUTPUT_ZERO": OUTPUT_ZEROS[branch],
                    "LAST_BEAT": beats - 1}
    for name, value in replacements.items():
        body = body.replace(name, str(value))
    return body


def reference_behavior_bodies() -> dict[str, str]:
    return {"InputBroadcast": BROADCAST, **{module: _projection(branch) for branch, module in MODULES.items()}}


def _header(name: str, outputs: tuple[str, ...]) -> str:
    ports = ["input logic d_d_clock", "input logic d_d_reset",
             "input logic [17:0] p_rx_payload", "input logic p_rx_valid", "output logic p_rx_ready"]
    for output in outputs:
        ports += [f"output logic [17:0] p_{output}_payload", f"output logic p_{output}_valid",
                  f"input logic p_{output}_ready"]
    return "module " + name + "(\n" + ",\n".join(ports) + "\n);\n"


def render_reference_project(*, tokens_per_batch: int = 2) -> dict[str, str]:
    """Manual wrapper plus explicit controls, independent of generic construction."""
    files = {"reference_broadcast.sv": _header("ReferenceBroadcast", tuple(MODULES)) + BROADCAST + "\nendmodule\n"}
    for branch in MODULES:
        files[f"reference_{branch}.sv"] = (_header("Reference" + branch.upper(), ("tx",)) +
                                            _projection(branch, tokens_per_batch=tokens_per_batch) + "\nendmodule\n")
    ports = ["input logic clk", "input logic rst_n", "input logic [17:0] in_payload",
             "input logic in_valid", "output logic in_ready"]
    for branch in MODULES:
        ports += [f"output logic [17:0] {branch}_payload", f"output logic {branch}_valid",
                  f"input logic {branch}_ready"]
    lines = ["module LlmQkvDev(\n" + ",\n".join(ports) + "\n);"]
    for branch in MODULES:
        lines += [f"wire [17:0] {branch}_input_payload;", f"wire {branch}_input_valid, {branch}_input_ready;"]
    connections = [".d_d_clock(clk)", ".d_d_reset(rst_n)", ".p_rx_payload(in_payload)",
                   ".p_rx_valid(in_valid)", ".p_rx_ready(in_ready)"]
    for branch in MODULES:
        connections += [f".p_{branch}_payload({branch}_input_payload)", f".p_{branch}_valid({branch}_input_valid)",
                        f".p_{branch}_ready({branch}_input_ready)"]
    lines.append("ReferenceBroadcast broadcast (" + ",".join(connections) + ");")
    for branch in MODULES:
        lines.append(f"Reference{branch.upper()} projection_{branch} (.d_d_clock(clk),.d_d_reset(rst_n),"
                     f".p_rx_payload({branch}_input_payload),.p_rx_valid({branch}_input_valid),.p_rx_ready({branch}_input_ready),"
                     f".p_tx_payload({branch}_payload),.p_tx_valid({branch}_valid),.p_tx_ready({branch}_ready));")
    files["top.sv"] = "\n".join(lines) + "\nendmodule\n"
    return files
