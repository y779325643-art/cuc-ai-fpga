"""Evaluator-owned multi-stream schedule and persistent-cache transaction checker."""

from __future__ import annotations

from dataclasses import dataclass
import random

from .oracle import DecodeInput, DecodeOracle, pack_vectors, unpack_vectors
from .task import (COMPLETION_CYCLES, KV_HEADS, MAX_CONTEXT,
                   MAX_SIMULATION_CYCLES, QUERY_HEADS)

TESTBENCH_TOP = "trusted_llm_attention_tb"
INPUT_BEATS = {"q": QUERY_HEADS * 2, "k": KV_HEADS * 2, "v": KV_HEADS * 2}
OUTPUT_BEATS = QUERY_HEADS * 2


def development_commands() -> tuple[DecodeInput, ...]:
    rng = random.Random(76103)
    commands = [
        DecodeInput((0,) * 12, (5, -2, 1, -3, 7, 2), (10, -10, 5, -30, 20, 11)),
        DecodeInput((0,) * 12, (-4, 3, 2, 1, -5, 3), (20, 6, -3, 6, -12, 31)),
        DecodeInput((16, -8, 5, -12, 24, 7, -5, 18, -30, 8, -14, 9),
                    (20, -10, 3, -7, 8, 14), (127, -128, 9, -55, 67, -13)),
        DecodeInput(tuple(rng.randrange(-128, 128) for _ in range(12)),
                    tuple(rng.randrange(-128, 128) for _ in range(6)),
                    tuple(rng.randrange(-128, 128) for _ in range(6))),
        DecodeInput((0,) * 12, (1, 1, 1, -1, -1, -1), (-80, 60, 7, 91, -44, -9)),
        DecodeInput((0,) * 12, (0,) * 6, (31, -13, 14, -21, 20, 2)),
    ]
    return tuple(commands)


@dataclass(frozen=True)
class TraceResult:
    cycles: int
    completed_invocations: int
    q_beats: int
    k_beats: int
    v_beats: int
    output_beats: int
    resets: int
    cancelled_invocations: int
    max_valid_cache_length: int
    final_valid_cache_length: int


def check_trace(stdout: str, *, expected_completed: int = 6) -> TraceResult:
    """Derive each expected output from accepted inputs and accumulated K/V."""
    incoming = {name: [] for name in INPUT_BEATS}
    counts = {name: 0 for name in INPUT_BEATS}
    previous_input = {name: None for name in INPUT_BEATS}
    pending: list[int] = []
    previous_output = None
    oracle = DecodeOracle()
    last_cycle = complete = output_count = resets = cancelled = max_length = 0
    started = None
    ended = was_reset = False
    for line in stdout.splitlines():
        if line.startswith("TRACE_END "):
            if ended or int(line.split()[1]) != last_cycle:
                raise ValueError("invalid trace completion")
            ended = True
            continue
        if not line.startswith("TRACE "):
            continue
        if ended:
            raise ValueError("trace after completion")
        parts = line.split()
        if len(parts) != 15:
            raise ValueError("malformed attention trace")
        try:
            cycle, reset = map(int, parts[1:3])
            streams = {}
            if reset == 0:
                if was_reset and parts[12] != "0":
                    raise ValueError("output valid persisted after reset edge")
                streams = {name: (0, 0, 0) for name in INPUT_BEATS}
                valid = ready = payload = 0
            else:
                for name, offset in (("q", 3), ("k", 6), ("v", 9)):
                    iv, ir = map(int, parts[offset:offset + 2])
                    streams[name] = (iv, ir, int(parts[offset + 2], 16) if iv else 0)
                valid, ready = map(int, parts[12:14])
                payload = int(parts[14], 16) if valid else 0
        except ValueError as error:
            raise ValueError("unknown or invalid signal in attention trace: " + str(error)) from error
        controls = [reset, valid, ready] + [value for iv, ir, _ in streams.values() for value in (iv, ir)]
        payloads = [payload] + [value for _, _, value in streams.values()]
        if cycle != last_cycle + 1 or any(value not in (0, 1) for value in controls):
            raise ValueError("noncontiguous cycle or nonbinary control")
        if any(not 0 <= value < (1 << 18) for value in payloads):
            raise ValueError("invalid eighteen-bit payload")
        last_cycle = cycle
        if not reset:
            if not was_reset:
                resets += 1
                cancelled += bool(pending or any(incoming.values()))
            oracle.reset()
            for name in incoming:
                incoming[name].clear()
                previous_input[name] = None
            pending.clear()
            previous_output = started = None
            was_reset = True
            continue
        was_reset = False
        for name, (iv, ir, ip) in streams.items():
            if previous_input[name] is not None and (not iv or ip != previous_input[name]):
                raise ValueError("source changed a stalled input token")
            previous_input[name] = ip if iv and not ir else None
            if iv and started is None:
                started = cycle
            if iv and ir:
                if pending:
                    raise ValueError("next invocation interleaved with pending output")
                incoming[name].append(ip)
                counts[name] += 1
                if len(incoming[name]) > INPUT_BEATS[name]:
                    raise ValueError("too many input beats")
        if oracle.valid_length == MAX_CONTEXT and not pending and any(ir for _, ir, _ in streams.values()):
            raise ValueError("full cache did not backpressure all inputs")
        if all(len(incoming[name]) == count for name, count in INPUT_BEATS.items()):
            command = DecodeInput(unpack_vectors(incoming["q"], QUERY_HEADS),
                                  unpack_vectors(incoming["k"], KV_HEADS),
                                  unpack_vectors(incoming["v"], KV_HEADS))
            pending = list(pack_vectors(oracle.decode(command), QUERY_HEADS))
            max_length = max(max_length, oracle.valid_length)
            for beats in incoming.values():
                beats.clear()
        if previous_output is not None and (not valid or payload != previous_output):
            raise ValueError("DUT changed a stalled output token")
        previous_output = payload if valid and not ready else None
        # Check before completion clears 'started', including the final accept.
        if started is not None and cycle - started > COMPLETION_CYCLES:
            raise ValueError("bounded attention completion exceeded")
        if valid:
            if not pending:
                raise ValueError("unexpected or premature attention output")
            if payload != pending[0]:
                raise ValueError(f"attention output mismatch at cycle {cycle}: got {payload:05x}, expected {pending[0]:05x}")
            if ready:
                pending.pop(0)
                output_count += 1
                if not pending:
                    complete += 1
                    started = None
    if not ended or not last_cycle or pending or any(incoming.values()) or previous_output is not None or any(
            value is not None for value in previous_input.values()):
        raise ValueError("incomplete trusted attention schedule")
    if complete != expected_completed:
        raise ValueError(f"expected {expected_completed} completed attention invocations, observed {complete}")
    return TraceResult(last_cycle, complete, counts["q"], counts["k"], counts["v"], output_count,
                       resets, cancelled, max_length, oracle.valid_length)


