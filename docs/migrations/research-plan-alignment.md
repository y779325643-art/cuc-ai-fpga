# Research Plan Alignment: `paper1-v1.8` to `paper1-v2.2`

Current case binding is `paper1-v2.3` / `llm_inference_subsystems_v1`.
See the [adopted amendment](../specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md)
and [LLM implementation/validation record](llm-case-migration-20261028.md).
The v2.2 alignment history below retains its original families and evidence;
none of its results transfers to LLM cases.

The [PC2.1 runtime/analysis implementation record](pc21-runtime-implementation-20261028.md)
now records the separately authorized software-infrastructure work. It adds no
official results or experiment authorization to the dated history below.

The [PC2.1 runtime/analysis implementation record](pc21-runtime-implementation-20261028.md)
now records the separately authorized software-infrastructure work. It adds no
official results or experiment authorization to the dated history below.

Living migration record. It is updated in place as batches land; it is not a
per-session report. It records what was audited, what was decided, what was
actually changed, and what remains.

> ## Target: `paper1-v2.2` (adopted 2026-09-15)
>
> The user adopted [`paper1-v2.2`](../specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md),
> [code-architecture spec `v2.1`](../specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md),
> and [`sr2fpga-pc-2.1`](../specs/PC-2.1-AI-stream-contract-design.zh.md) on
> 2026-09-15, and **authorized repository migration**. Official experiments were
> **not** authorized and the plan is not frozen.
>
> Sections 1-9 below record the completed `v1.8` to `v2.1` migration and remain
> valid history; section 3's target baseline is superseded where v2.2 differs.
> Section 10 reviewed v2.2 before adoption; section 11 records the v2.2
> migration itself; section 12 is the current continuation and completion assessment.

## 1. Authority

| Item | Value |
| --- | --- |
| Current research authority | [`paper1-v2.1`](../specs/superseded/2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md) |
| Declared status in that file | `当前 Paper-1 研究计划权威`, adopted 2026-09-14 by the user |
| Explicitly **not** granted by adoption | freeze, implementation authorization, official-experiment authorization (plan sections 0.3, 16.3) |
| Language authority | Chinese. The v1.8 "English governs" rule lapsed with v1.8; an English counterpart is a pre-publication obligation (plan section 16.3) |
| File SHA-256 at audit time | `0e5fea5605d893204c0c1a80bc97f06e403ced33ae3e4b1f3074cbfdae61a877` |
| Repository state at audit start | branch `develop`, HEAD `e20dfd2c`, working tree dirty (37 entries) |

Authority was established by reading the file's own status declaration, not by
filename date or version ordering. Two same-dated neighbours were checked and
are **not** authority:

| Neighbour | Declared status | Consequence |
| --- | --- | --- |
| [`PC-2.0-clean-slate-design.zh.md`](../specs/superseded/PC-2.0-clean-slate-design.zh.md) | `pc-2.0-design-candidate` | Not adopted. Verified absent from `contracts/manifest.json` (0 matches). System-HIS v1.2 remains the current PC serialization |
| [`...code-architecture-development-spec-v2.0.zh.md`](../specs/superseded/2026-09-14-sr2fpga-paper1-code-architecture-development-spec-v2.0.zh.md) | `sr2fpga-paper1-code-dev-v2.0-draft` | Draft. Targets PC 2.0, so it inherits PC 2.0's unadopted status |

The v2.0 architecture draft records the plan's hash as
`2da34c3bf557bb65c36663f2b79ca34871f05dc2760b0a8830e80a61e42ecd14`, which does
not match the current bytes. The draft was written against a different state of
the plan; it is not a synchronized subordinate spec.

## 2. Scope of this migration

In scope: aligning repository research authority, development instructions,
active documentation, the live code references to superseded authority, and the
WP0 inventory that plan section 13 places first.

Out of scope, with reasons:

- **Adopting PC 2.0** — unadopted design candidate; a PC format change is a
  method version change that invalidates prior checker and experiment pass
  records (PC 2.0 design section 1.1). This is a research decision, recorded as
  blocker **B1**, not made here.
- **Migrating to the v2.0 architecture draft** — depends on B1.
- **Running models, official evaluation, synthesis, place-and-route, or any
  paid campaign** — not authorized by the plan or by this task.

## 3. Target baseline extracted from `paper1-v2.1`

Tracking IDs are engineering handles only. They create no research definition;
each cites the plan section that governs it.

| ID | Requirement | Plan |
| --- | --- | --- |
| TB-01 | Core chain: frozen public requirement facts, then PC or Direct, then full multi-file FPP, then budgeted public check/repair, then a single sealed terminal candidate, then independent hidden evaluation, then designated L3, then a pre-declared L4 subset | 1.2 |
| TB-02 | Two primary comparisons, `M5-M1@B4` and `M4-M3@initial`, in **one** Holm family, one-sided FWER 0.05 | 6.1, 9.5 |
| TB-03 | Budget fairness is **B4**: at most 4 logical model calls per independent method, plus matched token / tool-call / runtime / EDA axes. Not matched repair counts | 6.4 |
| TB-04 | M0-M5 definitions and their shared-start pairing (`M0/M1` Direct initial, `M3/M4` initial PC, `M4/M5` initial checkpoint) | 6.2, 6.3 |
| TB-05 | Three shared-start **kinds** by outcome: `pc_failure_checkpoint`, `project_failure_checkpoint`, `project_checkpoint`; shared failures stay shared | 5.2 |
| TB-06 | The G0-G9 / CD1-CD10 gate sequence is replaced by seven work packages WP0-WP6 | 13 |
| TB-07 | Requirement audit (A_req / RQ0), EA search (RQ5), and target-profile adaptation are optional extensions, **disabled by default**, and non-blocking | 1.3, 12 |
| TB-08 | No generation-model training in Paper-1. Retained training code may stay but must not enter core dependencies, model selection, results, or release obligations | 1.3 |
| TB-09 | Every formal family needs an evaluator-owned oracle independent of the candidate PC, candidate testbench, and candidate RTL | 7.5 |
| TB-10 | Two orthogonal hidden fields, `hidden_execution_status` and `hidden_semantic_status`; exactly one semantic submission per `(campaign, instance, replicate, method)` | 8.3 |
| TB-11 | Application constraints enter as sourced public requirement facts carrying source, obligation role, applicability, verification responsibility, and actual result | 3.5 |
| TB-12 | The six evidence dimensions are withdrawn independently; `VPP-L3` never widens to mean full application compliance | 1.4, 3.6, 9.1 |
| TB-13 | Catalog intent is not capability. The WP0 family inventory must use the evidence ledger and real artifacts, not catalog fields | 16.4 |

## 4. WP0 inventory: verification of plan section 16.4

The plan pre-recorded six catalog/ledger inconsistencies. All six were
re-verified directly against
`contracts/task-catalog/sr2fpga-task-catalog-v0.2.json` (71 families) and
`reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json` (71 families,
identical id set).

| # | Plan claim | Verified result |
| --- | --- | --- |
| 1 | 64 `ready`, 9 with independent-oracle evidence, 40 `golden_model_status: none` | **Confirmed.** 64 / 9 / 40 exactly |
| 2 | Two `paper1_core` definitions disagree, 9-family difference | **Confirmed.** 21 family-level versus 14 in `recommended_sets`; symmetric difference 9 (8 one way, `qtable_update_core` the other) |
| 3 | `p_pulse_radar_signal` marks itself `paper1_core` but is absent from the recommended set | **Confirmed** |
| 4 | `l4_representative_subset` contains `conv2d_core`, which is `future` and never run; only `fir_filter` and `matrix_vector_mac` are `l4_open_status: pass` | **Confirmed** |
| 5 | `core_modules` is unfilled for families that demonstrably generate multiple RTL files | **Confirmed**, with one correction: the field is a **list**, and the unfilled value is `[]`, not `0`. `matched_filter`, `matrix_vector_mac`, `fir_filter`, and `stream_fork_join` are all `[]`; `sobel_threshold` and `uart_fifo_loopback` are populated. The field remains unusable for judging project structure |
| 6 | The three core physical families have no L4 evidence | **Confirmed.** `stream_fork_join`, `matched_filter`, and `sobel_threshold` are all `l4_open_status: not_run`, `highest_verified_level: L3` |

### 4.1 Additional finding not in section 16.4

**The four primary test families do not currently meet TB-09.**

| Family (plan section 7.1) | `golden_model_status` | Independent-oracle evidence | TB-09 today |
| --- | --- | --- | --- |
| `uart_fifo_loopback` | `embedded_sv` | **absent** | **not met** |
| `stream_fork_join` | `embedded_sv` | **absent** | **not met** |
| `matched_filter` | `python_reference` | present | met on current record |
| `sobel_threshold` | `python_reference` | present | met on current record |

Two of the four main-result families carry only a SystemVerilog golden model
embedded alongside the candidate testbench. Plan section 7.5 requires an oracle
independent of the candidate testbench and forbids treating a design and its own
testbench as mutual proof. Both families are nonetheless marked
`oracle_readiness: ready` in the catalog, which is the same over-claim as
section 16.4 item 1, now landing on the primary result set. Recorded as blocker
**B2**.

### 4.2 Identifiers named in plan section 7.6

The plan asked that these be checked rather than assumed. All five exist in both
catalog and ledger:

| Identifier | `implementation_status` | `benchmark_role` |
| --- | --- | --- |
| `p_vision_defect_core` | `implemented_current` | `eval_subset` |
| `p_rl_qlearning_accel` | `implemented_current` | `flagship` |
| `p_pulse_radar_signal` | `implemented_current` | `paper1_core` |
| `p_simple_cnn_pipeline` | `future` | `eval_subset` |
| `t9_host_protocol_shell` | `implemented_current` | `flagship_candidate` |

Existence is not capability. Per section 7.6 none of these is certified against
the v2.1 task-card requirements; their algorithms, interfaces, and oracles are
unaudited here.

## 5. Migration matrix

