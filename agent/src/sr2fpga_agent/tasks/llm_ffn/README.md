# Quantized LLM gated FFN development case

This fixed engineering case models the gate/up projections, SiLU lookup,
elementwise gating, down projection and a same-input residual addition used
around LLM feed-forward computation. It fixes two tokens, hidden width 5,
expanded width 7 and two signed INT8 lanes. The weights are synthetic public
constants, not a model checkpoint. This is a small RTL construction and
correctness case, not full-model inference, language-quality evidence or a
qualified benchmark population.

The boundary is `y=FFN(x)+x`. Normalization is outside this operator, and the
residual is exactly the public input `x`. A complete pre-norm decoder block
would instead preserve the original pre-normalization residual and supply a
separate normalized FFN input. This case does not implement RMSNorm or claim
that larger block.

## Exact public arithmetic

All activations use `real=raw/4`, zero point 0, signed 8-bit storage. All weights
use scale 1/4 and zero point 0. Bias is in the centered accumulator's units and
is added once before requantization. Accumulators use signed INT32 mathematical
semantics; the fixed input/weight bounds cannot overflow that range.

For each token, let `RNE` mean signed round-to-nearest with ties to even, and
`sat8` clamp to `[-128,127]`:

```text
g[j] = sat8(RNE((gate_bias[j] + sum_i x[i]*gate_weight[j,i])/4))
u[j] = sat8(RNE((up_bias[j] + sum_i x[i]*up_weight[j,i])/4))
a[j] = SILU_LUT[g[j]+128]
z[j] = sat8(RNE(a[j]*u[j]/4))
y[i] = sat8(RNE((down_bias[i] + sum_j z[j]*down_weight[i,j])/4) + x[i])
```

The 256-entry SiLU approximation is frozen as integer public asset bytes. Its
generation rule was `round-half-even(4*SiLU(q/4))`, clamped to signed INT8, using
Decimal precision 70 for `q=-128..127`. The table itself is the executable task
semantics. Runtime oracle and RTL never compute floating-point sigmoid/exp.
Passing verifies equivalence to this table; it does not establish the table's
model-quality or approximation-error suitability.

For the all-zero input, every gated product is zero and the output token is
`(1,0,1,-1,0)` from down bias. Input `(4,0,0,0,0)` gives output
`(5,0,1,-2,0)`, exercising the gate and residual ordering.

## Fields and transaction contract

`build_development_task()` returns public facts, a requirement-owned boundary,
public weight/LUT JSON bytes, and complete registered development target and
capability documents. It contains no evaluator input frames, expected outputs
or harness. The target fixes 10ns simulation clock, 60-second individual tool
timeouts and the actual driver's 4000-cycle global ceiling.

The public tensors have axes `[T,C]`, order `T,C`, lanes on C, and
`zero_pad_mask` tails. Each token has three 18-bit beats: masks `11,11,01`,
lane0 in bits 7:0, lane1 in 15:8, mask in 17:16. Invalid tail lanes are raw0.
One invocation therefore consumes six beats and produces six beats. The
internal seven-channel expanded tensors consume four beats per token with
masks `11,11,11,01`.

Tokens are numerically independent: outputs may begin after the first token is
accepted, while the second input token is still arriving. The monitor appends
expected outputs after each three accepted input beats and closes the invocation
only after all six inputs and six outputs. It does not require the reference's
full-frame buffering.

Transfers occur on rising-edge `valid&&ready`. A blocked producer must hold
valid and the entire payload. Invocations cannot interleave; the next input
invocation starts after previous final output acceptance. Active-low
synchronous reset cancels all partial and pending work and suppresses output
valid after the reset edge. Under the frozen source/sink service assumptions,
completion from first input offer to final output acceptance must have cycle
difference at most 512. The monitor checks the last output beat before clearing
its deadline state.

## Reference decomposition and verification

The hand-authored PC reference contains `FfnInputFork`, `FfnGateUp` and
`FfnFuseDownResidual`. The explicit fork tracks each destination's independent
acceptance. Gate/up projections have separate output counters and can stall
independently. The final unit buffers gate/up and residual tensors, pairs the
same token/channel, performs LUT gating and down projection, then adds the
corresponding residual. This is one reference architecture, not a requirement
that candidate designs duplicate its module layout or buffering.

`reference.py` supplies explicit reference behavior bodies and a separately
wired manual control. The generic PC emitter never inserts these algorithms.
`oracle.py` uses exact Python integer/Fraction arithmetic; RTL uses independent
signed integer loops and quotient/remainder rounding. Both share only public
constants. Tests also implement a separate columnwise mathematical crosscheck,
public LUT reconstruction and hand-derived packing/bias/residual examples.

`harness.py` is evaluator-owned. It drives a partial-input reset, a blocked
pending-output reset and three complete invocations with input pauses, output
stalls and drain cycles. The scoreboard reconstructs expected values from
accepted input beats, checks every offered output, stable blocked tokens,
complete counts and reset cancellation. PASS strings, exit0 or an early finish
do not replace trace completion; a corrupted real output trace must fail.
The pending-output reset probe feeds concurrently and cancels as soon as an
output is held, so it does not require a token-streaming design to absorb the
whole frame during a forced stall. This reset-cancelled probe permits a longer
stall; the normal bounded-completion assumption applies to completing calls.

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m pytest agent/tests/test_sr2fpga_llm_ffn.py -q -p no:cacheprovider `
  --basetemp=artifacts/paper1-ai/<fresh-ffn-tests>
```

Real parser tests need Yosys; RTL tests need Icarus/vvp. Tool crashes remain
failures and must be distinguished from algorithm mismatches. Local regression
does not authorize model generation, held-out evaluation, physical implementation
or evidence promotion.
