# PC 2.1 development guidance and public-feedback revision, 2026-10-29

The user authorized fixing tool compatibility guidance, public feedback and
proposal-format instructions, adding regression coverage, then rerunning one
QKV M0-M5 development block through the `.env` API with at most 11 actual model
calls. Existing work, staging and original runtime records remain preserved.

The previous block is
`artifacts/paper1-ai/api-qkv-development-20261028-01/`. Its M5 candidate passed
the public and synthetic terminal development checks; the other five slots
did not. The subsequent diagnosis is in
`artifacts/paper1-ai/api-qkv-analysis-20261029-01/`. Its modified M1 public-only
debug copy is diagnostic evidence, not a replacement for the original M1
candidate or score.

## Changed development surfaces

- Every model stage receives `pc21-generic-hdl-guidance-v1`: native Yosys
  `read_verilog -sv` compatibility, Icarus `iverilog -g2012`/`vvp`, portable
  constant tables and explicit combinational dependencies. The request identity
  records the guidance version. Mathematical requirements and public assets
  remain the same as in the previous block.
- JSON instructions prohibit Markdown fences and make body ownership explicit:
  the framework supplies the module header and closing `endmodule`. Repair
  instructions have one repair-schema root. Strict parsing remains in effect;
  no response cleanup or automatic JSON/RTL repair is introduced.
- `pc21-public-feedback-v2` extends the public projection with bounded,
  allowlisted diagnostics. Candidate-source file/line locations are filtered
  against actual declared files. Functional errors map to fixed categories;
  raw logs, trusted source locations, test inputs, vectors, seeds and hidden
  results are excluded. The feedback revision changes the tool-policy identity.

The trusted evaluator change concerns the public feedback surface. It does not
change oracle mathematics, test inputs, stage acceptance, tool selection,
method-call ceilings or terminal scoring. The existing protocol remains
unfrozen, and formal execution remains unsupported by the development entry.

## New evidence and comparison scope

The new preparation, regression and runtime directory is
`artifacts/paper1-ai/api-qkv-guidance-rerun-20261029-01/`. It captures before
files, the original staging patch and hashes of 633 previous-run files before
execution. The rerun uses a fresh campaign and output directory. Its actual
source and contract bytes are archived by the existing runtime.

The intended comparison fixes the public task bytes, model alias and thinking
mode, schedule, resource ceilings, local toolchain and public/synthetic terminal
suites. Guidance, format instructions and public feedback are revised together.
The earlier run had no provider decoding seed and no pinned server-side model
weights, so this is a descriptive before/after development comparison. It
cannot isolate the causal contribution of each change or establish population
performance. Actual outcomes and cost are read from the new run's sealed
artifacts, not asserted by this migration record.

No formal/actual held-out campaign, evidence promotion, external publication,
push or shared-branch merge is authorized by this development rerun.
