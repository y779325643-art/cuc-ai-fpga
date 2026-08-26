# SR2FPGA Phase D Frozen Multi-Teacher Pilot Report

> **Status: completed named-run evidence snapshot.** Commands and repository
> paths below are preserved as historical provenance and are not current
> operating instructions. Use [current status](../../../docs/current-status.md)
> and the [Paper-1 specification](../../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
> for present gates and commands.

Date: 2026-07-17

Live run: `phase-d-multiteacher-pilot-20260717-v1`

Deterministic control: `phase-d-control-20260717-v1`

Independent audit: `APPROVED`

## Scope

This report closes the frozen 24-episode Phase D pilot. It is an engineering
pilot, not a statistically conclusive model benchmark. The measured unit is a
project episode generated through System-HIS v1.2 and evaluated under the
frozen contract. Model IDs below are gateway-reported identifiers.

The pilot compares four teacher aliases across six byte-identical paired
requirements:

| Source alias | Reported model | Transport kind |
| --- | --- | --- |
| `claude` | `claude-opus-4-8` | Anthropic-compatible SSE |
| `gpt` | `gpt-5.5` | OpenAI-compatible |
| `qwen` | `qwen3-coder-plus` | OpenAI-compatible |
| `deepseek` | `deepseek-v4-pro` | DeepSeek System-HIS v1.2 |

The live provider preflight passed for all four aliases before generation. No
endpoint or credential is recorded in this report.

## Frozen Measurement

- Config fingerprint: `1b6b8ff396f2b29c16c3a6c9f36664aacc71f5fda3e89e574f215fa83928a49b`
- Freeze fingerprint: `17dd62e04fea801d075e9574cf6d89f6fcea3ceb33c974c2888a3f9f042e07c0`
- Planned/completed episodes: 24/24
- Complete four-source pairs: 6/6
- Scoreable model episodes: 24/24
- Unresolved infrastructure outcomes: 0
- Maximum semantic attempts: 3
- OpenXC7 eligibility: final L3-pass `fir_filter` episodes only, at most four

The six families were `sync_fifo`, `valid_ready_stream_accumulator`,
`stream_fork_join`, `fir_filter`, `sobel_threshold`, and
`qtable_update_core`. Requirements and hashes agree within every four-source
pair.

## Deterministic Control

The deterministic controls establish that the experiment plumbing and trusted
oracles work independently of the live model outcomes:

- 6/6 controls passed L0, L1, L2, and L3.
- 6/6 reference projects passed their declared oracle.
- The mutation gate killed 28/28 mutations, mutation score 1.0.
- The FIR control passed OpenXC7 L4; the other five were not selected for L4.
- Raw FIR report:
  `datasets/sr2fpga_phase_d_control_v1/sample_phase_d_control_fir_filter_8_000004/attempts/attempt_000/generated_project/eval/openxc7_nextpnr.log`.
- Raw report lines record `SLICE_LUTX: 30/106400`, placement frequency
  434.03 MHz, and routed frequency 423.37 MHz, both passing the frozen 100 MHz
  target.

These controls validate the measurement infrastructure. They are not LLM
baselines and are excluded from the 24-episode model denominator.

## Live Outcomes

No live episode crossed H2, so none reached L0-L3 tool acceptance:

| Source | Episodes | H2 fail | Generation fail | L0 | L1 | L2 | L3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude | 6 | 1 | 5 | 0 | 0 | 0 | 0 |
| GPT | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| Qwen | 6 | 2 | 4 | 0 | 0 | 0 | 0 |
| DeepSeek | 6 | 3 | 3 | 0 | 0 | 0 | 0 |
| **Total** | **24** | **12** | **12** | **0** | **0** | **0** | **0** |

Family/source outcome matrix:

| Family | Claude | GPT | Qwen | DeepSeek |
| --- | --- | --- | --- | --- |
| `sync_fifo` | H2 fail | H2 fail | generation fail | generation fail |
| `valid_ready_stream_accumulator` | generation fail | H2 fail | generation fail | generation fail |
| `stream_fork_join` | generation fail | H2 fail | H2 fail | H2 fail |
| `fir_filter` | generation fail | H2 fail | H2 fail | H2 fail |
| `sobel_threshold` | generation fail | H2 fail | generation fail | generation fail |
| `qtable_update_core` | generation fail | H2 fail | generation fail | H2 fail |

The strongest conclusion is therefore not about RTL simulation or synthesis.
The current bottleneck is the REQ2HIS/HIS2PROJECT boundary and H2 lowerability.
Representative evidence includes:

- `sample_phase_d_fifo_8_000001`: generated HIS passed H0/H1 but failed H2
  because its free-form verification scenarios were unsupported by the current
  lowerer.
- `sample_phase_d_t6_td_update_core_8_000024`: generated project reached H2
  validation but did not produce a lowerable, tool-eligible episode.
- The remaining rejected episodes preserve model generation failures in their
  `labels.json`, `trajectory.json`, and attempt diagnostics rather than
  reclassifying them as infrastructure errors.

## Initial, Repair, And Regression Measurement

Attempt `(a)` is the first attempt without tool feedback. Final `(b)` is the
state after at most two same-source repairs. In this pilot:

- initial L0/L1/L2/L3 survival: 0/24 at every level;
- final L0/L1/L2/L3 survival: 0/24 at every level;
- tool repair attempts used: 0;
- repair successes: 0;
- regressions: 0;
- patches recorded: 0.

All failures occurred before a project became eligible for tool-feedback
repair. Consequently, this run does not measure repair effectiveness. The
runner's `repair_trajectory` bucket contains 12 H2-failed episodes that retain
structured failure data; it must not be interpreted as 12 executed repairs.

## OpenXC7 L4

The live pilot produced no new L4 verdict because no FIR episode passed L3.
All 24 records still contain an explicit L4 status:

- pass: 0;
- fail: 0;
- not run: 24;
- 20 non-FIR episodes: `disabled_by_config`;
- 4 FIR episodes: `l3_failed`.

This is compliant with the frozen FIR-only policy. It is not evidence that the
live teacher projects achieved physical implementation. The deterministic FIR
control above is the physical-flow validation for this phase.

## Integrity And Audit

The independent audit at
`tmp/sr2fpga_runs/phase-d-multiteacher-pilot-20260717-v1/phase_d_audit.json`
returned `APPROVED` with no blocking finding. It confirmed:

- 24 scoreable episodes and six complete pairs;
- identical requirement hash within every pair;
- `requirement.txt` SHA-256 and metadata source/family/pair/hash agreement with
  every frozen sample entry;
- one consistent freeze fingerprint across all episode metadata;
- complete L0-L3 verdict fields, including upstream-failure outcomes;
- same-source repair policy and per-patch provider provenance when repairs occur;
- FIR-only L4 policy, prerequisite L3 pass, and archived-report rules;
- no unresolved infrastructure outcome;
- no trusted-artifact edit receiving pass credit;
- no credential-like material found by the all-file streaming artifact scan;
  and
- agreement between paired results and summary episode counts.

The exact direct audit command is now covered by a regression test and returns
`APPROVED` from the repository root.

## Independent Acceptance Review

Verdict: **APPROVED**

Blocking findings: none.

The implementation and artifacts satisfy the Phase D acceptance gates. This
verdict concerns completeness, frozen-protocol integrity, traceability, and
auditability. It does not convert failed projects into tool-accepted designs.

## Limitations And Next Gate

- This is one requirement per family and four gateway-reported models.
- No live episode reached L0, so live L1-L3 tools and L2 trusted oracles were
  not exercised; only deterministic controls exercised those paths.
- No semantic repair was eligible, so `(b-a)` remains unmeasured.
- No live OpenXC7 L4 or Vivado reference result was produced.
- H2 currently rejects useful but free-form verification intent that lacks a
  supported lowering profile. Prompt/schema strictness and lowerer coverage
  must be separated before scaling.
- Claude frequently failed strict JSON/project packaging; the other teachers
  exposed different H2 and cross-file lowerability failures. These signatures
  require structured analysis before changing the frozen protocol.

The next authorized step is failure-distribution analysis and a narrowly scoped
REQ2HIS/H2 hardening experiment. A larger Line-B collection or SFT dataset
should not start until that experiment demonstrates that failures are measuring
hardware generation rather than predominantly schema/lowerer mismatch.

## Final Verification

The final repository regression passed with `897 passed, 349 subtests passed`
in 168.49 seconds. The final acceptance command set is:

```powershell
python -m pytest LLM/tests -q
python scripts/audit_phase_d_pilot.py --run-root tmp\sr2fpga_runs\phase-d-multiteacher-pilot-20260717-v1 --output tmp\sr2fpga_runs\phase-d-multiteacher-pilot-20260717-v1\phase_d_audit.json
git diff --check
```