| Asset | Requirement | Current behaviour / old assumption | Disposition | Rationale |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | TB-06, TB-07 | `[paper1]` already resolves to v2.1; `[architecture]` resolves to the v1.12 spec without a caveat | **ADAPT** | v1.12 is an unsynchronized subordinate spec; the link needs a status caveat, not removal |
| `README.md`, `docs/README.md`, `docs/specs/README.md`, `docs/current-status.md` | TB-01 to TB-07 | Already point at v2.1 and already mark v1.8 superseded | **KEEP** | Landed in the pre-existing uncommitted work; re-verified correct |
| `agent/src/sr2fpga_agent/g3_test_evidence.py` | TB-06 | Binds the **superseded** v1.8 spec into the evidence source fingerprint | **ADAPT** | Live code treating retired authority as a required document |
| `docs/specs/superseded/2026-09-11-pc-layered-study-design-v1.md` | TB-06 | Cites the v1.8 spec as `Paper-1 规范` for current authority | **ADAPT** | Active design doc routing readers to retired authority |
| `docs/specs/2026-09-08-sr2fpga-terminology.md` | TB-06 | Same stale citation | **ADAPT** | Same |
| `.../foundation/canonical-citation-registry.md` | TB-06 | Declares itself "active ... canonical `paper1-v1.8`" | **ADAPT** | Self-declared active status is now false |
| `.../writing/v1.9-discussion-ledger-and-next-chat-handoff-2026-09-10.md` | TB-06 | States "`paper1-v1.8` remains the canonical research specification" | **ADAPT** | Handoff document; highest risk of re-injecting retired authority into a later session |
| `.../writing/contract-guided-evolutionary-dse-v1.9-candidate.md` | TB-06, TB-07 | Asserts v1.8 canonical; EA proposal | **ADAPT** | EA is now an optional disabled extension |
| `docs/superpowers/{plans,specs}/2026-08-29-g3b-*` | TB-06 | Written against `paper1-freeze-v1.7` | **ARCHIVE** | Completed design/plan records for a retired gate |
| `contracts/**` fields `g3_accepted`, `g4b_authorized`, `rq1_evidence`, `rq2_evidence` | TB-06 | 289 occurrences across 39 files; all are `const: false` negative guards | **KEEP as identifiers** | Renaming invalidates registered schemas and recorded artifacts for zero semantic change; plan section 14.1 prefers reusing registered contracts and section 16.1 preserves identifiers with a mapping. `contracts/README.md` already documents this |
| `agent/src/.../g3_acceptance.py`, `g3_test_evidence.py` (module names) | TB-06 | G3 gate vocabulary | **KEEP as identifiers** | Same rationale; they implement a still-required development/official boundary |
| `method_contract.py` field `budget_allocation_id` | TB-03 | Labels `paper1-at1-v1` / `paper1-two-stage-v1` / `paper1-online-repair-v1` with **no registry binding them to numbers** | **ADD** | B4 is not implemented. The budget mechanism (`ModelCallBudget`, standalone versus `paired_block_exclusive`) exists and is shape-compatible, but no B4 allocation is registered |
| `block_preparation.py` enum `CheckpointId` | TB-05 | Three checkpoints by *artifact* (`direct_initial_project`, `shared_system_his`, `skeleton_initial_project`), each carrying a `failed` status | **ADAPT (deferred)** | Orthogonal to the plan's three kinds *by outcome*. Needs a mapping, not a rewrite. Depends on B1 |
| `contracts/system-his/**`, `system_his_v12_checker.py` | section 3.1 | Current PC serialization | **KEEP** | Explicitly retained until PC 2.0 is decided (B1) |
| `contracts/pc-2.0/**` (untracked) | — | Unregistered schemas | **HOLD** | Do not register; blocked on B1 |
| `requirement_audit.py`, `ambiguity_*` modules and contracts | TB-07 | Implements RQ0 / A_req | **KEEP, disabled** | Plan section 12.1 keeps A_req as an optional extension, default off. Section 16.1 says retain, do not delete |
| `target_profile_pairs.py` | TB-07 | Target-profile adaptation | **KEEP, disabled** | Section 12.4 |
| `task_families/ga.py` | TB-07 | EA-adjacent | **KEEP, disabled** | Section 12.2 |
| `training/**`, `training_*.py`, training contracts | TB-08 | Retained training infrastructure | **KEEP, out of core** | Section 1.3 permits retention outside core dependencies |
| `contracts/task-catalog/sr2fpga-task-catalog-v0.2.json` | TB-13 | Six verified inconsistencies (section 4 above) | **UNRESOLVED** | Correcting the field values is a research-scope decision about which families are `paper1_core`; recorded as **B3** |
| `reports/evidence/legacy-runs/**` | section 16.1 | Historical run evidence | **ARCHIVE** | Preserved unchanged; not upgradeable to v2.1 evidence |

### 5.1 Code-level reuse verdicts

Verified against `agent/src/sr2fpga_agent/` (106 modules). "Verified" below means
the module was read and checked against the cited plan clause, not merely listed.

**KEEP — already matches a v2.1 clause, reuse as-is**

| Module | Clause | Evidence |
| --- | --- | --- |
| `hidden_execution_state.py` | TB-10 / 8.3 | Implements both orthogonal axes. `completed` is rejected unless the semantic status is exactly `pass`/`fail` *and* the raw evaluator outcome agrees; any non-completed status is rejected unless the semantic status is `None`. Idempotent commit recovery present |
| `terminal_selection.py` | 6.5 | "Select earliest accepted candidate, otherwise the last complete candidate" — the clause verbatim, fail-closed |
| `cost_accounting.py` | 6.4, 9.4 | 13 axes including `logical_model_calls`, input/output/cached tokens, `public_tool_calls`, `wall_time`, `eda_time` — exactly the axes B4 must bind |
| `paired_cost_views.py` | 9.4 | The three required views: actual, standalone-attributed, incremental |
| `model_budget.py` | 6.4 | Event-sourced call accounting with `standalone` vs `paired_block_exclusive` scopes; B4 wired onto it in Batch B without modification |
| `block_preparation.py`, `paired_block.py`, `block_cost_accounting.py` | 6.3 | Shared paired-block machinery. Its `_SHARED_INITIAL_CALL_CEILING` composes correctly with B4 — see below |
| `path_safety.py` | 4.3, 8.2 | Candidate-as-untrusted-input validation, directory-escape prevention, and edit-surface enforcement (`_is_model_editable`, `_rtl_edit_surface_respected`, `_is_trusted_artifact`) |
| `frozen_context.py`, `requirement_boundary.py` | 5.4, 12.1 | Method-neutral requirement disposition before dispatch; visibility-safe episode pack |
| `artifact_store.py`, `contract_registry.py`, `recorder.py` | 8.5, 14.1 | Hash-bound append-only artifacts and registered-format resolution |
| `oracles/*`, `oracle_runner.py` | 7.5 | Evaluator-owned oracle framework with scenario classes and mutation evidence |
| `method_contract.py`, `method_adapters.py`, `generation/*` | 6.2 | The closed M0-M5 vocabulary and its generation paths |
| `tool_runner.py`, `tool_environment.py`, `l4_tool_environment.py`, `openxc7_report.py`, `vivado_report.py` | 11 | Physical-evidence tooling and provenance |

B4 composes with the existing sharing structure without touching it:

```
M    B4 total  shared  exclusive   plan 6.4 remaining
M0          1       1          0                    0
M1          4       1          3                    3   <- "at most 3 repairs"
M5          4       2          2                    2   <- "at most 2 corrections"
```

**ADAPT — reusable core, needs work**

| Module | Gap |
| --- | --- |
| `block_preparation.py` `CheckpointId` | Three checkpoints by *artifact*; section 5.2 defines three by *outcome*. Needs a derived mapping (TB-05), not a rewrite |
| `rtl_introspect.py` | Regex-based port/parameter/module extraction. Section 4.2 wants AST/elaboration checking for the bounded structural guarantee. Usable as a helper, insufficient as the acceptance check |
| `contract_skeleton.py`, `generation/his2project.py` | The deterministic builder exists, but has no origin attribution and has not been audited for hidden family-specific behaviour — section 17's "lowerer 实质藏入答案" risk |
| `system_his_*.py` (8 modules) | Current PC serialization; retain until B1 |
| `task_catalog.py`, `task_evidence.py` | Code is sound; the *data* carries the six section 16.4 inconsistencies (B3) |

**ADD — required by v2.1, absent from the repository**

| Missing | Clause | Verified |
| --- | --- | --- |
| `construction_origin_map` | 4.4 | No match in `agent/src` or `contracts`. `frozen_context.py`'s `origin_map` is requirement-fact provenance, a different object. Without it, M4-M3 cannot be attributed between trusted structure and model behaviour |
| Statistical analysis (cluster bootstrap, Holm, the two hypotheses) | 9.5, 9.6 | No match for `bootstrap`, `Holm`, `studentized`, or `familywise` anywhere in `agent/src`, `training/src`, or `contracts`. Section 9.6 also requires unit tests on synthetic tables; none exist |
| B4 token / tool / runtime / EDA ceilings | 6.4, appendix A | Modelled as `unresolved_axes` in Batch B; values still to be measured |
| Application task cards | 7.12, appendix C | Not started |

## 6. Blockers

Blocking items require a research decision and are **not** resolved here.

**B1 — Is PC 2.0 adopted?**
`contracts/pc-2.0/` ships two schemas with no conversion layer and no runtime
consumer; `docs/specs/superseded/PC-2.0-clean-slate-design.zh.md` states outright
incompatibility with System-HIS v1.2. The v2.0 architecture draft assumes
adoption. Plan section 3.1 instead asks for a "logical obligation to existing
field to checker to lowerer to test" mapping at implementation time. Adopting
PC 2.0 invalidates existing checker and experiment pass records. Until decided,
System-HIS v1.2 remains current and TB-05 checkpoint-kind work stays deferred.

**B2 — Do `uart_fifo_loopback` and `stream_fork_join` stay in the primary four?**
Both fail TB-09 today (section 4.1). The options are to build independent
oracles, or to substitute from the frozen reserve per section 7.4. The plan
forbids substituting a family after seeing results, so this must be settled
before any formal run.

**B3 — Which families are actually `paper1_core`?**
The catalog carries two conflicting definitions differing by nine families
(section 4 item 2). Reconciling them changes the study population, so it is a
research decision, not a data-entry fix.

Also outstanding, from the plan's own section 16.3: no English counterpart of
the plan exists, and the v1.12 architecture spec is still written against
v1.7/v1.8 method families, gate sequence, and budget formulas.

## 7. Migration status

Repository alignment, capability implementation, and experiment execution are
tracked separately and must not be conflated.

| Dimension | State |
| --- | --- |
| Repository research authority and instruction chain | migrating; Batch A landed |
| Capability implementation required by v2.1 | **early.** TB-03 (B4) is registered, wired, and tested as of Batch B, with its non-call axes explicitly unresolved. TB-05 checkpoint kinds are unmapped; application task cards (TB-11) do not exist; TB-09 is unmet for two primary families |
| v2.1 research experiments | **not started, not authorized** |

## 7.1 Next directly executable tasks

Ordered, and none of them require a blocked decision:

1. **Map TB-05 checkpoint kinds.** Add the plan's outcome-based
   `pc_failure_checkpoint` / `project_failure_checkpoint` / `project_checkpoint`
   as a derived view over the existing `CheckpointId` nodes and their
   `failed` status, rather than replacing the artifact-based enum. Read-only
   derivation keeps it independent of B1.
2. **Adopt B4 in a development run config.** Set `budget_policy: paper1-b4-v1`
   in one `agent/configs/current/*.example.yaml` and confirm the planned sample
   metadata carries the registered ceilings. This exercises the Batch B path
   end to end without a paid call.
3. **Record the unresolved B4 axes as an explicit pre-pilot checklist** in the
   plan's appendix A terms, so `is_freeze_ready` has an owner.
4. **Drafting the vision task card** (plan section 13.5 calls it the first
   concrete deliverable) can begin, but section 7.7 leaves several values to be
   adjudicated, so it will stall without input on operator, output mode, and
   protocol subset.

Not executable yet: anything that depends on B1, B2, or B3; anything requiring
`iverilog` (see V6); anything requiring a model call.

## 8. Batch log

### Batch A — research authority and development entry points (2026-09-15)

Goal: remove superseded authority from the live instruction chain and from the
one code path that bound it, and give the migration a persistent home.

