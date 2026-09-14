# SR2FPGA Phase D Failure Analysis And H2 Hardening

> **Status: completed named-run analysis snapshot.** Commands, paths, and next
> steps below are preserved as historical provenance and are not current
> operating instructions. Use [current status](../../../docs/current-status.md)
> and the [Paper-1 specification](../../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md)
> for present gates and commands.

## Scope

This report analyzes the 24 frozen multi-teacher pilot episodes and evaluates a
narrow H2 compatibility hardening. The pilot artifacts were treated as read-only
inputs. No model API was called and no stored verdict was rewritten.

Replay command:

```powershell
python scripts/analyze_phase_d_h2_failures.py `
  --dataset-root datasets/sr2fpga_phase_d_v1 `
  --output tmp/phase-d-h2-hardening-analysis.json
```

## Failure Distribution

The pilot has two equally sized failure stages:

| Final level | Count | Share |
| --- | ---: | ---: |
| `GEN_FAIL` | 12 | 50% |
| `H2_FAIL` | 12 | 50% |

By source:

| Source | `GEN_FAIL` | `H2_FAIL` |
| --- | ---: | ---: |
| Claude | 5 | 1 |
| GPT | 0 | 6 |
| Qwen | 4 | 2 |
| DeepSeek | 3 | 3 |

By task family:

| Family | `GEN_FAIL` | `H2_FAIL` |
| --- | ---: | ---: |
| `sync_fifo` | 2 | 2 |
| `valid_ready_stream_accumulator` | 3 | 1 |
| `stream_fork_join` | 1 | 3 |
| `fir_filter` | 1 | 3 |
| `sobel_threshold` | 3 | 1 |
| `qtable_update_core` | 2 | 2 |

## Generation Failures

The 12 generation failures split into concrete causes:

| Category | Count | Meaning |
| --- | ---: | --- |
| `invalid_json` | 5 | REQ2HIS did not return strict JSON |
| `his_contract_validation` | 2 | Generated HIS violated H1 contract rules |
| `req_his_fidelity` | 2 | Generated HIS changed required interface semantics |
| `rtl_his_cross_check` | 2 | HIS2PROJECT RTL did not realize declared FSM states |
| `behavior_hole_merge` | 1 | Behavior output targeted a non-editable skeleton file |

These are model/generation-boundary failures. They are not H2 checker false
negatives and were not reclassified by this change.

## H2 Failure Structure

All 12 H2 candidates passed H0 and H1. Before hardening, their diagnostics were:

| H2 category | Diagnostic occurrences | Affected samples |
| --- | ---: | ---: |
| unsupported scenario | 54 | 12 |
| unsupported semantic kind | 31 | 11 |
| unsupported protocol | 18 | 6 |

Eleven candidates used structured scenario objects. The old checker converted
each complete object to a Python string before comparing it with the canonical
scenario set. One candidate used free-form scenario strings. This mixed a real
unsupported-profile decision with an avoidable representation mismatch.

The semantic-kind and protocol failures also exposed a prompt/gate mismatch:
the REQ2HIS prompt required these fields but did not expose H2's canonical
vocabulary.

## Implemented Hardening

The change remains fail-closed:

1. Scenario strings are read directly. Scenario objects use canonical `kind`,
   falling back to `name`; objects missing both are rejected with a concise
   diagnostic.
2. Only reviewed aliases are canonicalized. Examples include
   `synchronous_fifo -> fifo`, `stream_buffer -> buffer`,
   `stream_accumulator -> accumulator`, `combinational -> wire`, and
   `registered_data -> register`.
3. Unknown semantic kinds, protocols, and scenario identifiers still fail H2.
4. Initial and retry REQ2HIS prompts now publish the exact canonical H2
   vocabularies and scenario-object rule.

## Frozen Replay Result

The same 12 H2 candidates were replayed against the hardened validator:

| Metric | Before | After |
| --- | ---: | ---: |
| H2 pass | 0 | 0 |
| H2 fail | 12 | 12 |
| unsupported scenario occurrences | 54 | 54 |
| unsupported semantic-kind occurrences | 31 | 21 |
| unsupported protocol occurrences | 18 | 9 |
| samples with semantic-kind errors | 11 | 8 |
| samples with protocol errors | 6 | 2 |

No frozen sample changed to H2 pass. This is the expected conservative result:
all 12 still contain at least one scenario without a canonical lowering profile.
The hardening removes demonstrably equivalent label mismatches but does not
pretend that free-form verification intent has been lowered into a trusted
testbench.

Remaining semantic labels include `arithmetic`, `datapath`, `control`,
`streaming_fir_filter`, `fixed_point_multiplier`, and other architecture-specific
terms. Remaining protocols are `ready`, `sampled_sideband`, and
`pipeline_sideband`. These require a capability decision, not automatic aliases.

## Interpretation

The 24-pilot bottleneck is not one issue:

- 50% fail before a valid project candidate exists;
- 50% produce structurally valid HIS but cannot satisfy the current canonical
  lowerability profile;
- scenario-profile mismatch is universal across the H2 half;
- no live sample reaches RTL tool evaluation, so the pilot still provides no
  evidence about L1-L4 model performance or repair effectiveness.

The small H2 change improves diagnostic precision and future prompt compliance,
but correctly does not manufacture tool-eligible samples from the frozen run.

## Next Experiment

Run a new, small paired retry using the same six requirements and frozen model
settings, with the hardened prompt and validator code. Keep the original pilot
as the baseline. The next gate should require:

1. fewer `GEN_FAIL` and H2 vocabulary mismatches;
2. at least one generated candidate reaching L0;
3. no increase in H1 contract or H3 fidelity failures caused by prompt changes;
4. separate reporting of canonical scenario compliance versus actual L2 oracle
   coverage.

Do not start a larger Line-B collection until the small retry demonstrates that
the bottleneck has moved from schema/lowerer vocabulary toward RTL behavior and
tool-verifiable failures.
