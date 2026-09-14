# Paper-1 Research Program Workspace

> [Terminology, 2026-09-08](../../specs/2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> currently serialized as System-HIS v1.2; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

This directory contains the reasoning and writing workspace behind the
canonical Paper-1 specification. It supports the specification; it does not
override current code, machine evidence, `current-status.md`, or the English
freeze.

## Workspace Map

The [PC layered-study design v1](../../specs/2026-09-11-pc-layered-study-design-v1.md)
records the user-approved separation of PC generation, frozen-PC 2×2 conditions,
and end-to-end evaluation. It does not relabel historical M3–M5 or authorize execution.

| Path | Role | Status |
| --- | --- | --- |
| [`foundation/research_canon.md`](foundation/research_canon.md) | Frozen literature, repository facts, terminology, and forbidden claims | Design-time foundation snapshot |
| [`foundation/evidence_table.md`](foundation/evidence_table.md) | Claim-to-evidence strength and risk ledger | Design-time claim snapshot |
| [`foundation/g3-provider-seed-capability-probe.md`](foundation/g3-provider-seed-capability-probe.md) | Bounded provider seed-control qualification protocol and 2026-08-26 development diagnostics | Non-official G3 input; no campaign or pass authority |
| [`writing/argument_map.md`](writing/argument_map.md) | Scientific tension, central question, and conditional argument chain | Active writing aid |
| [`writing/section_contracts.md`](writing/section_contracts.md) | Allowed claims and evidence obligations by manuscript section | Active writing aid |
| [`writing/rq5-contract-preserving-ea-design-v1.8.md`](writing/rq5-contract-preserving-ea-design-v1.8.md) | Earlier RQ5 EA conditions and pre-outcome gates | Historical v1.8 design record; no implementation authority |
| [`writing/contract-guided-evolutionary-dse-v1.9-candidate.md`](writing/contract-guided-evolutionary-dse-v1.9-candidate.md) | Hardware-code-generation harness, provenance-typed requirement completion, and EA-core redesign | User-approved candidate direction; `LOGIC-001`, `METH-001`, and `EVID-001` resolved, experiment-protocol review remains open |
| [`writing/v1.9-discussion-ledger-and-next-chat-handoff-2026-09-10.md`](writing/v1.9-discussion-ledger-and-next-chat-handoff-2026-09-10.md) | Consolidated confirmed decisions, discussion-only proposals, open blockers, and copy-paste continuation prompt | Active handoff authority for the v1.9 design discussion; does not override canonical v1.8 |
| [`writing/style_guide.md`](writing/style_guide.md) | Terminology and result-language rules | Active writing aid |
| [`audit/v1.9-related-work-feature-audit-2026-09-10.md`](audit/v1.9-related-work-feature-audit-2026-09-10.md) | Full-text feature matrix for twelve closest LLM/RTL/FPGA-DSE works plus traditional-DSE anchors | Active v1.9 novelty and baseline audit; no experiment authority |
| [`audit/qa_report.md`](audit/qa_report.md) | Review that produced the 2026-08-14 program design | Historical design-QA snapshot |
| [`audit/qa_report-v1.7.md`](audit/qa_report-v1.7.md) | 2026-08-27 RQ1 hierarchy, multiplicity, power, and propagation review | Active v1.7 design-QA record; no outcome evidence |
| [`audit/qa_report-v1.6.md`](audit/qa_report-v1.6.md) | 2026-08-26 decoding-control and provider-capability revision ledger | Historical v1.6 amendment record |
| [`audit/qa_report-v1.5.md`](audit/qa_report-v1.5.md) | Earlier 2026-08-26 protocol-coherence review | Historical v1.5 design-QA snapshot |
| [`state.json`](state.json) | Research-writing workflow and gate metadata | Derived metadata, not authority |

## Scope

- Project: SR2FPGA Paper 1 research program
- Mode: hybrid (reconcile an existing research program, then compose a new canonical specification)
- Text type: research specification and experiment contract
- Target reader: project owner, implementation agents, EDA/LLM researchers, and later manuscript reviewers
- Language: Chinese-first with stable English technical terms
- Deliverable scope: repository-wide documentation audit, research canon, evidence table, argument map, manuscript/experiment section contracts, and one canonical Paper-1 spec
- Revision baseline: `paper1-v1.8`, adopted by user request on 2026-09-07 and kept open for further research-program revision. It adds RQ5 contract-preserving EA versus equal-budget random search while retaining M0--M5 and all execution gates.
- Evidence cut-off: implementation/evidence review on 2026-08-26; v1.7 is a pre-outcome protocol amendment dated 2026-08-27, while the `foundation/` evidence snapshot remains dated 2026-08-14
- Repository baseline: local `develop` at `bd516c110862`; the locally known `origin/develop` ref matched, without implying remote CI, review, or merge verification
- Archive after confirmation: no automatic archive, deletion, release, commit, or push

## Authority boundary

The 2026-09-07 v1.8 EA amendment in the English specification governs the
current status. It adds a research-design-only RQ5 and requires EA-G3 through
EA-G4b before official execution. Previous v1.7 QA and M3/M4 audits retain
their original scope and require affected-scope review. The amendment does not
authorize implementation, model runs, G5, or official campaigns.

The canonical Paper-1 research question and experimental protocol are defined by
[`2026-08-14-sr2fpga-paper1-research-program-design.md`](../../specs/2026-08-14-sr2fpga-paper1-research-program-design.md).
This foundation bundle records why that spec is defensible. It does not override:

- machine contracts registered by [`contracts/manifest.json`](../../../contracts/manifest.json);
- current runtime behavior and tests;
- artifact-backed evidence in the task ledger and committed reports; or
- the System-HIS v1.2 schema semantics that remain valid after contract harmonization.

The canonical spec retains the v1.6 separation of replicate identity, provider
requested-seed provenance, and local schedule randomization, with a G4b choice
between documented seed control and stochastic blocked execution. Its 2026-08-27
v1.7 amendment makes `M4-M3` and `M4-M0` the two-member primary RQ1 Holm family
and makes `M3-M2` a mandatory secondary estimation contrast. It keeps RQ3/M6
and all model training outside Paper-1, retains the separate RQ2 Holm family,
defines positive artifact-derived G3 acceptance and paired-block execution, and
makes target-profile adaptation an optional separately frozen extension. The
2026-08-14 foundation files, the original QA snapshot, and the v1.5/v1.6 QA
records remain historical; their implementation facts and prior inferential
orders are not rewritten and do not override v1.8.

When these sources disagree, the disagreement is a blocking research debt, not a
license to select the most convenient interpretation.

## v1.9 consolidated candidate protocol — 2026-09-11

The current design-level protocol is the consolidated section in
[the v1.9 candidate](writing/contract-guided-evolutionary-dse-v1.9-candidate.md).
[D1-D29 in the ledger](writing/v1.9-discussion-ledger-and-next-chat-handoff-2026-09-10.md)
preserve individual confirmations. The user has delegated routine methodological
judgment; newly resolved design choices are labeled draft judgments, not invented
individual confirmations or operational freeze authority.

- LLM+EA optimizes requirement-constrained PPA; single/multi-FPGA design is in
  scope, without default board-count priority. Resources remain separate and
  power/energy have explicit system and evidence boundaries.
- Track G reports all generation attempts and costs. Track O compares qualified
  methods on a common public-feasible seed; its results remain conditional.
- Seal the final public Pareto set, validate every member once, and compute
  primary terminal NHV from the passing subset. Public NHV is process evidence.
  Complete terminal evaluation with no passing members gives zero.
- Draft seed-reference policy registers a separate seed check before terminal
  outcomes. A failed/unscorable seed makes its improvement increment unavailable;
  a passing seed can have a negative increment if the final scored set is worse.
  No outcome-dependent seed backfill or selected-project replacement is allowed.
- Draft normalization fixes objectives, directions, region and reference within
  each comparison; incompatible signatures are not pooled automatically.
  Unresolved terminal members yield missing scores and sensitivity bounds, not
  automatic failure or zero.
- Draft independent unit is the audited semantic requirement cluster; profiles,
  replicates and Design Points are nested. Pair methods, aggregate within
  compatible strata, and retain family-level reporting.
- Atomic D-/P- labels replace old S0-S3/P0 in candidate tables only. Realization
  fairness and external native-smoke/adapter qualification remain prerequisites.
- Draft primary algorithmic budget counts candidate-construction attempts,
  including repairs/rejections/duplicates, with separate safety ceilings. This
  does not establish equal compute or dollars. Report actual shared,
  standalone-attributed and incremental costs.

Hardware/link inventory, tool qualification, exact signatures/anchors, operational
budget limits, pilot-based precision/effect/multiplicity/power and signed
propagation are still open. The prospective gate sequence is a design dependency
map, not replacement authority. EXPT-PROTOCOL-001, EXPT-FAIR-001 and EVID-002 are
not closed. Canonical v1.8, the separate PC study, LaTeX, code and contracts remain
unchanged. No model, QoR pilot, terminal evaluation or experiment is authorized.

Design refinement 2026-09-12 adds task/platform records, realization-parity
crosswalks and a two-stage excluded-pilot specification in candidate sections
12-15. D30 removes task-family, board-model/count, homogeneous-device and link-type
restrictions from general design. Workload semantics and a finite device/link
graph are inputs; example families are illustrative. Specific experiments still
freeze actual configurations and qualified evidence, not universal support. D-MAP-ONLY isolates fixed-compute placement from joint
architecture freedom. TAPA-CS/RePart receive bounded source-level scope checks,
not claim-ready promotion or runnable-baseline status. Physical/power evidence,
objective anchors, budgets and calibration remain unresolved. No pilot or
implementation was run or authorized.

Three-object principle D31 (confirmed 2026-09-12): requirements define accepted
obligations, the platform graph defines external device/link facts, and the
architecture proposal defines searchable realization/placement choices.
Available hardware is input; active devices and work distribution are outputs.
Candidate section 16 specifies field responsibilities, DSC/DP/PC/FPP mapping,
constraint closure and a change-to-check matrix. Every modified/repaired child
still needs full public acceptance; affected system/physical evidence is renewed.
The detailed matrix is an analyst design specification, not implemented schemas,
verified checker capabilities, or execution authority.

Empirical focus D32 (confirmed 2026-09-14): study AI accelerators implemented on
FPGAs, not ASIC tapeout, while preserving generic LLM+EA/DSC and requirement/
platform/architecture separation. Section 17 adds AI numerical/workload
contracts, compute-memory-communication design variables, operator/subgraph/
system evidence levels and task-aware baseline roles. Existing generic RTL
examples are qualification references, not complete AI accelerator evidence.
Workload/model choice, precision/tolerance, objectives and measurement remain
to be fixed. No preset device/count cap, training, implementation or run is
authorized; canonical v1.8 and the independent PC study remain unchanged.

## Problem being solved

The product north star is to turn a possibly incomplete, ambiguous, or
unsupported requirement into either a coherent FPGA project with independent
evidence or an honest bounded stop. Paper 1 separately tests the shared
requirement boundary on a sealed ambiguity audit, then determines whether the
deterministic materialization/edit-surface bundle and the complete untrained
Project Contract pipeline improve method-neutral verified project success
(`VPP-L3@1`) relative to matched free-generation and Direct controls. The
representation bundle remains a secondary
mechanism estimate. Oracle-separated repair/evaluation is the second
confirmatory line under the same facts, model, tools, and budget.

## Required deliverables

1. One stable ambiguity-audit and benchmark protocol with frozen information
   privileges, requirement/default/capability policies, edit
   surfaces, budgets, splits, tool versions, and outcome definitions.
2. A matched baseline ladder that includes a HORIZON-motivated direct repair
   control and does not call it HORIZON-like until the required semantics exist.
3. Reproducible M0-M5 episode, repair, cost, missingness, and hidden-outcome
   artifacts with held-out evaluators excluded from candidate/repair context.
4. A representative, secondary OpenXC7 L4 confirmation. Signed target-profile
   pairs and complete-pair `TPA-L4` are required only if the separately frozen
   optional extension is enabled.
5. A claim ledger that can support a TRETS paper when Project Contract or repair effects
   are negative.
6. An RQ5 EA design/lineage record that preserves public-fitness-only selection
   and one-shot hidden terminal evaluation.

## Constraints

- Training support is retained infrastructure outside Paper-1; no Paper-1 model
  is trained.
- Current Phase D evidence is a valid negative pilot: 24/24 episodes completed,
  but 0/24 reached L0 and no repair was attempted.
- Current physical evidence consists of two representative OpenXC7 post-route L4
  passes; Vivado and L5 have no passing evidence.
- G1 Project Contract/common-project conformance and G2 catalog/evidence semantics are
  locally closed on this checkout; neither is a model or research outcome.
- Development/excluded Runner paths now exercise sealed, final-only hidden
  conformance, but no signed official hidden/VPP producer or G4b authorization
  surface exists. Development artifacts remain non-official.
- A method-neutral project contract, provenance-bearing requirement boundary,
  and development ambiguity-audit chain exist; signed audit fixtures, official
  execution, and positive gate authority under the active freeze remain absent.
- M2-M5 development Runner paths and several artifact-derived scenario reducers
  exist, but positive G3 gate authority, full paired-block/seed closure, shared-
  cost reconciliation, remaining project-repair/missingness scenarios, and
  official method-neutral VPP remain incomplete.
- Official generation must not read deterministic generator implementations,
  trusted testbenches, hidden oracles, held-out reference projects, or dataset
  payloads.
- Closed-API and local-model conditions must be reported separately when logit
  access or constrained decoding changes their capabilities.

## Explicit non-goals for Paper 1

- claiming that repository-level agentic RTL repair is new;
- claiming general requirement-to-bitstream-to-board automation;
- making L5, broad Vivado closure, QoR prediction, RL architecture search, or
  Tier-B logit-masked decoding mandatory for the minimum paper;
- training or fine-tuning a model, or claiming a learned treatment;
- treating application-themed shells as proof of application-level RL, vision,
  radar, or SoC realism; or
- rewriting dated plans so they appear to have predicted the current design.

## Done condition

The research design is ready to guide implementation now, but it is ready for
outcome-producing execution only after a positive non-official G3 acceptance
artifact, core G4a manifests, the natural excluded G5 pilot, and an independently
verified G4b authorization receipt. The two-member RQ1 Holm family, secondary
M3-M2 reporting contract, separate RQ2 Holm family, RQ1 gate-conditional full-
claim joint-power rule, RQ2 Holm-adjusted marginal-power rules, equal-family
estimators,
missingness rules, and cost reducers must be frozen,
and every intended TRETS claim must map to a named artifact or remain a
hypothesis. Model training and an optional target-profile extension are not part
of the minimum done condition.