| File | Change |
| --- | --- |
| `agent/src/sr2fpga_agent/g3_test_evidence.py` | **Code.** `source_fingerprint` bound `docs/specs/2026-08-14-...-research-program-design.md` (the superseded v1.8 spec) as a governing document. Now binds `docs/specs/2026-09-14-...-research-plan-v2.1.zh.md`. Module docstring states that `G3` is a retained identifier, not a current work-package claim |
| `AGENTS.md` | Routing row for research semantics now names `paper1-v2.1`, its adoption date, Chinese authority, not-frozen status, and that adoption granted neither implementation nor experiment authorization. Architecture row carries an explicit "not yet synchronized" caveat and a conflict rule. Added `[migration]` link |
| `docs/README.md` | Added a `migrations/` directory row, a `superpowers/` row marked historical, and a "Continue the v2.1 migration" reading path |
| `docs/specs/2026-09-08-sr2fpga-terminology.md` | Current-authority citation moved from the v1.8 spec to `paper1-v2.1`; note that its "实验门" wording refers to the retired G0-G9 sequence |
| `docs/specs/superseded/2026-09-11-pc-layered-study-design-v1.md` | Same citation fix, plus a scope notice recording which parts survive v2.1 (A/B/A-R/B-R labels, PC interface responsibilities) and which must be re-read (experiment protocol, budget fairness, gates) |
| `.../foundation/canonical-citation-registry.md` | Status line no longer claims v1.8 is canonical; routing role retained, claim-permission statements flagged for re-reading |
| `.../writing/v1.9-discussion-ledger-and-next-chat-handoff-2026-09-10.md` | Marked superseded and explicitly "not a current handoff"; the original authority bullets kept as a dated historical record |
| `.../writing/contract-guided-evolutionary-dse-v1.9-candidate.md` | Reframed as a historical candidate; records that EA is now an optional, default-disabled extension |
| `docs/superpowers/specs/2026-08-29-g3b-*-design.md` | Marked historical; points at the shipped implementation and at the open TB-05 mapping |
| `docs/superpowers/plans/2026-08-29-g3b-*.md` | Marked **COMPLETED AND HISTORICAL — do not execute**; its "REQUIRED SUB-SKILL ... implement this plan task-by-task" agentic-worker directive explicitly voided, and its unchecked boxes declared a historical snapshot rather than outstanding work |

Old assumptions removed from the active instruction and run path: that the v1.8
specification is current authority; that the G0-G9 / G3b gate sequence is the
live work sequence; that the v1.9 EA redesign is a pending Paper-1 direction;
that the 2026-09-10 ledger is a valid handoff; and that the G3b plan is
executable work.

### Batch B — B4 budget allocation (2026-09-15)

Goal: implement TB-03. Before this batch, `paper1-v2.1` section 6.4 had no
implementation: `method_contract.budget_allocation_id` carried the labels
`paper1-at1-v1` / `paper1-two-stage-v1` / `paper1-online-repair-v1` with nothing
binding them to numbers, and the runner derived ceilings from `max_attempts`
using the superseded v1.7/v1.8 formula.

The concrete defect that formula produces:

```
legacy-attempts-v1, max_attempts = n
  M1 -> max(1, n)              M5 -> 2 + max(0, n - 1)
  n=1: M1=1, M5=2    n=3: M1=3, M5=4    n=5: M1=5, M5=6
```

M5 receives one more logical model call than M1 at every attempt count, so
`M5-M1` would have compared two different budgets. That is precisely the matched
-repair-count fairness section 6.4 replaces.

| File | Change |
| --- | --- |
| `agent/src/sr2fpga_agent/budget_allocation.py` | **New.** Registers the section 6.4 allocations: M0 `1+0`, M1 `1+3`, M2/M3/M4 `2+0`, M5 `2+2`, all within the `B4_TOTAL_MODEL_CALLS = 4` ceiling. Each allocation is cross-validated against its method contract, so initial-stage calls must equal the declared non-repair stages and remaining calls require a method that actually permits repair or PC correction. The token, tool-subcall, runtime, and EDA axes the plan leaves open are `None` and surfaced through `unresolved_axes`; `is_freeze_ready` is `False` while any remain, which encodes appendix A's rule that placeholders must not reach an approved configuration. `budget_policy_sha256()` gives the policy an identity |
| `agent/src/sr2fpga_agent/method_contract.py` | `budget_allocation_id` values now name the registered B4 policies. This deliberately changes `method_policy_sha256`; per plan section 16.1 that is the intended method-version break and prior pass records are not carried over. Module docstring updated; the stale "adapters are introduced in CD4" reference to the retired CD1-CD10 sequence removed |
| `agent/src/sr2fpga_agent/runner.py` | New `RunnerConfig.budget_policy`, loaded from run config. Under `paper1-b4-v1`, `_sample_model_call_ceiling` takes ceilings from the registry, ignores `max_attempts` entirely, and refuses a `max_model_calls` override that contradicts the allocation. Unknown policy values are rejected in `planned_samples`. The default stays `legacy-attempts-v1` so existing development configs and the passing suite are untouched |
| `agent/tests/test_sr2fpga_agent_budget_allocation.py` | **New**, 31 tests, including negative cases: over-ceiling, negative, repair-flag mismatch, wrong initial-stage count, remaining calls on a non-repair method, unknown condition, and an assertion that the superseded allocation ids are gone |
| `agent/tests/test_sr2fpga_agent_runner_budget_policy.py` | **New**, 42 tests. Covers B4 invariance across `max_attempts` in `{1,3,4,7}`, M1 == M5 == 4 under B4, rejection of contradicting overrides, unknown policy rejection, and a regression witness recording that the legacy policy gives M1 != M5 |

Scope note: B4's non-call axes remain unresolved by design — the plan defers them
to development measurement and requires locking before the exclusionary pilot.
This batch makes that incompleteness explicit and machine-checkable rather than
resolving it.

## 9. Verification log

| # | Check | Command | Result |
| --- | --- | --- | --- |
| V1 | Contracts suite, pre-migration baseline | `python -m pytest contracts/tests -q` | **PASS** — 313 passed in 35.16s |
| V2 | Agent suite, pre-migration baseline | `python -m pytest agent/tests -q` | **82 failed, 1765 passed, 333 subtests passed** in 956s. All 82 pre-date the migration — see V6 |
| V3 | Batch A behavioural change | `source_fingerprint(repo)` keys inspected | **PASS** — v2.1 plan present, v1.8 spec absent, architecture spec retained, 328 files fingerprinted |
| V4 | Batch A regression, evidence recorder and manifest | `python -m pytest agent/tests/test_sr2fpga_agent_g3_acceptance.py agent/tests/test_sr2fpga_agent_g3_scenarios.py contracts/tests/test_contract_manifest.py -q` | **PASS** — 16 passed in 120.44s |
| V5 | Migration-record and instruction link targets | existence check on every path added in Batch A | **PASS** |
| V6 | RTL-simulation tests | `python -m pytest agent/tests/test_sr2fpga_agent_failure_injector.py -q` | **FAIL — pre-existing environment defect, not a migration regression.** 21 failed / 44 passed. Every failure is `AssertionError` at `agent/tests/rtl_sim_support.py:80` with empty tool output |
| V7 | WP0 inventory verification | direct reads of the catalog and evidence ledger | **PASS** — all six section 16.4 claims confirmed; one correction and one new finding recorded in section 4 |
| V8 | Real-tool minimal closed loop | not attempted | **BLOCKED** by V6 |
| V9 | Post-Batch-A regression | `python -m pytest contracts/tests agent/tests/test_agent_repository_resources.py agent/tests/test_repository_paths.py agent/tests/test_sr2fpga_agent_paper1_protocol.py agent/tests/test_sr2fpga_task_catalog_v02.py -q` | **PASS** — 355 passed, 5 subtests passed in 58.06s |
| V10 | Batch B new coverage | `python -m pytest agent/tests/test_sr2fpga_agent_budget_allocation.py agent/tests/test_sr2fpga_agent_runner_budget_policy.py -q` | **PASS** — 31 + 42 = 73 passed |
| V11 | Batch B regression, budget-adjacent modules | `python -m pytest agent/tests/test_sr2fpga_agent_runner_method_dispatch.py test_..._project_contract.py test_..._terminal_selection.py test_..._public_evaluator.py test_..._method_adapters.py test_..._paper1_protocol.py + both new files -q` | **PASS** — 181 passed in 22.27s |
| V12 | Batch B regression, runner and cost accounting | `python -m pytest agent/tests/test_sr2fpga_agent_runner.py test_..._cost_accounting.py test_..._block_preparation.py test_..._training_eligibility.py -q` | **3 failed, 185 passed, 13 subtests passed.** The three failures are byte-identical in name to the V2 baseline's `runner.py` failures, so **no regression** |
| V13 | B4 through the public config loader, no model call | `load_runner_config('agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml')`, then compare ceilings under both policies and run `planned_samples` | **PASS** — legacy gives `M1=1, M5=2`; `paper1-b4-v1` gives `M1=M5=4` and `M0=1, M2/M3/M4=2`, matching section 6.4. `planned_samples` accepted the policy and produced 24 samples |
| V14 | Static sweep for retired authority in the live path | searches for the superseded spec path, the superseded allocation ids, and "remains the canonical" assertions | **PASS** — no live occurrence remains. Surviving mentions are deliberate: the migration matrix quoting what it fixed, a negative test asserting the old ids are gone, and a docstring explaining the rename |

### V2 baseline failure distribution

All 82 baseline failures fall in ten files and split into two pre-existing
groups:

| Group | Files | Signature |
| --- | --- | --- |
| Simulation compile/run | `failure_injector`, `project_generator`, `oracle_signal`, `oracle_image`, `oracle_numeric`, `oracle_rl`, `public_l2_harness`, `pc_assembly` | `sim compile failed` with exit code `3221225785` = `0xC0000139` `STATUS_ENTRYPOINT_NOT_FOUND`, plus bare `AssertionError` at `rtl_sim_support.py:80` |
| Runner resume | `full_pack_smoke`, `runner` | `ArtifactConflictError: artifact key already names different content: tool-environments/development-preflight` |

`full_pack_smoke` was re-run in isolation and reproduces 8 failures
independently, so these are not ordering artefacts of the full run. The runner
group is consistent with a preflight record that varies because the toolchain is
broken, but that causal link was not proven and is recorded as an observation
only.

### V6 root cause

`iverilog` compilation exits `127` with no diagnostic:

```
$ iverilog -g2012 -o sim.out t.v   # trivial one-module file
rc=127
$ PATH="/d/Tools/oss-cad-suite/bin:/d/Tools/oss-cad-suite/lib:$PATH" iverilog -g2012 -o sim.out t.v
rc=0
```

`iverilog -V` succeeds in both cases, so the front end runs but cannot start its
backend. `PATH` places `/mingw64/bin` ahead of `/d/Tools/oss-cad-suite/bin`, so
`iverilog.exe` resolves mingw64 runtime DLLs instead of the oss-cad-suite ones.
A second, separate Icarus install exists at `/c/iverilog/bin`.

This is an environment/installation problem, not a repository defect. It was
**not** changed by this migration: the pre-migration baseline run (V2, started
before any edit) shows the identical failure pattern. It is left unfixed because
repairing the toolchain install and reordering the operator's `PATH` is outside
this task; hardcoding a `PATH` override into `rtl_sim_support.py` would change
evaluation-harness behaviour without a request.

