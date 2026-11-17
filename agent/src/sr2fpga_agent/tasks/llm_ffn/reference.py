"""Explicit hand-authored RTL control, never inserted by the generic emitter."""

from __future__ import annotations

from .task import (GATE_WEIGHTS, UP_WEIGHTS, DOWN_WEIGHTS, GATE_BIAS, UP_BIAS,
                   DOWN_BIAS, SILU_LUT, signatures)


def _lookup(name: str, values: tuple) -> str:
    return (f"function integer {name}(input integer index);\nbegin\ncase(index)\n"
            + "\n".join(f"{i}: {name} = {value};" for i, value in enumerate(values))
            + f"\ndefault: {name} = 0;\nendcase\nend\nendfunction\n")


ROUND = """
function integer round4(input integer value);
integer magnitude, quotient, remainder;
begin
 magnitude = value < 0 ? -value : value;
 quotient = magnitude >> 2; remainder = magnitude & 3;
 if(remainder > 2 || (remainder == 2 && (quotient & 1))) quotient = quotient + 1;
 round4 = value < 0 ? -quotient : quotient;
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
    fork = """
reg [17:0] held;
reg busy, feature_pending, residual_pending;
assign p_rx_ready = !busy;
assign p_features_payload = held;
assign p_residual_payload = held;
assign p_features_valid = busy && feature_pending;
assign p_residual_valid = busy && residual_pending;
always @(posedge d_d_clock) begin
 if(!d_d_reset) begin busy<=0; feature_pending<=0; residual_pending<=0; held<=0; end
 else if(!busy) begin
  if(p_rx_valid) begin
   held<=p_rx_payload; busy<=1; feature_pending<=1; residual_pending<=1;
  end
 end else begin
  if(p_features_ready) feature_pending<=0;
  if(p_residual_ready) residual_pending<=0;
  if((!feature_pending || p_features_ready) && (!residual_pending || p_residual_ready)) busy<=0;
 end
end
"""
    project = (_lookup("gw", tuple(x for row in GATE_WEIGHTS for x in row))
               + _lookup("uw", tuple(x for row in UP_WEIGHTS for x in row))
               + _lookup("gb", GATE_BIAS) + _lookup("ub", UP_BIAS) + ROUND + """
