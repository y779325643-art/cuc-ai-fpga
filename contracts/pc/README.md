# Project Contract formats and legacy decision interface

## Choose a format

| Entry | Role |
| --- | --- |
| [PC 2.1 schemas](2.1/) and [development command guide](../../agent/src/sr2fpga_agent/pc/README.md) | Registered format, typed development public sources, listed static semantic checks, deterministic RTL structure and parser-protected behavior composition; functional correctness requires execution |
| [PC 2.0](2.0/README.md) | Superseded, unregistered design candidate retained as a drafting reference |
| [System-HIS v1.2](../system-his/) and decision interface below | Retained legacy formats and development tools for historical artifacts |

## Legacy PC decision interface v1

This opt-in development interface implements the
[field responsibility design](../../docs/specs/superseded/2026-09-11-pc-field-responsibility-v1.md).
It does not replace System-HIS v1.2 or relabel historical M0–M5 data.

These are the **registered** PC interface contracts and they operate on the
legacy System-HIS v1.2 serialization. The separate
[PC 2.0 design candidate](../../docs/specs/superseded/PC-2.0-clean-slate-design.zh.md) in
`contracts/pc/2.0/` was superseded by PC 2.1. PC 2.0 was not adopted or registered
in `manifest.json`. The PC 2.1 input command does not read older formats;
the legacy commands below do not assemble PC 2.1 inputs.

## Contracts

- `pc-decisions-v1.schema.json`: model-owned `decisions` and named `fact_bindings`.
  Its version is host-owned `x-contract-version` metadata, not a writable payload
  field. Unknown fields and old complete-PC payloads are rejected.
- `pc-assembly-execution-v1.schema.json`: observed invocation/failure information
  bound to immutable raw response, public context and platform refs.
- `pc-assembly-record-v1.schema.json`: replayable derived result, raw/source refs,
  field/binding provenance, failure stage, PC and H-validation refs, and source
  fingerprints. It grants no experiment or pass-credit authority.

The model chooses architecture, state owners, source layout, behavior declarations
and semantic binding targets. The host copies frozen identity/facts and acceptance
obligations, derives `owns_state` and artifact paths/inventories, and encodes named
bindings as RFC 6901 pointers. Array order is retained. Unknown/ambiguous names,
reserved path collisions and missing or host-controlled binding keys are errors.
Unknown optional facts remain in the frozen input; they are not filled with zeros.

Input v1 is deliberately closed. Only the fields declared in the decision schema
are supported; legacy extension fields must not be silently dropped or enabled.
An interface extension needs a reviewed schema/version update. This is not a claim
that every legacy PC variant has been ported or that a model cannot produce errors.

## Offline CLI

Use a verified development/excluded episode pack, its matching platform JSON,
and a saved model decision response. The output root must be fresh and below
repository `artifacts/`:

```powershell
python -m sr2fpga_agent.pc_assembly --episode-pack <episode-pack.json> --platform <platform.json> --response <decision-response.json> --output-root artifacts/<fresh-run>
python -m sr2fpga_agent.pc_assembly --output-root artifacts/<fresh-run> --verify pc-interface/attempt-000/record
```

Assembly exits 0 only for `pc_valid`; failed inputs still produce records and exit
1. Successful `--verify` exits 0 even for a faithfully recorded failed attempt.
No model, simulator, synthesis, deployment or package-installation command is run
by this CLI. H2 uses the existing in-memory dry materializer.

## Programmatic use

`assemble_pc(context, platform, raw_response)` returns a non-mutating result.
`record_pc_assembly(store, attempt_id, context, platform, raw_response)` records an
offline attempt. `PCDecisionGenerator(client, platform, store).generate(context,
attempt_id)` makes at most one logical client invocation and records the result.
It does not construct a provider client, load credentials, add retries, or modify
old Runner defaults. Paid use still needs caller authorization and budget control.
Provider transport retries are the client's responsibility; invocation counts
are not HTTP counts or billing proof.

An atomic retained attempt claim prevents reusing an attempt ID from dispatching
again. A process interruption can leave a claim and source inputs without a final
record; this is incomplete, not a success and not permission to silently retry.
Code/contract drift during model invocation or assembly prevents result commit.
Replay requires the recorded source/runtime fingerprint and rebuilds the result
from the immutable execution and input records. It is artifact-integrity checking,
not independent attestation that a remote provider was used.

`pc_valid` means the assembled PC passed existing H0–H3 checks. It does not mean
the corresponding FPP is functionally correct, physically implemented or eligible
for official VPP credit. The 2×2 study runner and its operational freeze are separate
work; this interface alone does not authorize or execute that study.