Consequence: the plan's real-tool checks cannot be exercised here, so no claim
is made about simulation-backed behaviour. `yosys`, `vvp`, and `verilator`
resolve; `nextpnr-xilinx` is absent, so no L4 path is runnable either.

## 10. Review of `paper1-v2.2-draft` and code spec `v2.1-draft` (2026-09-15)

Review only. Nothing in this section was migrated, and no file outside this
record was changed for it.

### 10.1 Authority status

| Document | Self-declared status | Adopted? |
| --- | --- | --- |
| `2026-09-15-...-research-plan-v2.2.zh.md` | `paper1-v2.2-draft`, `完整研究重构候选稿` | **No** |
| `2026-09-15-...-code-architecture-development-spec-v2.1.zh.md` | `sr2fpga-paper1-code-dev-v2.1-draft` | **No** (appendix D.3 says so explicitly) |
| `PC-2.1-AI-stream-contract-design.zh.md` | `pc-2.1-design-candidate` | **No** |
| `contracts/pc-2.0/{project-contract,design-proposal}-2.1.schema.json` | delivered candidate schemas | **Not registered** in `contracts/manifest.json` |

### 10.2 Byte-identity verification

Twelve of the fifteen cited source hashes were recomputed and **match exactly**,
including both PC 2.1 schemas, the PC 2.1 design, `IMPLEMENTATION_DELTA`, the
v2.0 architecture spec, the v1.12 spec, and v2.2 itself as cited by the code
spec. Two do not:

| Citation | Cited | Actual | Meaning |
| --- | --- | --- | --- |
| v2.2 `[R1]`, the v2.1 plan | `2da34c3b…` | `0e5fea56…` | v2.2 was written against a **pre-adoption** copy of v2.1. It labels v2.1 `paper1-v2.1-draft` and therefore does not account for v2.1's section 16.3 adoption record or its section 16.4 WP0 inventory. The same stale hash appears in the v2.0 architecture spec |
| v2.2 `[R6]` / code spec `[T]`, `conformance.json` | `4f9e2619…` | `25b042c2…` | Different file. The repository's `reports/conformance.json` is the **PC 2.0** report (`tests_run: 70`). PC 2.1 claims **149** tests and points readers at this same path |

### 10.3 What the repository actually contains

| Claim | Verified state |
| --- | --- |
| PC 2.1 schemas delivered | **Present**, both hash-verified — but placed in `contracts/pc-2.0/`, whose `README.md` still describes only the 2.0 files and says "Not adopted. Not registered." The code spec's target layout puts them at `contracts/pc/2.1/` |
| PC 2.1 reference checker and semantic helpers "已实现" | **Absent from the repository.** No `tensor_reference` or PC 2.1 checker module exists. Same gap class already recorded for PC 2.0 |
| PC 2.1 149-test conformance report | **Absent.** Only the 70-test PC 2.0 report is present |
| Three primary AI families | **Absent from the task catalog.** `ai_dw_pw_block`, `ai_quantized_residual_block`, `ai_tiled_gemm_pipeline` are all missing. The only AI-adjacent entries, `conv2d_core` and `p_simple_cnn_pipeline`, are both `implementation_status: future` and were never run |

### 10.4 Internal consistency — checked and sound

All sample-size and budget arithmetic was recomputed and is self-consistent
across both documents:

- Shared-initial dedup calls `6` = S_D 1 + S_C 1 + S_B 1 + U_P 1 + M2 gen 1 + M3 gen 1.
- Attributed initial `10` = 1+1+2+2+2+2. Block maxima `11` and `15` follow from `+3+2`.
- `blocks = 3ncr`, `method_results = 18ncr = 6 × blocks`; at n=20, c=2, r=3 this
  gives 60 clusters, 120 configs, 360 blocks, 2160 results, 3960/5400 calls.
- Pilot 144 = 3×4×1×2×6 with 12 clusters and 24 blocks; second model 144 with 18
  clusters; native agent 36 with 9 clusters; physical 54 = 3×3×1×1×6.

The two documents agree on every shared figure. The v2.2 B4 table is **identical
to v2.1 section 6.4**, so `agent/src/sr2fpga_agent/budget_allocation.py` and its
73 tests remain valid unchanged under v2.2.

### 10.5 Principal findings

1. **Evidence base resets to zero for the main result.** The outgoing four
   families carry L3 plus qualified mutation evidence; two even have independent
   oracles. The incoming three have no catalog entry, no implementation, no
   oracle, no mutation qualification, and no tool qualification — and PC 2.1's
   emitter, tensor ABI, and checker do not exist in the repository either. v2.2
   handles this correctly in governance terms (section 7.5 qualification gate,
   section 16.2 fallback to a case study), but neither document states the
   engineering cost of rebuilding the entire evidence base.
2. **Blockers B2 and B3 are superseded, not solved.** Both concern the four
   families' oracle independence and `paper1_core` membership. Under v2.2 those
   families leave the main statistics, so the questions lapse — while the far
   larger gap in finding 1 replaces them.
3. **M1 file-level repair (v2.2 section 5.4) changes an implemented surface.**
   `method_contract.py` gives M1 `allowed_edit_surface_id =
   "direct-project-repair-v1"`. Adopting v2.2 requires a new edit surface and a
   corresponding `method_policy_sha256` break.
4. **`IMPLEMENTATION_DELTA.zh.md` section 3 and PC 2.1's scope statement still
   assert the four-family population is unchanged.** Both are superseded by
   v2.2, which both v2.2 section 20 and code spec section 22.3 acknowledge and
   schedule for correction. Until corrected they are live contradictions.
5. **Neither document read the repository.** Both say so explicitly (v2.2
   sections 0.4 and C.3; code spec sections 0.1 and D.2). So neither accounts for
   the verified WP0 inventory, the B4 implementation, or the toolchain defect
   (`iverilog` exit `127`) that blocks the real-tool loop this plan depends on far
   more heavily than v2.1 did.

### 10.6 Decision required

Adopting v2.2 is a research decision with a large engineering consequence and is
**not** made here. It supersedes blocker **B1**: the question is no longer
"PC 2.0 or System-HIS v1.2" but "adopt the v2.2 + PC 2.1 population switch, or
keep v2.1". Recorded as blocker **B4-scope**.

---

## 11. Migration to `paper1-v2.2` (adopted 2026-09-15)

Adoption resolved blocker **B4-scope** and superseded **B1**, **B2**, **B3**:
PC 2.1 is adopted, and the four families that B2/B3 concerned leave the main
statistics.

### 11.1 Revised target baseline

Where v2.2 differs from the section 3 table:

| ID | Change under v2.2 | Plan |
| --- | --- | --- |
| TB-01 | Task population is three quantized-AI subsystems: `ai_dw_pw_block`, `ai_quantized_residual_block`, `ai_tiled_gemm_pipeline`. The former four families exit the main statistics and keep development/regression value | 2.1, 2.3 |
| TB-02 | Unchanged — `M5-M1@B4` and `M4-M3@initial` in one Holm family | 9.1, 12.2 |
| TB-03 | **Unchanged.** v2.2's B4 table is identical to v2.1 section 6.4, so the Batch B implementation carried over with no edit | 10.1 |
| TB-04 | Unchanged M0-M5, plus **M1 may now do atomic file-level replacement** instead of resending the whole project | 9.2, 5.4 |
| TB-05 | Shared-start DAG restated as `S_D` / `S_C` / `S_B` / `U_P`; failure sharing unchanged | 10.2 |
| TB-09 | Unchanged requirement, now applied to three families that have **no** oracle at all | 8.2 |
| TB-13 | New: the independent statistical unit is `design_cluster_id`, not `semantic_instance_id`; configurations and replicates nest inside it | 7.1, 12.1 |
| **TB-14** | **New.** PC format is `sr2fpga-pc-2.1`. No reader, alias, or conversion path for System-HIS v1.2 or PC 2.0 | 0.1, 4 |
| **TB-15** | **New.** `construction_origin_map` must attribute structure between trusted build and model behaviour | 5.2, 11.2 |
| **TB-16** | **New.** Native coding-agent comparison C0/C1 is a planned secondary population with its own budget accounting — never B4 outer-call counts | 13.5 |

### 11.2 Batch C — adoption records

| File | Change |
| --- | --- |
| `docs/specs/...-research-plan-v2.2.zh.md` | Version `paper1-v2.2-draft` to `paper1-v2.2`; status line now records adoption. **Added section 21**: authorization scope (migration yes, experiments no), the authority-relation table, and the five items confirmed open at adoption — the stale `[R1]` hash, the missing PC 2.1 checker, the missing 149-test report, the absent AI families, and the broken `iverilog` |
| `docs/specs/...-code-architecture-development-spec-v2.1.zh.md` | Version to `sr2fpga-paper1-code-dev-v2.1`; added a status line; section 0.3 and appendix D.3 record adoption instead of draft status |
| `docs/specs/PC-2.1-AI-stream-contract-design.zh.md` | Status to current PC design. Added an implementation-fact banner stating the checker and conformance report are absent from the repository. Its "does not change the v2.1 population" scope line corrected |
| `docs/specs/IMPLEMENTATION_DELTA.zh.md` | Its section 3 "four families unchanged" clause struck through and corrected; the header records the supersession |

### 11.3 Batch D — entry points

`AGENTS.md`, `README.md`, `docs/README.md`, `docs/specs/README.md`,
`docs/current-status.md`, the terminology ledger, `contracts/README.md`,
`contracts/pc/README.md`, and the `agent/`, `training/`, `app/` READMEs now route
to v2.2 / spec v2.1 / PC 2.1. `docs/specs/README.md` was rewritten; the
`current-status.md` migration section was replaced and now lists what v2.2 needs
that does not exist.

Two substitution bugs were caught and fixed during this batch: a relative-path
depth error that produced `../../../docs/...` from `../../docs/...`, and a stale
section reference — v2.2 puts the B4 table in section 10.1, not 6.4.

### 11.4 Batch E — PC 2.1 registration (code and contracts)

| Change | Detail |
| --- | --- |
| Layout | Schemas moved from `contracts/pc-2.0/` to `contracts/pc/2.1/` per spec section 3.1, verified byte-identical before the old directory was removed. PC 2.0 schemas preserved at `contracts/pc/2.0/`, still unregistered |
| `contracts/manifest.json` | **Registered** `project_contract_2_1` (`sr2fpga-pc-2.1`) and `design_proposal_2_1` (`urn:sr2fpga:pc-design:2.1`) |
| `agent/src/sr2fpga_agent/contract_registry.py` | Version-field map extended: `project_contract_2_1` binds `properties.schema_version.const`; `design_proposal_2_1` binds `$id`, because that projection is a `$ref` wrapper with no version field. **No schema bytes were edited**, so the SHA-256 values v2.2 and spec v2.1 cite stay valid |
| `agent/src/sr2fpga_agent/g3_test_evidence.py` | Evidence fingerprint now binds v2.2 and spec v2.1; the superseded plan and v1.12 spec are out |
| `contracts/tests/test_contract_manifest.py` | Registered-key set updated |
| `contracts/tests/test_pc_2_1_registration.py` | **New**, 12 tests |

