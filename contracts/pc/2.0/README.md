# Project Contract 2.0 — superseded design candidate

> **Superseded (2026-09-15).** PC 2.0 was never adopted. `sr2fpga-pc-2.1` is the
> current Project Contract serialization; see [`../2.1/`](../2.1/) and the
> [PC 2.1 design](../../../docs/specs/PC-2.1-AI-stream-contract-design.zh.md).
> These schemas are retained because PC 2.1 cites them as its drafting base.

Machine format `sr2fpga-pc-2.0`. Design document:
[`PC-2.0-clean-slate-design.zh.md`](../../../docs/specs/superseded/PC-2.0-clean-slate-design.zh.md)
(Chinese, 2026-09-14).

> **Not adopted. Not registered. Consumed by nothing.**
> These schemas are deliberately absent from
> [`contracts/manifest.json`](../../manifest.json), so `ContractRegistry` cannot
> resolve them and no runtime path reads them. Registering them would mean
> adopting the format, which also retires System-HIS v1.2.
> [System-HIS v1.2](../../system-his/) remains the serialization of historical
> artifacts. Current work uses PC 2.1 as linked above.

## Files

| File | Role |
| --- | --- |
| `design-proposal-2.0.schema.json` | Validates the **model-authored** design projection — the part a model is allowed to produce |
| `project-contract-2.0.schema.json` | Validates the **complete PC** after the trusted controller has injected immutable bindings |

The two share one design definition. They are not a lax format and a strict
format, and they are not two competing PC formats.

## Why a clean slate

The candidate splits what the old serialization merged. A PC becomes *typed,
hierarchical architecture decisions bound to frozen requirements* — not a
container that also holds a requirement database, build log, and evaluation
results. It drops `verification.pass_condition`, `artifacts.predicted_qor`,
duplicated file lists, measured resources, direct script paths, and
compatibility aliases from the required core.

It is **incompatible with System-HIS v1.2 by design** and ships no aliases,
converter, or lenient entry path. Historical v1.2 documents and results stay
archived for interpretation; nothing overwrites their original evidence
identity.

## What is and is not implemented

Section 12 of the design document is the authority. Summarised:

| Layer | Status |
| --- | --- |
| Strict JSON parsing (duplicate keys, non-finite literals, size/depth) | reference implementation |
| JSON Schema (closed objects, discriminated unions, bounded expression grammar) | both files meta-validated |
| Reference and instance expansion (module/port/parameter/domain/fact refs, recursion, reachability) | reference implementation |
| Static structural semantics (type match, direction, drivers, point-to-point streams, no implicit cross-domain, state/parameter ranges) | reference implementation |
| Behavioural and requirement conformance (algorithm, protocol, storage events, numeric and timing commitments) | **not implemented** |
| Build and edit boundary (RTL emitter, real source manifest, AST checks, repair scope) | **not implemented** |
| EDA and physical (lint, simulation, synthesis, timing, mapping, board) | **not executed** |
| Runtime security and authorization (sandbox, trusted registration, signing, event and hidden isolation) | **not wired into the project** |

The reference static checker itself and the two illustrative project contracts
described by the design document are **not present in this checkout** — only
these two schemas are.

## A schema-valid contract is not a correct design

Section 12.1 of the design states it directly: a project can be schema-valid,
graph-legal, and interface-type-consistent while implementing the wrong
algorithm. `intent`, `numeric_rules`, `timing`, and `requirement_map` cannot
prove themselves. Structural benefit has to be measured by `M4-M3` and by the
change in error classes; overall correctness stays with the shared independent
oracle, and the PC-based methods get no looser standard than the controls.

Keeping source and output paths out of the PC also does not make a candidate's
RTL trustworthy. The emitted FPP is still handled as untrusted input.

## Local evidence

[`reports/conformance.json`](../../../reports/conformance.json) — 70 cases, 0
failures, 0 errors, scoped to "local static schema/checker conformance; NOT HDL
or benchmark results". The design document's `[T0]` additionally cites
`reports/stream_static_report.json` and `reports/comb_static_report.json`;
neither is present.

## Relationship to the research plan

The candidate treats
[`paper1-v2.1`](../../../docs/specs/superseded/2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md)
as its upstream scope authority and answers the field-mapping obligation that
section 3.1 of that plan defers to implementation. **A PC format version is not
a research plan version.** The candidate adds no training, does not re-enable
the EA extension, and changes no family, hypothesis, or budget.

Its own section 1.1 carries the consequence: a PC format change is a method
version change, so earlier experiment results and earlier checker pass records
do not carry over automatically.
