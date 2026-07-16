# SR2FPGA Phase C Independent Oracle Evidence

Generated on 2026-07-16 from the fresh qualification run
`phase-c-independent-oracle-20260714-v1` using
`configs/current/sr2fpga_phase_c_independent_oracle.example.yaml`.

## Scope

Phase C qualifies evaluator-local independent Python references for exactly four
domains and nine task families. This batch uses the deterministic reference
generator to validate the benchmark oracle and evidence pipeline; it is not an
LLM-generation result. OpenXC7, Vivado, and L5 were disabled for this batch.
Previously verified dual-tool L4 evidence for `fir_filter` and
`matrix_vector_mac` remains recorded separately in the task evidence ledger.

## Completion Gates

| Gate | Result |
| --- | ---: |
| Planned/completed families | 9 / 9 |
| L3 success | 9 / 9 |
| Rejected | 0 |
| Independent Python oracle pass | 9 / 9 |
| Oracle infrastructure errors | 0 |
| Required scenario classes | 4 / 4 for every family |
| Mutation cases scoreable and killed | 45 / 45 |
| Critical survivors | 0 |
| Critical non-scoreable mutations | 0 |
| Line-A ready | 9 / 9 |
| Hidden vector/seed export findings | 0 |
| Local evidence audit issues | 0 |

## Domain Summary

| Domain | Families | Public | Hidden | Randomized | Stress | Mutations killed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Numeric | 2 | 2 | 2 | 2 | 2 | 9 / 9 |
| Signal | 3 | 3 | 3 | 3 | 3 | 12 / 12 |
| Image | 2 | 2 | 2 | 2 | 2 | 15 / 15 |
| RL | 2 | 2 | 2 | 2 | 2 | 9 / 9 |
| **Total** | **9** | **9** | **9** | **9** | **9** | **45 / 45** |

## Family Evidence

| Family | Domain | Bundle SHA-256 | Fresh run | Retained highest level | Mutations |
| --- | --- | --- | --- | --- | ---: |
| `fir_filter` | Numeric | `2d345802bb8c7ccd202caa44622b2e39ea71885cb38bbdc13c88538b01623904` | L3 | L4 | 5 / 5 |
| `matrix_vector_mac` | Numeric | `ff087b41cab0c4dbd44d7558e7ddd5012875c469fad16427d46eba6b1f10e61b` | L3 | L4 | 4 / 4 |
| `matched_filter` | Signal | `ff396a9aa78f09e316b6a6f3563cfc097e83685155315ac4460245cd581d9262` | L3 | L3 | 4 / 4 |
| `peak_detector` | Signal | `668c707e9133b0eb4ec4801d6ba12552a1a3323c143769835d2a2b45fbb820e3` | L3 | L3 | 3 / 3 |
| `p_pulse_radar_signal` | Signal | `8da72dff4f03eb73d4aa948c2b98e2f7c0be4d6c077719f54693387a97247170` | L3 | L3 | 5 / 5 |
| `sobel_threshold` | Image | `2c61e0e0657b32ea3c09234de8971c1810540dfdc4a9ddc382233d1c2628a2ec` | L3 | L3 | 7 / 7 |
| `p_vision_defect_core` | Image | `db10f9263766ed89db53d36a05e12367080320f7827057a700fa91ff0ee63563` | L3 | L3 | 8 / 8 |
| `qtable_update_core` | RL | `1eb99fdc074868d921bfd996eb89d6bbd3d54ec68a5a2d65ed79f4fa61bb7bbf` | L3 | L3 | 4 / 4 |
| `p_rl_qlearning_accel` | RL | `0d81ef12461af2b560e7061295c906c33cd4f546f2c7abc4371d21c55e49df3b` | L3 | L3 | 5 / 5 |

Every bundle was reloaded with `load_oracle_bundle()`, which recomputes the
canonical bundle and file hashes. Every `evidence.json`, `labels.json`, and
`trajectory.json` agreed on family identity, bundle hash, scenario status, and
the L3 verdict.

## Leakage Audit

The audit scanned all generated export files and the evaluator-local bundles.
Exports contained no `.memh` paths, actual non-public scenario seeds, hidden
input/expected paths, or complete hidden/random/stress vector contents.
Evaluator-local `.memh` files remain under each attempt's trusted oracle folder
and are not model-visible training exports.

## Artifact Roots

- Run summary: `tmp/sr2fpga_phase_c_independent_oracle/runs/phase-c-independent-oracle-20260714-v1/summary.json`
- Sample data: `tmp/sr2fpga_phase_c_independent_oracle/dataset/`
- Training exports: `tmp/sr2fpga_phase_c_independent_oracle/exports/`
- Per-family trajectory: `<sample>/eval/trajectory.json`
- Oracle manifest/evidence: `<sample>/attempts/attempt_000/eval/oracle/{manifest,evidence}.json`
- Mutation evidence: `<sample>/oracle_mutations/`

The implementation plan originally referred to `results.json`; the canonical
runtime artifact is `evidence.json`. The audit rejects obsolete-only
`results.json` evidence.

## Commands

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_independent_oracle.example.yaml --run-id phase-c-independent-oracle-20260714-v1 --preflight
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_independent_oracle.example.yaml --run-id phase-c-independent-oracle-20260714-v1
python -m LLM.src.sr2fpga_agent.task_evidence --output docs/sr2fpga-task-evidence-status.md --audit-run-root tmp
```

## Tool Versions

The run used the locally discovered OSS CAD Suite tools:

- Verilator `5.049 devel rev v5.048-335-g2d157b29b`
- Icarus Verilog `14.0 devel s20260301-220-g78750c51d-dirty`
- Yosys `0.66+154`, git `23aadd92a`

The per-sample `tool_versions.json` currently records these fields as `unknown`;
the versions above were queried directly from the same active executables after
the run. Improving version capture is a recorder follow-up, not a Phase C gate.

## Limitations

- This is one width-8 deterministic sample per family, not a statistical model comparison.
- Phase C validates benchmark independence and oracle strength; it does not claim LLM first-attempt success.
- L4 and L5 were not run in this batch. Only FIR and matrix-vector MAC retain prior dual-tool L4 evidence.
- Hidden vectors are intentionally evaluator-local, so public exports expose hashes and scenario metadata rather than the withheld contents.