### 11.5 Batch F — archive

Superseded specifications moved to `docs/specs/superseded/` with an
[index](../specs/superseded/README.md) giving each file's status and why it is
retained. Tracked files moved with `git mv` so history follows.

Archived: `paper1-v1.8` (English and Chinese), `paper1-v2.0-draft`,
`paper1-v2.1`, code-architecture `v1.12` and `v2.0-draft`, the PC 2.0 design,
the System-HIS v1.2 semantic spec, and the two 2026-09-11 PC study designs.

Active `docs/specs/` now holds only the terminology ledger, v2.2, spec v2.1,
PC 2.1, `IMPLEMENTATION_DELTA`, and the index.

**Nothing was deleted.** Files inside `superseded/` were **not** edited, because
v2.2 appendix C and spec v2.1 appendix D cite them by SHA-256; three cited
hashes were re-verified byte-identical after the move. The cost is that some
relative links inside archived files no longer resolve — recorded in the archive
README rather than silently fixed.

### 11.6 Verification

| # | Check | Result |
| --- | --- | --- |
| V15 | `python -m pytest contracts/tests` after registration | **PASS** — 313 passed |
| V16 | PC 2.1 resolves through `ContractRegistry` and rejects PC 2.0, System-HIS, empty, and case-variant documents | **PASS** |
| V17 | `python -m pytest contracts/tests/test_pc_2_1_registration.py` | **PASS** — 12 passed |
| V18 | Full regression: contracts + evidence recorder + repository resources + both budget suites | **PASS** — 422 passed in 161.88s |
| V19 | Markdown link integrity, 253 links across active docs, contracts and project READMEs | **PASS** — 0 broken in active docs. 17 dangling inside `superseded/` are intentional (hash-cited bytes); 9 `artifacts/` paths were already dangling because that directory is git-ignored runtime output |
| V20 | Hash-cited archived files unchanged after the move | **PASS** — `0e5fea56`, `9fa43aad`, `fd5123c3` all match |
| V21 | Evidence fingerprint binds the new authority | **PASS** — v2.2 and spec v2.1 in, superseded plan and v1.12 out, 334 files |
| V22 | Real-tool loop | **BLOCKED** — `iverilog` still exits `127`; unchanged by this migration |

### 11.7 Migration status after adoption

| Dimension | State |
| --- | --- |
| Research authority and instruction chain | **migrated.** Every active entry point routes to v2.2 |
| Project Contract format | **migrated.** PC 2.1 registered and resolving; System-HIS retained read-only for existing artifacts |
| Capability implementation | **early.** B4 carried over. Absent: the three AI families, PC 2.1 checker and structure emitter, tensor ABI, `construction_origin_map`, statistical analysis |
| v2.2 research experiments | **not started, not authorized** |

### 11.8 Next directly executable tasks

1. **Register the three AI family identities** in the task catalog with honest
   status (`implementation_status: future`, `oracle_readiness: not_ready`), so
   the population exists as an identity before anything claims readiness.
2. **Implement `construction_origin_map`** (TB-15). Without it M4-M3 cannot be
   attributed, which is the point of the second primary comparison.
3. **Add the PC 2.1 checker** (`pc/validation.py`, `pc/tensors.py` per spec
   section 3.1), or obtain the checker the PC 2.1 package says it delivered.
4. **Update M1's edit surface** for file-level replacement (v2.2 section 5.4);
   this breaks `method_policy_sha256` again, deliberately.
5. **Fix the toolchain** — put `/d/Tools/oss-cad-suite/bin` ahead of
   `/mingw64/bin` — so the real-tool loop V22 blocks on can run.

Not executable yet: anything needing a model call, official evaluation, or EDA.

## 12. Full migration continuation — 2026-09-15 (current)

### 12.1 Protected starting point and authority

This continuation begins on `develop`, HEAD
`e20dfd2ce46c5690767e30cb629fb5c58aff073a`, with staged renames, unstaged
changes and untracked migration/code/schema files already present. All changes
in sections 1–11 predate this continuation; they are not newly claimed work.
No commit, staging, reset, stash, branch switch or external write is authorized
by this task. The preexisting index/worktree patches and status are retained in
`artifacts/migrations/2026-09-15-v2.2-continuation/`.

The designated plan `docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md`
was read in full (1,091 lines), including its §21 adoption notice: `paper1-v2.2`,
current Chinese authority, adopted, **not frozen**, migration authorized and
formal experiments unauthorized. §21 supersedes the drafting-time §0.3 reference
to the old architecture. The plan itself is not edited by this continuation.
Historical memory was searched for migration context but supplied no applicable
current decision; live files govern this audit.

### 12.2 Target baseline and dependency order

TB-01–TB-16 in §11.1 remain tracking handles, not additional research rules.
Their current interpretation is exclusively the v2.2 plan:

| ID | Current requirement and section |
| --- | --- |
| TB-01 | Three AI families only in the main population; old tasks remain regression (§2, §6) |
| TB-02 | M5−M1 system and M4−M3 shared-PC build/edit contrasts (§9, §12) |
| TB-03–05 | Candidate B4, batched behavior, shared successes/failures and full attributed costs (§5, §10); numeric resource ceilings remain unconfirmed |
| TB-06–08 | WP0–WP6; training, EA, Q-table and platform integration outside core (§2.3, §16) |
| TB-09–10 | Independent oracle; sealed terminal; one hidden semantic slot; real access isolation (§8, §15) |
| TB-11–12 | Exact public math/ABI/reset/stall facts; evidence-specific success and complete failure/unknown denominators (§3, §11) |
| TB-13 | Design-cluster/dependency-group sampling; configuration and replicate nesting; development exposure permanent (§7, §12) |
| TB-14 | Strict PC2.1 design input, controller byte bindings, no legacy fallback (§4, §21) |
| TB-15 | Deterministic structure only, protected behavior and construction attribution (§5, §11.2) |
| TB-16 | Native Agent comparison planned secondary, independently budgeted (§13.5) |

Minimal target: reuse the local controller, immutable storage, tool wrappers and
accounting where verified; replace PC parsing/checking/building along
`requirements -> pc -> build -> methods -> public workers -> sealed hidden/physical
workers -> analysis`. Do not add a microservice framework. Register family
identities before runnable tasks; implement input/binding before tensor semantic
checking, then structure building, then the DW→PW development task/reference and
model loop. Research-valued choices (task numeric profile, splits, scientific
thresholds, pilot budget and model) stay unresolved until explicitly determined;
identity registration must not fabricate readiness or thresholds.

### 12.3 Initial coverage and planned batches

`inventory.json` inventories 11,969 tracked/untracked non-ignored files by path
and size, hashing small text files only. This is **inventory, not full reading**.
Ignored runtime trees, large binaries/data and dependency contents are excluded
from source review; no historical experiment bytes are changed. An initial
all-file hash attempt was interrupted and replaced with bounded text hashing.
The inaccessible `.pytest_cache` is recorded as an inventory limitation.

| Surface | Evidence / discrepancy | Decision | Dependency / acceptance |
| --- | --- | --- | --- |
| Root AGENTS, plan, architecture, migration/status, owning READMEs | Plan fully read; stale v2.1 text remains below updated headers | ADAPT | G: correct actual authority/current claims; inspect links |
| Catalog + task_catalog loader + consumers | `paper1_core` still selects old tasks, three AI identities absent; old schema fields impose HIS assumptions | ADAPT / ADD | G: name current population without fabricated task qualification; preserve explicit regression sets; negative readiness tests |
| Registered PC2.1 schemas and registry | Already registered before this turn; runtime does not consume them | KEEP / ADD | H: strict parsing and controller binding, positive/negative input tests |
| cli/runner/generation/pc_assembly | Real existing path still HIS1.2; no PC2.1 construction | RETIRE from new core / KEEP legacy development | H: explicit old runtime identity and reject new-core claims rather than fallback |
| Existing tool/storage/accounting | Candidate reuse, not yet universally audited | ADAPT pending scoped review | Focused tests and call-chain audit |
| Trusted oracle/hidden/metrics | AI oracle and cluster analysis absent | ADD / UNRESOLVED | Task math/profile and independent evidence required; do not fake success |
| Historical data/results and old task RTL | Useful original-scope regression evidence | ARCHIVE logically / KEEP bytes | No promotion to AI evidence; retain original identities |

Batch G: finish authority/capability wording and population identity migration.
Batch H: strict PC2.1 input/bindings and public development command; explicitly
isolate the legacy runner. Batch I: validate focused regressions, exercise public
commands, record actual tool availability and remaining WP1/WP2 work. Full tensor
checker/emitter and task/oracle qualification remain distinct implementation
milestones, not implied by G/H success.

### 12.4 Validation in this continuation

| Check | Result |
| --- | --- |
| Before edits: `python -m pytest contracts/tests/test_pc_2_1_registration.py contracts/tests/test_task_catalog_contract.py agent/tests/test_sr2fpga_task_catalog_v02.py agent/tests/test_sr2fpga_agent_budget_allocation.py agent/tests/test_sr2fpga_agent_runner_budget_policy.py -q -p no:cacheprovider` | PASS: 110 passed, 5 subtests passed, 3.72 s |
| Environment discovery | Python 3.13 at `python313`; Icarus/vvp/Yosys/Verilator resolve from oss-cad-suite; nextpnr-xilinx not found. Resolution alone is not execution verification |
| New AI model/RTL/full FPP loop | NOT RUN: PC2.1 build/task/oracle missing; model budget not authorized |

### 12.5 Executed changes and retained boundaries

**G — population and authority.** Catalog data revision 0.3.0 retains the
registered v0.2 envelope/path, but intentionally changes selection semantics.
`paper1_core` now contains only the three plan §2 AI identities. Previous core,
held-out and physical sets have explicit `legacy_` names; old core family roles
are `development_regression`. New identities have no generator alias, no mutation
suite and a null threshold, not an invented research number. Navigation tier and
difficulty are explicitly non-binding engineering metadata. `current_research`
records the adopted plan/format, absent formal split and disabled recipes.
`current_research_family_specs()` has no legacy fallback. The historical recipe
restriction remains active only for old development and has a revised policy
identity; old run fingerprints must not be silently resumed against this catalog.

The task ledger adds only three `not_implemented`/`not_run` rows. All 71 original
family rows, alias evidence and L4 evidence remain identical as JSON objects;
independent review verified this. Its derived status is regenerated and reports
current core 0/3, while explicitly identifying aggregate tool counts as including
historical families. This is absence bookkeeping, not evidence promotion.

The writing workspace's `state.json` still pointed to v2.1 and old candidate
next actions. Its exact starting bytes are preserved at
`docs/research-program/paper1-v1/history/state-before-v2.2-migration.json`, verified
against the pre-edit SHA-256. `state.json` is now a short historical-workspace
pointer to v2.2 and this migration record. No old QA/candidate fields are
available as current top-level state. The workspace README labels its contents
historical. No global instruction or configuration was changed.

**H — implemented PC2.1 input milestone.** `agent/src/sr2fpga_agent/pc/inputs.py`
implements bounded strict JSON, duplicate/noninteger/nonfinite/invalid-Unicode
rejection, registered design schema validation, controller-supplied original-byte
bindings and full-PC rechecking. `pc/__main__.py` exposes `assemble` and `check`;
new files are written exclusively and revalidated before saving. Model output
cannot supply the bindings or redirect trusted source reads. Neither API nor CLI
claims semantic validation, construction, H-stage success or task readiness.
The fixture is explicitly schema-only, not an AI or RTL reference.

