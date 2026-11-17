# LLM inference development cases

The current `paper1-v2.3` case population comprises three quantized LLM
inference subsystems. [The adopted amendment](../../../../docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md)
defines scope; methods, budgets and evidence rules remain inherited from v2.2.

| Case | Family | Fixed development profile | Mechanisms |
| --- | --- | --- | --- |
| `qkv` | `llm_quantized_qkv_projection` | T2, Din5, Hq4, Hkv2, head dimension3, lane2 | Public synthetic projections, different Q/KV shapes, signed requantization, independently stalled outputs |
| `attention` | `llm_kv_cache_decode_attention` | Hq4, Hkv2, D3, capacity4, lane2 | Persistent KV append, actual GQA group mapping, stable public exp LUT, normalized AV, reset invalidation |
| `ffn` | `llm_gated_ffn` | T2, Din5, Dff7, lane2 | Gate/up, public SiLU LUT, elementwise gate, down projection, same-input residual |

Each case owns `task.py` (public facts/assets), `oracle.py` and `harness.py`
(evaluator-owned math/stimuli), `reference.py` (explicit hand-authored control),
and a local README. The generic PC checker/emitter contains no case algorithm.
These fixed profiles are independent: their scales, zero points and invocation
boundaries do not define one directly composable decoder layer. No model weights,
language-model accuracy, token-generation throughput or official qualification
is claimed. FFN normalization and QKV RoPE are outside their boundaries.

The [case coverage and next-increment guide](../../../../docs/code-guide/llm-case-coverage.zh.md)
maps current obligations to actual test sources and distinguishes remaining
qualification work. It does not promote the three controls into a benchmark.

## Public preparation

Run from the repository root using this checkout's source:

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m sr2fpga_agent.tasks.llm prepare --case all --output artifacts/paper1-ai/llm-public-01
```

The output must be fresh and below `artifacts/`. Its `public/` directories contain
only registered requirements, target/capability profiles and original public
asset bytes. Reference bodies, oracle, stimuli and expected outputs are not
placed there. Source snapshots and preparation events use the existing immutable
ArtifactStore outside `public/`. Preparation makes zero model/tool calls.
The source snapshot is provenance, not an OS access sandbox for a candidate.

## Hand-authored control validation

```powershell
python -B -m sr2fpga_agent.tasks.llm check-reference --case all --output artifacts/paper1-ai/llm-reference-01
```

This command assembles each manual PC, loads typed public sources, runs static
checks, emits deterministic structure, composes explicit reference bodies with
real Yosys checks, compiles with Icarus and runs vvp plus an independent trace
checker. It retains invalid/failed parser and tool records. `result.json` keeps
static, composition, compile, simulation, semantic and synthesis states separate;
it records `official=false`, `candidate_generated=false`, `model_calls=0` and
`hidden_evaluation=not_run`. Existing output is never overwritten.

Add `--synthesize` explicitly to also run generic `Yosys synth -top` within the
profile timeout. Generic cells do not establish FPGA resource mapping or L4.
Use `--case qkv`, `--case attention` or `--case ffn` for one case.

## Regression

```powershell
python -B -m pytest agent/tests/test_sr2fpga_llm_suite.py agent/tests/test_sr2fpga_llm_qkv.py agent/tests/test_sr2fpga_llm_attention.py agent/tests/test_sr2fpga_llm_ffn.py -q -p no:cacheprovider --basetemp=artifacts/paper1-ai/llm-tests-01
```

Real-tool tests require Yosys/Icarus/vvp. On this Windows installation Icarus
has returned `0xC0000005` inside the execution sandbox; preserve the failed
record and use the host approval mechanism for environment qualification.
Do not skip failed assertions or execute a leftover simulator binary.

The old [DW/PW case](ai_dw_pw/README.md) and its original runs remain intact as
historical development/regression assets. No prior result transfers to this
LLM population. Formal family qualification, splits, design clusters, full
budget freeze and physical evidence remain separate work.