def render_testbench(commands: tuple[DecodeInput, ...] | None = None) -> str:
    commands = commands if commands is not None else development_commands()
    if len(commands) != 6:
        raise ValueError("fixed attention schedule requires six complete commands")
    assignments = []
    for index, command in enumerate(commands):
        for name, values, heads in (("q", command.query, QUERY_HEADS), ("k", command.key, KV_HEADS), ("v", command.value, KV_HEADS)):
            for j, beat in enumerate(pack_vectors(values, heads)):
                assignments.append(f"{name}_stimulus[{index * INPUT_BEATS[name] + j}] = 18'h{beat:05x};")
    send_tasks = []
    for name in INPUT_BEATS:
        send_tasks.append(f"""task send_{name}(input [17:0] value);
begin
 @(negedge clk); {name}_valid=1; {name}_payload=value;
 @(posedge clk);
 while({name}_ready !== 1'b1) @(posedge clk);
 @(negedge clk); {name}_valid=0;
end
endtask
""")
    return """module trusted_llm_attention_tb;
reg clk=0, rst_n=0;
reg q_valid=0,k_valid=0,v_valid=0;
reg [17:0] q_payload=0,k_payload=0,v_payload=0;
wire q_ready,k_ready,v_ready,context_valid;
wire [17:0] context_payload;
reg context_ready=0, forced_stall=0, drain=0;
integer cycle=0, completed_beats=0, i,j;
reg [17:0] q_stimulus[0:47], k_stimulus[0:23],v_stimulus[0:23];
LlmAttentionDev dut(.clk(clk),.rst_n(rst_n),
 .q_payload(q_payload),.q_valid(q_valid),.q_ready(q_ready),
 .k_payload(k_payload),.k_valid(k_valid),.k_ready(k_ready),
 .v_payload(v_payload),.v_valid(v_valid),.v_ready(v_ready),
 .context_payload(context_payload),.context_valid(context_valid),.context_ready(context_ready));
always #5 clk=~clk;
always @(negedge clk) context_ready = !forced_stall && (drain || (cycle%7 != 0 && cycle%7 != 1));
always @(posedge clk) begin
 cycle=cycle+1;
 $display("TRACE %0d %0d %0d %0d %05h %0d %0d %05h %0d %0d %05h %0d %0d %05h",
 cycle,rst_n,q_valid,q_ready,q_payload,k_valid,k_ready,k_payload,v_valid,v_ready,v_payload,context_valid,context_ready,context_payload);
 if(!rst_n) completed_beats=0;
 else if(context_valid && context_ready) completed_beats=completed_beats+1;
 if(cycle>""" + str(MAX_SIMULATION_CYCLES) + """) begin $display("TRUSTED_TIMEOUT"); $finish; end
end
task reset_dut;
begin
 @(negedge clk); rst_n=0; q_valid=0; k_valid=0; v_valid=0;
 repeat(3) @(negedge clk);
 rst_n=1;
end
endtask
""" + "\n".join(send_tasks) + """
task send_command(input integer index);
integer b;
begin
 if(index%2 == 0) begin
  for(b=0;b<8;b=b+1) send_q(q_stimulus[index*8+b]);
  for(b=0;b<4;b=b+1) send_k(k_stimulus[index*4+b]);
  for(b=0;b<4;b=b+1) send_v(v_stimulus[index*4+b]);
 end else begin
  for(b=0;b<4;b=b+1) send_v(v_stimulus[index*4+b]);
  for(b=0;b<4;b=b+1) send_k(k_stimulus[index*4+b]);
  for(b=0;b<8;b=b+1) send_q(q_stimulus[index*8+b]);
 end
end
endtask
initial begin
""" + "\n".join(assignments) + """
 reset_dut;
 send_q(q_stimulus[0]);
 reset_dut;
 forced_stall=1;
 send_command(0);
 wait(context_valid === 1'b1);
 repeat(2) @(negedge clk);
 reset_dut;
 forced_stall=0;
 for(i=0;i<4;i=i+1) begin
  send_command(i);
  wait(completed_beats == (i+1)*8);
 end
 repeat(3) @(negedge clk);
 if(q_ready !== 0 || k_ready !== 0 || v_ready !== 0) $fatal(1,"full cache accepted input");
 reset_dut;
 send_command(4);
 wait(completed_beats==8);
 send_command(5);
 wait(completed_beats==16);
 @(negedge clk); drain=1;
 repeat(12) @(negedge clk);
 $display("TRACE_END %0d",cycle);
 $finish;
end
endmodule
"""
