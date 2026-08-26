# SR2FPGA Phase C Independent Oracle Evidence

> **Status: completed named-run evidence snapshot.** Commands and repository
> paths below are preserved as historical provenance and are not current
> operating instructions. Use [current status](../../../docs/current-status.md)
> and the [Paper-1 specification](../../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
> for present gates and commands.

Generated on 2026-07-16 from the fresh qualification run
`phase-c-independent-oracle-20260716-v2` using
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
| Paper-1 core mutation-qualified | 14 / 14 |
| All mutation-qualified families | 21 |
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
canonical bundle and file hashes. The artifact audit checks the current v2
summary membership, sample metadata family identity, mutation details, bundle
hash, scenario classes, per-scenario seed hashes, and L3 labels against the
matching trajectory. It separately validates the retained FIR and matrix-vector
MAC L4 claims against the historical dual-tool summary, labels, trajectories,
and every referenced OpenXC7/Vivado report path.

## Paper-1 Core Mutation Closure

The catalog-defined `recommended_sets.paper1_core` denominator contains 14
families. Four implemented families lacked artifact-backed mutation evidence in
the previous ledger. Run `phase-c-core-mutation-closure-20260716-v2` closes that
gap without changing the denominator.

| Family | Mutations killed | L3 | Line-A ready |
| --- | ---: | ---: | ---: |
| `single_dual_port_ram` | 3 / 3 | pass | yes |
| `valid_ready_stream_accumulator` | 4 / 4 | pass | yes |
| `stream_fork_join` | 4 / 4 | pass | yes |
| `mac_array` | 4 / 4 | pass | yes |
| **Total** | **15 / 15** | **4 / 4** | **4 / 4** |

Qualification is backed by each mutation directory's `sim_compile.json` and
`sim_run.json`: compilation must pass and simulation must report `TEST_FAIL`.
The accumulator reference now exposes an `accum_ready` backpressure input; its
testbench fills the skid buffer while `accum_ready=0` and verifies that valid and
the running sum remain stable before releasing the held transaction. Its two
stall mutations therefore alter behavior only during a real `valid && !ready`
interval.

After this run all 14 catalog Paper-1-core families are mutation-qualified.
Across the full 71-family catalog, 21 implemented families now carry qualified
mutation evidence.

## Leakage Audit

The audit parses every JSONL export below the audit root and compares its values
against each evaluator-local bundle. It detects withheld seeds serialized as
numbers or decimal strings, normalizes Windows/POSIX path separators, and rejects
complete hidden vectors even when embedded in larger strings. Exports contained
no actual non-public scenario seed, hidden input/expected path, or complete
hidden/random/stress `.memh` vector. Sanitized `seed_sha256` values are retained
in trajectories and training views so runs remain auditable without disclosing the original seeds.
Evaluator-local `.memh` files remain under each attempt's trusted oracle folder
and are not model-visible training exports.

## Artifact Roots

- Independent-oracle run summary: `tmp/sr2fpga_phase_c_independent_oracle_v2/runs/phase-c-independent-oracle-20260716-v2/summary.json`
- Independent-oracle samples: `tmp/sr2fpga_phase_c_independent_oracle_v2/dataset/`
- Independent-oracle exports: `tmp/sr2fpga_phase_c_independent_oracle_v2/exports/`
- Core-mutation run summary: `tmp/sr2fpga_phase_c_core_mutation_closure_v2/runs/phase-c-core-mutation-closure-20260716-v2/summary.json`
- Core-mutation samples: `tmp/sr2fpga_phase_c_core_mutation_closure_v2/dataset/`
- Retained dual-tool L4 summary: `tmp/sr2fpga_line_a_l4_dual_tool/runs/line-a-l4-dual-tool-20260713-v2/summary.json`
- Per-family trajectory: `<sample>/eval/trajectory.json`
- Oracle manifest/evidence: `<sample>/attempts/attempt_000/eval/oracle/{manifest,evidence}.json`
- Mutation evidence: `<sample>/oracle_mutations/`

The implementation plan originally referred to `results.json`; the canonical
runtime artifact is `evidence.json`. The audit rejects obsolete-only
`results.json` evidence.

## Commands

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_independent_oracle.example.yaml --run-id phase-c-independent-oracle-20260716-v2 --preflight
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_independent_oracle.example.yaml --run-id phase-c-independent-oracle-20260716-v2
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_core_mutation_closure.example.yaml --run-id phase-c-core-mutation-closure-20260716-v2
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
- L4 and L5 were not run in either 2026-07-16 batch. Only FIR and matrix-vector MAC retain artifact-backed dual-tool L4 evidence from `line-a-l4-dual-tool-20260713-v2`.
- Hidden vectors are intentionally evaluator-local, so public exports expose hashes and scenario metadata rather than the withheld contents.