Old CLI/runner help now says legacy development. Explicit research-plan/PC-format
claims are rejected before run construction rather than silently ignored. Old
Python generation and demo APIs remain available for their historical development
scope; this is **not** a complete migration of their internal HIS machinery.

**I — caller synchronization and validation.** Independent review found that
`testbench_checker.oracle_strength_ready()` would compare a score to the new null
threshold. It now returns false for an undefined threshold; no old threshold was
changed, no new threshold assigned, and all three AI identities have negative
readiness tests. The review also verified no original evidence rows changed.
Compatibility tests now assert current and historical schema identities separately
and check the old specifications' explicit archive entries; they no longer demand
that archived files remain active specification entry points.

### 12.6 Coverage ledger and remaining audit

| Scope | Inventory / reading / verification in this continuation |
| --- | --- |
| Whole visible versioned tree | 11,969 files inventoried; 9,864 datasets, 1,493 reports, 242 agent, 124 contracts, 97 outputs, 74 docs, 34 training, 25 references, 6 app, 4 compatibility tests, plus root files. Inventory is not semantic review |
| Instructions | Root AGENTS fully read; ancestor instruction paths checked; nested/override instructions searched; `.agents`/`.codex` and CI presence inspected. Related local/global surface audit recorded separately below |
| Research | v2.2 fully read, target extracted independently before edits; subordinate architecture sections for authority/input/build responsibilities read; PC2.1 schema and input-design clauses read by implementation reviewer |
| Runtime | CLI and two_stage/oracle registry read; runner configuration, dispatch, version defaults, initial run/recovery entry and official-population guards traced; agent pipeline, pc_assembly, generation/context_his and req2his relevant sections read |
| Catalog/report | Catalog shape, every family ID/status through machine inspection; loader and evidence parser/report/caller sections read; affected tests and report recomputation executed |
| New PC inputs | All new implementation and tests read and independently reviewed; public command exercised, input/registry/negative tests run |
| Training/app | Relevant package/entrypoint/config boundaries and documentation reviewed; Training package/CLI lightweight regression exercised. No live browser or model-serving/training run |
| Unfinished source audit | Entire runner/agent/tool_runner/oracle_runner, full skeleton/repair/hidden isolation, all oracle algorithms, analysis/report scripts and all tests have **not** been fully read. No comprehensive security or evaluator correctness claim |
| Historical data/binaries | Path/size and bounded text hashes only; no workload download, numerical revalidation or evidence promotion. Ignored runtime/private trees and binaries excluded from semantic review |

### 12.7 Validation evidence and interpretation

All local outputs are under `artifacts/migrations/2026-09-15-v2.2-continuation/`.

- `pc-input-smoke/execution.json`: **PASS**, both public `python -m
  sr2fpga_agent.pc assemble` and `check` return 0; exact command arguments and
  output are saved. Receipt explicitly records semantic validation and RTL
  construction as `not_run`. This is an input closed loop only.
- `tool-smoke/result.json`: **PASS**, repository `local_tools` resolves and runs
  Icarus `-g2012 -s smoke` and vvp, both exit 0. This supersedes the old universal
  environment-blocked claim for this Windows session. It does not qualify a
  tensor ABI, AI workload or L3/L4 flow. `nextpnr-xilinx` was not found.
- First integrated contract/catalog/evidence/input run: **FAIL then fixed**,
  508 passed and 1 failed because the committed derived evidence view had not
  yet been regenerated. The test caught a real synchronization omission;
  the renderer/view were synchronized without weakening the assertion.
- First compatibility run: **FAIL**, 13 passed / 4 failed. It found stale
  wording expectations, old active specification paths and missing historical
  runtime links. Missing evidence is labelled missing, not represented as verified.
- One interim catalog test run: 41 passed / 1 environment error because pytest
  could not access its temporary directory. Same test command with authorized
  external execution: **PASS**, 42 passed + 5 subtests; no implementation change
  was used to hide the permission error.
- `behavior-validation.xml`: **PASS**, 150 tests, 12.28 s. Command:
  `python -m pytest agent/tests/test_sr2fpga_agent_testbench_checker.py agent/tests/test_sr2fpga_current_population.py agent/tests/test_sr2fpga_pc21_cli.py agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_agent_budget_allocation.py agent/tests/test_sr2fpga_agent_runner_budget_policy.py agent/tests/test_agent_cli_smoke.py agent/tests/test_sr2fpga_legacy_runtime_boundary.py training/tests/test_training_package_boundary.py training/tests/test_training_cli_smoke.py -q -p no:cacheprovider`.
- Focused Ruff on new PC code, catalog, qualification caller and new tests:
  **PASS**. `git diff --check`: **PASS** (line-ending notices are not defects).
- New AI task→PC→RTL→independent oracle loop: **NOT RUN / implementation blocked**.
  The semantic checker/emitter and complete DW→PW task/reference are absent.
  Real-model generation is additionally outside the authorized resource scope.
  No formal hidden, synthesis campaign, place-and-route, training or board run.

### 12.8 Completion and next batch

**Full repository migration: PARTIALLY COMPLETE.** Current input/population
entry points can support v2.2 development, but the repository cannot yet execute
the v2.2 research method end to end. This is not merely waiting for experiments:
substantial engineering migration remains.

Next directly executable batch is WP1 semantic input resolution: implement the
public requirement-boundary adapter, finite expression/reference and tensor
checks with the PC2.1 design/schema as authority; preserve separate static
results and unverified behavioral obligations. Then implement ABI/structure
emission and `construction_origin_map`, protected batched behavior and M1 atomic
file replacement. Reuse audited storage/accounting/tool functions, not old HIS
semantic defaults. A full independent review of runner/repair/hidden workers
and configuration defaults remains necessary before replacing the legacy runtime.

WP2 follows with a complete development DW→PW task card, precise finite numerical
profile, nondegenerate public weights, independent integer reference and hand
packing cross-checks. The plan gives starting shapes, not all required numerical
or environmental decisions. Any choices changing task semantics/fairness require
explicit recorded research decisions; they are not filled by the input fixture.
Model/budget, split/dependency groups, pilot thresholds and final sample sizes
remain unresolved protocol decisions. No future experiment is claimed complete.

### 12.9 Instruction/configuration and documentation closeout

The surface review found only the root tracked AGENTS; `.agents/` and `.codex/`
were empty and no tracked `.github` CI was found. The accessible global Codex
AGENTS was empty. `.claude/settings.local.json` contains local permission rules,
not a research plan; they do not enlarge this task's authority and were not
modified. No credential/auth/environment files were read for this audit. This
check does not prove that external CI or every dynamic context mechanism is absent.

The retained app calls `DataGenerationAgent` with deterministic reference metadata
and zero model budget; it stays a legacy demo. Training import/entrypoint checks
and lightweight CLI tests do not constitute a training run. Old auto-recipe calls
in `req2his`, prompts and repair remain in the isolated legacy machinery; the new
PC input command imports none of these paths.

The documentation review's second tool call was interrupted without a successful
completion receipt. The lead reread each affected file and finished the remaining
changes; no unconfirmed subagent edit was counted as done. Final current-status
numbers distinguish current core 0/3 from historical core 14/14. Nine missing
historical runtime links are retained as explicitly missing paths. The historical
2026-09-14 authority snapshot remains labelled historical. Configuration READMEs
say maintained legacy development, and B4 is only a call-axis setting there.

`document-links.json`: **PASS**, 144 local inline/reference links checked across
12 active/changed entry documents; zero missing. This excludes archived source
specifications whose original bytes and historical links are intentionally kept.
`app-validation.xml`: **PASS**, 56 local demo tests in 15.87 s; no browser,
external deployment or real model was involved.


Final integrated check: **PASS**, `final-validation.xml`, 528 passed and
5 subtests passed in 41.77 s. Exact command:
`python -m pytest contracts/tests compatibility_tests agent/tests/test_sr2fpga_task_catalog_v02.py agent/tests/test_sr2fpga_agent_family_recipe.py agent/tests/test_sr2fpga_agent_task_catalog_exact_aliases.py agent/tests/test_sr2fpga_task_evidence_v01.py agent/tests/test_sr2fpga_current_population.py agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_pc21_cli.py agent/tests/test_sr2fpga_legacy_runtime_boundary.py -q -p no:cacheprovider --junitxml=artifacts/migrations/2026-09-15-v2.2-continuation/final-validation.xml`.
The 150-test behavior suite and 56-test app suite are separate overlapping checks,
not additional independent research samples. No all-repository test pass is claimed.

No Git commit, push, staging change, branch switch, reset, cleanup, deployment or
external publication was performed. The original plan bytes and archived writing
state bytes were checked against the starting inventory. `continuation-changes.json`
identifies this continuation's edits separately from the preexisting migration.

### 12.10 Teaching pair-development increment: entry-module reference

The first post-migration teaching-sized task adds one PC2.1 semantic rule:
`design.entry` must exactly name a key in `design.modules`. The implementation is
isolated in `agent/src/sr2fpga_agent/pc/semantics.py`; schema parsing remains in
`inputs.py`, which invokes the rule after schema validation during both assembly
and saved-PC loading. The check is case-sensitive and deliberately does not
claim module reachability, instance, port, type, parameter, tensor or behavioral
validation.

The public receipt now reports `semantic_validation: partial`, identifies
`entry_module_exists: pass`, and keeps RTL construction `not_run`. Focused input
and command tests: **PASS, 51 passed**. They cover a valid entry, missing entry,
case mismatch, saved-PC recheck, public-command rejection and absence of an
output file after rejection. Focused Ruff: **PASS**. No model or RTL tool ran.

### 12.11 Teaching pair-development increment: instance-module references

The next small rule checks every instance in each structural module. Its
`module` value must exactly name a key in `design.modules`; behavioral modules
are skipped because their schema has no `instances` collection. Diagnostics name
the parent, instance and missing target, for example
`Top.u_worker -> MissingWorker`. Assembly and saved-PC loading both execute the
rule through the internal `_validate_semantics()` coordinator.

Focused input and public-command tests: **PASS, 54 passed**. They cover a valid
structural-to-behavioral reference, a missing target, saved-PC rechecking, and a
behavioral module without an instance collection. Focused Ruff: **PASS**. The
check does not establish recursion freedom, reachability, binding/type/net/tensor
correctness, RTL construction or behavioral correctness. No model or RTL tool ran.

### 12.12 Teaching pair-development increment: recursive hierarchy rejection

The module-definition graph must be acyclic. An iterative depth-first walk keeps
the active path separate from completed modules: returning to an active module
reports the exact cycle, while two branches may legally reuse one completed
module. The iterative implementation avoids imposing Python's own recursion
limit on the number of modules. It checks every defined module, not only the
entry-reachable subset; unreachable definitions remain a separate missing rule.

Focused input and public-command tests: **PASS, 58 passed**. They cover direct
self-instantiation, a two-module cycle, legal shared-module reuse and saved-PC
rechecking. Focused Ruff: **PASS**. No model or RTL tool ran.