reg signed [7:0] image [0:9];
reg signed [7:0] gates [0:13];
reg signed [7:0] ups [0:13];
reg [1:0] state;
reg [3:0] received, gate_sent, up_sent;
reg gate_done, up_done;
integer t,c,k,position,acc_g,acc_u;
assign p_rx_ready = state == 0;
assign p_gate_valid = state == 2 && !gate_done;
assign p_up_valid = state == 2 && !up_done;
always @* begin
 p_gate_payload=0; p_up_payload=0;
 if(state==2 && !gate_done) begin
  if(gate_sent%4==3) p_gate_payload={2'b01,8'd0,gates[(gate_sent/4)*7+6]};
  else p_gate_payload={2'b11,gates[(gate_sent/4)*7+(gate_sent%4)*2+1],gates[(gate_sent/4)*7+(gate_sent%4)*2]};
 end
 if(state==2 && !up_done) begin
  if(up_sent%4==3) p_up_payload={2'b01,8'd0,ups[(up_sent/4)*7+6]};
  else p_up_payload={2'b11,ups[(up_sent/4)*7+(up_sent%4)*2+1],ups[(up_sent/4)*7+(up_sent%4)*2]};
 end
end
always @(posedge d_d_clock) begin
 if(!d_d_reset) begin state<=0; received<=0; gate_sent<=0; up_sent<=0; gate_done<=0; up_done<=0; end
 else case(state)
  0: if(p_rx_valid && p_rx_ready) begin
   position=(received/3)*5+(received%3)*2;
   image[position]<=$signed(p_rx_payload[7:0]);
   if(received%3!=2) image[position+1]<=$signed(p_rx_payload[15:8]);
   if(received==5) begin state<=1; received<=0; end
   else received<=received+1;
  end
  1: begin
   for(t=0;t<2;t=t+1) for(c=0;c<7;c=c+1) begin
    acc_g=gb(c); acc_u=ub(c);
    for(k=0;k<5;k=k+1) begin
     acc_g=acc_g+$signed(image[t*5+k])*gw(c*5+k);
     acc_u=acc_u+$signed(image[t*5+k])*uw(c*5+k);
    end
    gates[t*7+c]<=clamp8(round4(acc_g)); ups[t*7+c]<=clamp8(round4(acc_u));
   end
   state<=2; gate_sent<=0; up_sent<=0; gate_done<=0; up_done<=0;
  end
  2: begin
   if(p_gate_valid && p_gate_ready) begin
    if(gate_sent==7) gate_done<=1; else gate_sent<=gate_sent+1;
   end
   if(p_up_valid && p_up_ready) begin
    if(up_sent==7) up_done<=1; else up_sent<=up_sent+1;
   end
   if((gate_done || (p_gate_valid && p_gate_ready && gate_sent==7)) &&
      (up_done || (p_up_valid && p_up_ready && up_sent==7))) begin state<=0; received<=0; end
  end
  default: begin state<=0; received<=0; gate_done<=0; up_done<=0; end
 endcase
end
""")
    fuse = (_lookup("dw", tuple(x for row in DOWN_WEIGHTS for x in row))
            + _lookup("db", DOWN_BIAS) + _lookup("silu", SILU_LUT) + ROUND + """
reg signed [7:0] gates [0:13];
reg signed [7:0] ups [0:13];
reg signed [7:0] residual [0:9];
reg signed [7:0] product [0:13];
reg signed [7:0] result [0:9];
reg [1:0] state;
reg [3:0] gate_count, up_count, residual_count, sent;
integer t,c,k,position,acc,activation;
assign p_gate_ready = state==0 && gate_count<8;
assign p_up_ready = state==0 && up_count<8;
assign p_residual_ready = state==0 && residual_count<6;
assign p_tx_valid = state==2;
always @* begin
 p_tx_payload=0;
 if(state==2) begin
  if(sent%3==2) p_tx_payload={2'b01,8'd0,result[(sent/3)*5+4]};
  else p_tx_payload={2'b11,result[(sent/3)*5+(sent%3)*2+1],result[(sent/3)*5+(sent%3)*2]};
 end
end
always @(posedge d_d_clock) begin
 if(!d_d_reset) begin state<=0; gate_count<=0; up_count<=0; residual_count<=0; sent<=0; end
 else case(state)
  0: begin
   if(p_gate_valid && p_gate_ready) begin
    position=(gate_count/4)*7+(gate_count%4)*2;
    gates[position]<=$signed(p_gate_payload[7:0]);
    if(gate_count%4!=3) gates[position+1]<=$signed(p_gate_payload[15:8]);
    gate_count<=gate_count+1;
   end
   if(p_up_valid && p_up_ready) begin
    position=(up_count/4)*7+(up_count%4)*2;
    ups[position]<=$signed(p_up_payload[7:0]);
    if(up_count%4!=3) ups[position+1]<=$signed(p_up_payload[15:8]);
    up_count<=up_count+1;
   end
   if(p_residual_valid && p_residual_ready) begin
    position=(residual_count/3)*5+(residual_count%3)*2;
    residual[position]<=$signed(p_residual_payload[7:0]);
    if(residual_count%3!=2) residual[position+1]<=$signed(p_residual_payload[15:8]);
    residual_count<=residual_count+1;
   end
   if(gate_count==8 && up_count==8 && residual_count==6) state<=1;
  end
  1: begin
   for(t=0;t<2;t=t+1) begin
    for(k=0;k<7;k=k+1) begin
     activation=silu($signed(gates[t*7+k])+128);
     product[t*7+k]=clamp8(round4(activation*$signed(ups[t*7+k])));
    end
    for(c=0;c<5;c=c+1) begin
     acc=db(c);
     for(k=0;k<7;k=k+1) acc=acc+$signed(product[t*7+k])*dw(c*7+k);
     result[t*5+c]<=clamp8(round4(acc)+$signed(residual[t*5+c]));
    end
   end
   state<=2; sent<=0;
  end
  2: if(p_tx_ready) begin
   if(sent==5) begin state<=0; gate_count<=0; up_count<=0; residual_count<=0; sent<=0; end
   else sent<=sent+1;
  end
  default: begin state<=0; gate_count<=0; up_count<=0; residual_count<=0; sent<=0; end
 endcase
end
""")
    return {"FfnInputFork": fork, "FfnGateUp": project, "FfnFuseDownResidual": fuse}


def _manual_header(module: str, signature: dict) -> str:
    """Separate control headers, without calling the PC structure emitter."""
    ports = ["input logic d_d_clock", "input logic d_d_reset"]
    for name, port in signature["ports"].items():
        direction = port["direction"]
        reverse = "input" if direction == "output" else "output"
        ports += [f"{direction} logic [17:0] p_{name}_payload",
                  f"{direction} logic p_{name}_valid", f"{reverse} logic p_{name}_ready"]
    return f"module {module}(\n" + ",\n".join(ports) + "\n);\n"


def render_reference_project() -> dict[str, str]:
    signatures_by_module = {"FfnInputFork": signatures()["fork"], "FfnGateUp": signatures()["project"],
                            "FfnFuseDownResidual": signatures()["fuse"]}
    files = {name + ".sv": _manual_header(name, signatures_by_module[name]) + body + "\nendmodule\n"
             for name, body in reference_behavior_bodies().items()}
    files["LlmGatedFfnDev.sv"] = """module LlmGatedFfnDev(
 input logic clk,rst_n,input logic [17:0] in_payload,input logic in_valid,output logic in_ready,
 output logic [17:0] out_payload,output logic out_valid,input logic out_ready);
wire [17:0] features_payload,residual_payload,gate_payload,up_payload;
wire features_valid,features_ready,residual_valid,residual_ready,gate_valid,gate_ready,up_valid,up_ready;
FfnInputFork fork_unit(.d_d_clock(clk),.d_d_reset(rst_n),
 .p_rx_payload(in_payload),.p_rx_valid(in_valid),.p_rx_ready(in_ready),
 .p_features_payload(features_payload),.p_features_valid(features_valid),.p_features_ready(features_ready),
 .p_residual_payload(residual_payload),.p_residual_valid(residual_valid),.p_residual_ready(residual_ready));
FfnGateUp project_unit(.d_d_clock(clk),.d_d_reset(rst_n),
 .p_rx_payload(features_payload),.p_rx_valid(features_valid),.p_rx_ready(features_ready),
 .p_gate_payload(gate_payload),.p_gate_valid(gate_valid),.p_gate_ready(gate_ready),
 .p_up_payload(up_payload),.p_up_valid(up_valid),.p_up_ready(up_ready));
FfnFuseDownResidual fuse_unit(.d_d_clock(clk),.d_d_reset(rst_n),
 .p_gate_payload(gate_payload),.p_gate_valid(gate_valid),.p_gate_ready(gate_ready),
 .p_up_payload(up_payload),.p_up_valid(up_valid),.p_up_ready(up_ready),
 .p_residual_payload(residual_payload),.p_residual_valid(residual_valid),.p_residual_ready(residual_ready),
 .p_tx_payload(out_payload),.p_tx_valid(out_valid),.p_tx_ready(out_ready));
endmodule
"""
    return files
