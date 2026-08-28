# Evidence table

> Historical evidence-cutoff snapshot created under `paper1-freeze-v1.3`.
> The active `paper1-freeze-v1.7` controls current scope; this table is not
> silently updated and does not override the active no-training protocol.

| Claim | Evidence/source | Strength | Usable section | Risk | Status |
|---|---|---|---|---|---|
| Repository reorganization is locally complete | `reports/reorganization/final-verification.md`; current checkout | evidence-backed | Artifact/implementation | Local ref equality is not remote CI | verified, bounded |
| The current code supports multi-file generation and H0-H3/L0-L4 orchestration | `agent/src/sr2fpga_agent/`; Agent tests | evidence-backed | System/method | Support is not general success | implemented and tested |
| Training is independently packaged | `training/pyproject.toml`, `training/src/`, boundary tests | evidence-backed | System/artifact | No trained model follows from packaging | implemented and tested |
| 31 families have L3-or-higher evidence | `reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json` and referenced stable artifacts | evidence-backed | Current capability | Ledger granularity is family-level | verified |
| 14/14 Paper-1 core families are L3 and mutation-qualified | canonical catalog recommended set plus evidence ledger | evidence-backed | Benchmark readiness | Deterministic/reference evidence only | verified |
| Nine families have independent Python-reference evidence | evidence ledger; Phase C report | evidence-backed | Oracle-quality motivation | Does not cover all 31 families | verified |
| Two families have OpenXC7 L4 passes | evidence ledger and stable L4 artifacts | evidence-backed | Physical confirmation | Not general L4, bitstream, or L5 | verified, representative |
| Phase D measured learned/model quality | Phase D reports | unsupported | none | 0/24 L0 and no repair | forbidden |
| Current runtime enforces the full v1.2 schema and W1-W10 | schema, checker, fixture conflict | unsupported | debt/method boundary | Narrative spec exceeds code | blocked |
| System-HIS is a defensible typed requirement/project contract | v1.2 schema, generators, checkers, L0 cross-file checks | evidence-backed for existence; plausible for research value | Method | Value over controls is untested | implemented, effect hypothetical |
| Oracle separation addresses visible-harness over-solving | HORIZON limitation plus intended hidden/stress/reference protections | plausible-inference | Motivation/protocol | Current oracle path can use candidate TB and leak diagnostics into repair | blocked until G3 |
| HORIZON motivates the matched outer-loop control | HORIZON reader and comparison analysis | evidence-backed | Related work/baselines | Current M1 lacks several HORIZON semantics and is not a reproduction | required control |
| Repository-level tool repair is SR2FPGA novelty | HORIZON and adjacent work | unsupported | none | Direct novelty collision | forbidden |
| Generated HIS improves first-attempt structural correctness | prior small ablations and mechanism | plausible-inference | Hypothesis/RQ1 | Prompt and extra-call confounds | unproven |
| HIS-guided repair improves hidden semantic success under equal budget | no outcome-producing matched experiment | hypothesis | RQ2/results | Could only move failures from L0 to L2 | unproven |
| Verified-final or verified-trajectory SFT improves held-out-family VPP | training infrastructure only | outside Paper-1 | future work only | RQ3/M6 withdrawn in v1.3 | withdrawn |
| A learned model reduces attempts/tokens/tool cost | no matched cost experiment | outside Paper-1 | future work only | No Paper-1 training | withdrawn |
| Tier-B constrained decoding is necessary for Paper 1 | historical `docs/superpowers/specs/2026-06-25-system-his-constrained-decoding-design.md` (Git history); active Paper-1 freeze | unsupported as a requirement | optional ablation/future work | High engineering cost and local-model asymmetry | demoted |
| QoR prediction is a Paper-1 contribution | export/training task definitions only | unsupported | optional extension | No calibrated prediction result | demoted |
| L5 is required to support the core learning claim | no L5 evidence | unsupported | optional extension | Board work can dominate schedule | excluded from minimum closure |
| The task catalog is semantic evidence | catalog intent and known semantic errors | unsupported | none | `clock_divider`, T7, T10/T11 conflicts | forbidden |

## Evidence-use rule

Only `evidence-backed` rows may be written in present tense as results. A
`plausible-inference` must be explicitly introduced as an interpretation. A
`hypothesis` must name its comparison, outcome, and failure condition. An
`unsupported` claim is removed or moved to future work.