### 12.13 Teaching pair-development increment: module reachability

Starting at `design.entry`, an iterative work list follows structural instance
references and records reached module definitions. The checker rejects the
stable sorted difference `all definitions - reached definitions`. Multiple
instances may reference one definition; this produces multiple hardware copies
but does not make the definition unreachable or recursive.

Focused input and public-command tests: **PASS, 62 passed**. They cover an
isolated module, a disconnected two-module subtree, saved-PC rechecking and two
instances of the same module definition. Focused Ruff: **PASS**. This closes the
initial entry/reference/recursion/reachability slice only; parameter, domain,
port, net, type and tensor checks remain absent. No model or RTL tool ran.

### 12.14 Teaching pair-development increment: signature-source ownership

The entry module alone must use `signature.source=requirement_boundary`; every
internal module must use `declared`. This preserves the public ABI as a
controller-owned requirement boundary while allowing the model to declare
internal interfaces. The rule compares the actual source with the source
expected from module identity and reports both values on mismatch.

Focused input and public-command tests: **PASS, 65 passed**. They cover a
declared entry, an internal module that claims the requirement boundary, the
valid entry/internal pairing and saved-PC rechecking. Focused Ruff: **PASS**.
The checker does not yet project or compare the actual requirement boundary,
nor validate parameters, domains, ports, nets, types or tensors. No model or RTL
tool ran.

### 12.15 Teaching pair-development increment: instance parameter names

For each structural instance, supplied parameter keys must be declared in the
target module's internal signature. The checker computes the stable sorted set
difference `supplied - declared` and reports the parent, instance, target and all
unknown names. This rule relies on the earlier hierarchy and signature-source
checks, so every target exists and is an internal `declared` module.

Focused input and public-command tests: **PASS, 68 passed**. They cover a valid
`DEPTH` binding, an extra `UNKNOWN` binding and saved-PC rechecking. Focused Ruff:
**PASS**. Missing bindings, expression references, evaluation and min/max range
checks remain separate unfinished rules. No model or RTL tool ran.

### 12.16 Teaching increment: complete instance parameter bindings (2026-09-16)

After the read-only architecture review, the user authorized its recommendations.
This round completes only the agreed parameter-binding step. The existing
`validate_instance_parameter_names()` now checks both `supplied - declared`
(unknown names) and `declared - supplied` (missing names). Every instance must
supply its own complete mapping; no defaults or bindings from a sibling instance
are inherited. Empty mappings remain valid for modules declaring no parameters.
This implements the explicit-binding/no-implicit-default requirement in current
architecture §6.2 and its PC core parameter semantics. No schema or research
definition changed. CLI receipts add `instance_parameter_bindings_complete`;
overall semantic validation remains `partial`.

Validation: the four new API cases first failed with `DID NOT RAISE
PcSemanticError`, confirming the pre-change gap. After implementation, input,
public CLI and registration regression passed **85 tests in 7.32 s**:
`python -B -m pytest agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_pc21_cli.py contracts/tests/test_pc_2_1_registration.py -q -p no:cacheprovider`.
Coverage includes missing one/all parameters with stable diagnostics, independent
bindings for two instances of one definition, saved-PC rechecking and public CLI
rejection without an output file. Existing no-parameter, unknown-name and valid
binding cases remain exercised. Focused Ruff and `git diff --check`: **PASS**.
No model, RTL or physical tools ran; no commit or staging operation occurred.

Next teaching round: inspect the existing public requirement/profile contracts
and implement a bounded public-boundary reader/adapter. Resolve missing contract
semantics explicitly before writing an adapter; hashing arbitrary bytes does not
establish a valid task context. Subsequent parameter evaluation and interface
checks must use per-instance environments and distinguish definition IDs,
instance paths and specialization identities. The review also requires explicit
state/reset/memory/FIFO, numeric and timing checks, plus scoped check reports;
these remain future work, not capabilities delivered in this round. Keep the
small-step explanation/implementation/verification/pause cadence.

### 12.17 Public requirement contract mapping (2026-09-16; audit only)

This teaching round inspected the existing public inputs before implementing an
adapter, as required by current architecture §5.1 and plan §§2.2, 3, appendix A.
No runtime, schema, research definition or task numerical profile changed.

Observed legacy path: `requirement_boundary.evaluate_requirement_boundary()`
builds `RequirementEnvelope`, checks ambiguities and System-HIS backend support,
then returns a disposition. `freeze_ready_requirement_context()` freezes the
facts and profile identities into `FrozenRequirementContext`.
`build_development_episode_pack()` writes the registered `episode-pack-v1` with
separate `public_context` and `audit_only`; `generation_visible()` projects the
public context. This visibility separation is useful, but the old disposition
is not AI task qualification under v2.2.

| New requirement | Existing representation | Mapping / gap |
| --- | --- | --- |
| Source identity, revision, original text | requirement_id/revision_id/public_text | Reuse responsibilities |
| Fact origin | fact_id/value/provenance/source_ids | Reuse provenance; origin does not establish guarantee/assumption/preference role |
| Read-only public projection and private metadata separation | FrozenRequirementContext / episode-pack public_context and audit_only | Reuse boundary; never mount private pack as candidate input |
| Exact external top/interface, parameters and domains | No typed boundary field in public_context | Define a versioned extension; do not infer ports from text or a global width |
| Tensor/kernel/numerical/transaction obligations | fact value is unconstrained JSON; no AI-specific shape enforced | Bytes can be stored, but semantics are not validated; must define source-owned contracts |
| Public assets and required fact coverage | No dedicated typed fields in the examined public_context | Explicit identity/hash/format and coverage definitions needed |
| Frozen content identity | Canonical-JSON projection hash in frozen_context._sha256 | Retain original meaning; PC2.1 source-byte hash is a separate identity and must not reuse this hash |
| Task ready | Legacy System-HIS capability/ambiguity checks | Cannot transfer to AI population or infer independent oracle/tool qualification |

Schema-only in-memory probes on `episode-pack-v1.$defs.public_context` showed:
`ready` with empty fact_records is structurally accepted; arbitrary nested
fact values are accepted; adding a fact `role` or a top-level `boundary` is
rejected by the closed schema. These probes deliberately do not validate
digests, invoke a complete pack loader, or establish task readiness. Existing
contract tests: `python -B -m pytest contracts/tests/test_episode_pack_schema.py
-q -p no:cacheprovider` — **PASS, 4 passed in 0.20 s**.

Recommended next teaching slice (proposal, not yet a registered format): design
a versioned extension of the existing public-context contract, beginning with
an explicit external boundary (actual RTL top, parameter declarations/bindings,
domain slots and ports) and its source identity. Keep public facts as the source
of truth shared by Direct and PC; the adapter produces a derived read-only view.
Choose the exact versioned carrier and inspect its readers/writers before editing;
do not silently add fields to v1 or turn the PC schema fixture into a ready AI
task. Boundary conformance alone is not a complete task card. Full numerical,
transaction, asset, role and qualification requirements remain subsequent work.

### 12.18 Public boundary format design (2026-09-16; proposal only)

This round designs the next input slice, not a registered or runnable new task
format. Authority remains research plan §§3–4 / appendix A and architecture
§§4.1, 5.1–5.2. The following fields are an engineering proposal implementing
those responsibilities, not fields already prescribed verbatim by the plan.

**Carrier and ownership.** Recommend a versioned `public-context-v2` projection
of the existing episode public context, with an explicit `context_version`,
retaining requirement/revision identity, original text and source provenance.
Its `boundary` is authored/approved with the public task, never by the candidate.
The future `episode-pack-v2` should reference that same public contract and keep
audit-only metadata separate. A serialized public projection may be saved as the
PC requirements input, but is derived from one task source; the pack must refer
to that same content identity rather than hold an independently editable copy.
Do not change the v1 registry entry, upgrade its ready status automatically or
pass a full private episode pack to the candidate. No complete v2 contract is
registered in this round: boundary coverage is not complete task qualification.

**Proposed boundary fields.**

| Field | Meaning / owner | Validation responsibility |
| --- | --- | --- |
| `rtl_top` | Actual top-module name fixed by the public task | Accepted HDL identifier/profile; no derivation from candidate entry ID |
| `signature` | Parameter declarations, domains, logical ports and optional tensor contracts | Reuse PC2.1 `signature_fields` rules; no candidate `source` tag here |
| `parameter_values` | Concrete nonnegative integer values for this task's top parameters | Exact declaration coverage, ranges and later expression resolution |
| `abi.domains` | Physical clock/reset pin names for declared domain slots | Exact applicable coverage; no pins invented for clock/reset `none` |
| `abi.ports` | Explicit RTL names for value signals or stream payload/valid/ready | Exact logical-port coverage; compatible signal roles and collision checks |

Widths, directions, signedness and reset polarity remain in the signature and
are derived after parameter binding; the ABI mapping adds names, not a second
set of these values. Stream `input` means payload/valid inputs and ready output
at the external boundary. Stream `output` reverses those roles. Shared physical
clock domains, additional protocols and backend-specific naming require explicit
support; the first development example uses one rising-edge synchronous-reset
domain, without claiming all schema expressible configurations are supported.
Actual timing frequencies/constraints remain target-profile facts, not a second
clock-frequency field inside the logical domain.

**Teaching example: boundary only.** This JSON is a design example, not a ready
task, PC, RTL implementation, AI case or frozen research configuration. It fixes
an 8-bit stream boundary; computation, reset cancellation and completion behavior
still need the task's public facts. No behavioral meaning follows from the names.

```json
{
  "rtl_top": "StreamBlock",
  "signature": {
    "parameters": {"W": {"minimum": 1, "maximum": 32}},
    "domains": {
      "d": {"clock": "rising", "reset": {"kind": "sync", "polarity": "active_low"}}
    },
    "ports": {
      "rx": {"kind": "stream", "direction": "input", "protocol": "ready_valid_v1", "payload": {"kind": "uint", "width": {"param": "W"}}, "domain": "d"},
      "tx": {"kind": "stream", "direction": "output", "protocol": "ready_valid_v1", "payload": {"kind": "uint", "width": {"param": "W"}}, "domain": "d"}
    }
  },
  "parameter_values": {"W": 8},
  "abi": {
    "domains": {"d": {"clock": "clk", "reset": "rst_n"}},
    "ports": {
      "rx": {"payload": "in_data", "valid": "in_valid", "ready": "in_ready"},
      "tx": {"payload": "out_data", "valid": "out_valid", "ready": "out_ready"}
    }
  }
}
```

The candidate may name its logical entry `Top` and set its source to
`requirement_boundary`. The future resolver obtains that entry's signature and
parameter environment from this public boundary. The builder emits the required
actual top `StreamBlock`. Direct receives the same public interface facts and
physical pin names without receiving a reference PC or reference RTL.

**Readers/writers inspected and integration order.**

1. `frozen_context.py` currently writes/reads only `episode-pack-v1`;
   `FrozenRequirementContext` has no boundary. Preserve this legacy reader.
2. `generation/context_direct.py`, `generation/context_his.py` and
   `method_adapters.py` consume the old context. New method integration must give
   both method families the same validated v2 public content; no PC-only facts.
