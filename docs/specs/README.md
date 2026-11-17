# SR2FPGA Research Specifications

> [Terminology, 2026-09-08](2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> now serialized as `sr2fpga-pc-2.1`; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

Use the task-based routes in the [documentation map](../README.md). Read
[current status](../current-status.md) first only when interpreting current
implementation, verification, debt, or results. Migration progress toward the
current plan is in the
[migration record](../migrations/research-plan-alignment.md).

## Current Paper-1 Authority

- [Paper-1 LLM case amendment v2.3](2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) — **current case and population authority**, adopted 2026-10-28, not frozen.

The current plan is the v2.3 amendment together with the v2.2 base text. QKV
projection, KV-cache decode attention and gated FFN replace the earlier three
AI families; inherited methods, metrics, budgets and evidence rules remain.
The earlier adoption description below is retained as the base-plan record.

- [Paper-1 research plan v2.2](2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md) — base authority except the case/population clauses superseded by v2.3; Chinese, adopted 2026-09-15

`paper1-v2.2` governs the ACM TRETS target, research questions, M0-M5 method
conditions, information boundaries, metrics, statistics, work packages, and
claim rules. Paper-1 does not train models.

| | |
| --- | --- |
| Task population | Three LLM inference subsystems: `llm_quantized_qkv_projection`, `llm_kv_cache_decode_attention`, `llm_gated_ffn`, under v2.3 |
| Primary comparisons | `M5-M1@B4` and `M4-M3@initial`, in one Holm family, one-sided FWER 0.05 |
| Budget | `B4` — matched total logical model calls, plus matched token/tool/time axes |
| Independent unit | `design_cluster_id`; configurations and replicates nest inside it |
| Default-disabled | A_req requirement audit, EA search, model training, Q-table, board bring-up |
| Planned secondary | Native coding-agent comparison (C0/C1), second model, tensor-check ablation, natural-failure repair probe |

Adoption fixed the research direction **and authorized repository migration**.
Official-experiment authorization was recorded separately and **was not
granted**; this plan is not frozen. See its section 21 for the adoption record
and the five items confirmed open at adoption time.

The Chinese file is the authoritative text. The v1.8 convention that English
governs ended with that version; an English counterpart is required before
publication and does not yet exist.

## Current Code-Development Specification

- [Paper-1 code architecture and development specification v2.1](2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md) — `sr2fpga-paper1-code-dev-v2.1`, adopted 2026-09-15

This subordinate specification maps the research protocol to code modules,
interfaces, state machines, artifacts, work packages, and acceptance tests. It
does not modify the estimand, method privileges, work-package order, or outcome
rules.

It describes a **target** architecture, not the current checkout. Where the
repository and this spec disagree, record `implementation_protocol_drift` and
consult the migration record; do not change research obligations to match code.

## Current Project Contract Format

- [PC 2.1 AI-stream contract design](PC-2.1-AI-stream-contract-design.zh.md) — machine format `sr2fpga-pc-2.1`, adopted 2026-09-15
- [PC 2.0 to PC 2.1 implementation delta](../migrations/IMPLEMENTATION_DELTA.zh.md) — target change list for checker, ABI, cache invalidation and evaluation boundaries

PC 2.1 adds tensor, quantization, sequence, and bounded-relation semantics for
quantized AI datapaths. It **replaces System-HIS v1.2 and PC 2.0** and provides
no reader, alias, or conversion path for either.

Both schemas are registered in [`contracts/manifest.json`](../../contracts/manifest.json)
and live at [`contracts/pc/2.1/`](../../contracts/pc/2.1/):
`project_contract_2_1` binds `schema_version: sr2fpga-pc-2.1`, and
`design_proposal_2_1` binds `$id: urn:sr2fpga:pc-design:2.1`.

**Implementation status.** The current `pc/` package implements typed public
loading, configuration-level static checks, tensor ABI, deterministic structure
construction and real-parser-protected behavior composition. See the
[development guide](../../agent/src/sr2fpga_agent/pc/README.md) and
[LLM case guide](../../agent/src/sr2fpga_agent/tasks/README.md). These do not
establish family qualification. `reports/conformance.json` remains a historical
PC 2.0 report and is not the evidence for current PC 2.1 behavior.

`system_his` remains registered so existing artifacts stay readable. New runtime
paths must not use it.

## Retained Narrow Semantic Authority

- [DSC / DP / PC / FPP terminology ledger](2026-09-08-sr2fpga-terminology.md) — naming only; not implementation or experiment authority

## Superseded

Everything that previously appeared in this index as current — the `paper1-v1.8`
and `paper1-v2.1` plans, the `v1.12` and `v2.0` code-architecture specs, the
System-HIS v1.2 semantic spec, the PC 2.0 design, and the 2026-09-11 PC study
designs — now lives in [`superseded/`](superseded/README.md) with its status and
the reason it is retained.

Version labels inside historical QA reports, writing aids, and dated audits
describe the state at the time of writing and are deliberately not rewritten.
This directory holds normative research, semantic, and code-design
specifications only; transient task plans and experiment results belong
elsewhere.