3. `ContractRegistry` currently creates validators without an explicit local
   cross-schema resource registry. Future schema reuse must resolve registered
   PC2.1 definitions offline through an allowlist (or verified same-source
   generated definitions), not accidentally fetch a URI or silently fork types.
4. The PC CLI currently reads opaque public bytes and prints partial checks.
   After a versioned public loader is implemented, it should recognize and
   validate that explicit source format before providing the boundary to the
   resolver. Legacy opaque/schema fixtures must not become valid ready tasks.

**Next bounded implementation and acceptance.** First implement and test the
boundary shape as a proposed portion of the v2 public contract, with an explicit
development validation scope. Test a valid example; missing top/interface;
unknown fields; missing/extra top parameter values; invalid ranges; missing
logical port/domain mappings and physical signal collisions. Reuse the fixed
PC2.1 type definitions and their version identity. Split schema-shape checks from
cross-field semantics; success must say boundary-only, not ready or PC-valid.
Then implement source-byte identity, the typed read-only projection and entry
resolution. Formal fact roles, task math, assets, transaction obligations and
qualification must be specified before completing the v2 ready-task reader.

Design verification: extracted the JSON example directly from this section and
validated its `signature` against the locally registered PC2.1
`$defs/signature_fields`: **PASS**. In-memory assertions also passed for exact
parameter-name coverage, concrete value ranges, logical-port/domain mapping
coverage, port-domain references and uniqueness of physical pin names.
`git diff --check`: **PASS**. These are checks of the documented example, not
tests of an implemented boundary schema/loader. This round edited only this
migration record; no PC schema, runtime, task-ready status or research plan changed.

### 12.19 Development public-boundary shape contract (2026-09-16)

Implemented the shape-only part of §12.18. The versioned development wrapper is
`contracts/episode-pack/development-public-boundary-v1.schema.json`, registered
under `development_public_boundary`. It requires `contract_version`, the fixed
scope `boundary_shape_only`, and a closed `boundary` object with `rtl_top`,
`signature`, concrete nonnegative integer `parameter_values`, and `abi`.
Value pin maps use `signal`; stream pin maps require `payload`, `valid`, `ready`;
domain maps require explicit clock/reset names or null. A checked-in example
demonstrates the proposed StreamBlock boundary only, with no task math or ready
claim. The wrapper is a development validation surface for the future v2 public
context, not a new independent requirement authority or complete episode format.

Signature types reference the existing registered PC2.1 `$defs/signature_fields`
and identifiers by URI. `ContractRegistry` now carries an explicit dependency
allowlist, resolves only local resources with `referencing.Registry`, and refuses
unregistered resources without network fallback. Cached validators include the
identities of dependency files. `referencing` is declared as a direct lightweight
dependency. Existing PC schema bytes and v1 episode schema are unchanged.

The runtime route exercised is manifest lookup -> RegisteredContract -> local
dependency resolution -> JSON Schema validation. No new public task loader or
LLM/RTL integration is claimed. The PC CLI still treats source files as opaque
bytes and does not consume this boundary wrapper yet.

Initial focused verification: **PASS, 39 tests**, using
`python -B -m pytest contracts/tests/test_development_public_boundary.py contracts/tests/test_contract_manifest.py contracts/tests/test_pc_2_1_registration.py -q -p no:cacheprovider --tb=short`.
New tests exercise required/unknown fields, complete stream mapping shapes,
concrete top parameters, inherited PC type checks, value mapping/null domain pin
shapes, invalid version/scope, denied external schema retrieval and dependency
cache invalidation. Scope tests explicitly demonstrate that cross-field defects
can still pass shape validation; they are not hardware conformance assertions.
Focused Ruff passed after correcting test import ordering.

Next teaching round: check boundary cross-field relations against its signature,
starting with exact logical/physical mapping coverage and port-kind agreement.
Parameter coverage/ranges, domain/reset pin consistency, reserved names and
physical-name collisions remain separately listed semantic obligations. A
strict source reader, source-byte binding, v2 fact roles/assets/task obligations
and per-instance resolution follow; no boundary-only result grants ready status.

Integrated validation: **PASS, 433 passed in 43.76 s**. Exact command:
`python -B -m pytest contracts/tests agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_pc21_cli.py agent/tests/test_agent_repository_resources.py compatibility_tests/test_active_documentation_paths.py -q -p no:cacheprovider --junitxml=artifacts/migrations/2026-09-16-public-boundary-shape/validation.xml`.
Evidence: `artifacts/migrations/2026-09-16-public-boundary-shape/validation.xml`.
Focused Ruff and `git diff --check`: **PASS**. No model/EDA/FPGA execution,
research-plan edit, commit, staging change or external publication occurred.

### 12.20 Public boundary port mapping semantics (2026-09-16)

Added the scoped public Python entry point
`public_boundary.check_public_boundary_ports(payload, registry=...)`. It invokes
the registered development boundary schema first and returns its diagnostics
immediately on shape failure. For schema-conforming documents it reports missing
and extra ABI port mappings in sorted order, then checks that each common logical
port uses the correct mapping form: `signal` for value; `payload/valid/ready`
for stream. Names are exact/case-sensitive and all errors carry boundary paths.
The function does not mutate source data. An empty diagnostics tuple means only
schema plus these two port rules passed, not full boundary validity or task ready.

Ownership remains method-neutral: this module is outside the PC package, for a
future public-context loader shared by Direct and PC. It is directly callable
and tested as a public API; it is not yet wired into the complete task loader,
model prompts or RTL construction. No schema version or marker was changed.
Domain/clock/reset consistency, physical-name collisions, reserved words and
parameter semantics remain unimplemented.

Validation: `python -B -m pytest agent/tests/test_sr2fpga_public_boundary.py contracts/tests/test_development_public_boundary.py -q -p no:cacheprovider --tb=short`
— **PASS, 39 passed in 1.01 s**. Cases include valid stream and mixed value/stream
ports, missing/extra maps, both mapping-kind mismatches in input/output directions,
stable diagnostics, malformed schema inputs, empty interfaces and input immutability.
Scope tests retain unvalidated domain/collision examples without claiming they
are valid hardware. Focused Ruff: **PASS**.

Next small step: public boundary domain mapping coverage and clock/reset pin
presence consistent with the declared domain. Keep physical-name uniqueness as
a separate explicit check before any RTL emission. No model, RTL or EDA run,
research change, commit or staging operation was performed in this round.

### 12.21 Public boundary domain mapping and pin presence (2026-09-16)

Added `public_boundary.check_public_boundary_domains(payload, registry=...)`
alongside the port checker. It first validates the registered boundary schema,
then checks exact domain-map coverage and each declared domain's consumption:
clock=rising needs a clock name, clock=none needs null; reset=sync/async needs a
reset name, reset=none needs null. A domain with clock=none must declare reset=none,
consistent with the registered PC2.1 domain description and inherited domain
semantics. Errors name the relevant declared-domain or ABI pin path; diagnostics
are ordered by domain name and the payload is not mutated.

This public Python entry point is tested directly, but is not yet part of the
full public task loader. It checks declared pin presence only: async-reset
presence is not async capability qualification, and no waveform/reset/CDC/timing
claim follows. Port-to-domain references, target restrictions, physical-name
collisions and parameter semantics remain separate work. Existing schema and
research definitions were not changed.

Validation: `python -B -m pytest agent/tests/test_sr2fpga_public_boundary.py contracts/tests/test_development_public_boundary.py -q -p no:cacheprovider --tb=short`
— **PASS, 58 passed in 1.69 s**. Cases cover low/high synchronous reset, no reset,
nonconsuming domains, async declaration pin presence, missing/extra mappings,
missing/unwanted pins, clock=none/reset inconsistency, missing null fields,
malformed schema inputs, empty domain tables, ordering and input immutability.
Focused Ruff: **PASS**. These counts include earlier port/shape tests and are not
additional hardware samples. No model, simulation, EDA, commit or staging action.

Next small step: validate that every port's referenced domain exists, preserving
the allowed null domain for value ports. Physical-name uniqueness remains a
separate explicit obligation before RTL generation.

### 12.22 PC2.1 construction and first DW→PW development closure (2026-10-26)

The user authorized completing the PC checker, deterministic RTL structure and
first DW→PW development loop, then selected Codex subagents with at most six
candidate invocations and no output-token ceiling. This is a bounded development
scope; formal studies, held-out scoring, physical implementation and evidence
promotion remain outside it.

Implemented configuration-level parameter expressions/ranges, type/domain/net
semantics, tensor descriptors and finite relations, typed public-source/asset
loading, tensor ABI, deterministic specialization/wiring and real-parser body
composition. Public CLI `validate/build/compose` complements the retained
input-only `assemble/check`. Registered development public context v2, capability,
target and behavior-bundle contracts extend the actual boundaries without
changing PC2.1 or historical contracts.

The fixed N1/H4/W5/Cin3/Cout5/lane2 task has public exact affine arithmetic,
hand-authored nondegenerate weights, an independent integer oracle, separately
implemented RTL control and a trusted complete-transaction monitor. Reference
optimizations used a serial DW MAC while preserving arithmetic, ABI and the
2048-cycle completion bound. Its PC-emitted package passed compilation,
simulation and full generic Yosys synthesis in
`artifacts/paper1-ai/dw-pw-reference-20261026-04/`.

Actual candidate execution used 3 of 6 authorized external subagent invocations:
1 rejected PC schema proposal, 1 PC correction and 1 batch supplying both
behavior units. The three-file RTL FPP passed public compilation, exact
numerical/transaction simulation and full synthesis. The same bytes then passed
terminal development replay with different input values. Each suite completed
3 invocations,180 output beats and2 reset cancellations. These are fixed-task
development checks, not population success rates. No RTL behavior repair was
needed; only the observed PC format correction occurred.

Before any candidate functional result, a monitor defect was corrected: idle
payload bits are unconstrained when valid=0. The original candidate run was
retained and a continuation created with identical public bytes/build identity
and only3 remaining invocations. The revised monitor passed14 narrow tests and
the prior reference trace before generated-candidate evaluation. The continuation
stores the full candidate, source/tool records, construction origins and terminal
file hashes using the existing ArtifactStore/event machinery. Full record:
[DW→PW development run](../../artifacts/paper1-ai/dw-pw-candidate-20261026-02/README.md).

Validation: **603 passed** in the final affected contracts/PC/HDL/resource/docs
suite (`artifacts/paper1-ai/validation-20261026/combined-final.xml`), followed by
**14 passed** on the idle-payload monitor subset and actual candidate/terminal
execution. Suites overlap. Focused Ruff and diff whitespace checks passed.
Icarus access violations inside the sandbox, earlier synthesis timeouts and an
interrupted pipeline remain preserved. Approved external tool execution and
file-backed process-tree timeouts provided the qualified local tool path.

Limitations: the collaboration API cannot enforce candidate filesystem
isolation; public prompts, hash checks and parser boundaries do not prove
private files inaccessible. External subagent invocations are counted, while
provider internal calls/tokens/seed are unavailable. The first final response
was JSON-value-preserving transcription with normalized whitespace; later
responses are exact candidate-written bytes. This remains
`formal_method_conformant=false`, with no official/B4/hidden/L4 authority.
The three-family catalog/evidence ledger has not been promoted; residual/GEMM,
full task qualification, statistical analysis and official execution remain open.
