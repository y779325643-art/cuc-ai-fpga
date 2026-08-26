# Paper-1 Research Program Workspace

This directory contains the reasoning and writing workspace behind the
canonical Paper-1 specification. It supports the specification; it does not
override current code, machine evidence, `current-status.md`, or the English
freeze.

## Workspace Map

| Path | Role | Status |
| --- | --- | --- |
| [`foundation/research_canon.md`](foundation/research_canon.md) | Frozen literature, repository facts, terminology, and forbidden claims | Design-time foundation snapshot |
| [`foundation/evidence_table.md`](foundation/evidence_table.md) | Claim-to-evidence strength and risk ledger | Design-time claim snapshot |
| [`foundation/g3-provider-seed-capability-probe.md`](foundation/g3-provider-seed-capability-probe.md) | Bounded provider seed-control qualification protocol and 2026-08-26 development diagnostics | Non-official G3 input; no campaign or pass authority |
| [`writing/argument_map.md`](writing/argument_map.md) | Scientific tension, central question, and conditional argument chain | Active writing aid |
| [`writing/section_contracts.md`](writing/section_contracts.md) | Allowed claims and evidence obligations by manuscript section | Active writing aid |
| [`writing/style_guide.md`](writing/style_guide.md) | Terminology and result-language rules | Active writing aid |
| [`audit/qa_report.md`](audit/qa_report.md) | Review that produced the 2026-08-14 program design | Historical design-QA snapshot |
| [`audit/qa_report-v1.6.md`](audit/qa_report-v1.6.md) | 2026-08-26 decoding-control and provider-capability revision ledger | Active v1.6 design-QA record; no outcome evidence |
| [`audit/qa_report-v1.5.md`](audit/qa_report-v1.5.md) | Earlier 2026-08-26 protocol-coherence review | Historical v1.5 design-QA snapshot |
| [`state.json`](state.json) | Research-writing workflow and gate metadata | Derived metadata, not authority |

## Scope

- Project: SR2FPGA Paper 1 research program
- Mode: hybrid (reconcile an existing research program, then compose a new canonical specification)
- Text type: research specification and experiment contract
- Target reader: project owner, implementation agents, EDA/LLM researchers, and later manuscript reviewers
- Language: Chinese-first with stable English technical terms
- Deliverable scope: repository-wide documentation audit, research canon, evidence table, argument map, manuscript/experiment section contracts, and one canonical Paper-1 spec
- Desired version: `paper1-freeze-v1.6` execution-guiding freeze for ACM TRETS; empirical claims remain conditional until experiments finish
- Evidence cut-off: protocol/current-checkout review on 2026-08-26; the `foundation/` evidence snapshot remains dated 2026-08-14
- Repository baseline: local `develop` at `bd516c110862`; the locally known `origin/develop` ref matched, without implying remote CI, review, or merge verification
- Archive after confirmation: no automatic archive, deletion, release, commit, or push

## Authority boundary

The canonical Paper-1 research question and experimental protocol are defined by
[`2026-08-14-sr2fpga-paper1-research-program-freeze-design.md`](../../specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md).
This foundation bundle records why that spec is defensible. It does not override:

- machine contracts registered by [`contracts/manifest.json`](../../../contracts/manifest.json);
- current runtime behavior and tests;
- artifact-backed evidence in the task ledger and committed reports; or
- the System-HIS v1.2 schema semantics that remain valid after contract harmonization.

The canonical spec's 2026-08-26 v1.6 amendment updates the active argument map,
section contracts, and workflow state in this workspace. It keeps RQ3/M6 and
all model training outside Paper-1, makes RQ1/RQ2 the primary empirical line,
defines positive artifact-derived G3 acceptance and paired-block execution, and
makes target-profile adaptation an optional separately frozen extension. It
also separates replicate identity, provider requested-seed provenance, and
local schedule randomization, with a G4b choice between documented seed control
and stochastic blocked execution. The
2026-08-14
`foundation/` and `audit/` files remain explicitly historical design snapshots;
their old implementation facts and confirmatory ordering are not silently
rewritten and do not override v1.6.

When these sources disagree, the disagreement is a blocking research debt, not a
license to select the most convenient interpretation.

## Problem being solved

The product north star is to turn a possibly incomplete, ambiguous, or
unsupported requirement into either a coherent FPGA project with independent
evidence or an honest bounded stop. Paper 1 separately tests the shared
requirement boundary on a sealed ambiguity audit, then determines whether the
System-HIS representation bundle, deterministic skeleton choices, and
oracle-separated repair/evaluation improve project-level correctness or cost
relative to matched direct, untyped, and repository-repair controls under the
same facts, model, tools, and budget.

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
5. A claim ledger that can support a TRETS paper when System-HIS or repair effects
   are negative.

## Constraints

- Training support is retained infrastructure outside Paper-1; no Paper-1 model
  is trained.
- Current Phase D evidence is a valid negative pilot: 24/24 episodes completed,
  but 0/24 reached L0 and no repair was attempted.
- Current physical evidence consists of two representative OpenXC7 post-route L4
  passes; Vivado and L5 have no passing evidence.
- G1 System-HIS/common-project conformance and G2 catalog/evidence semantics are
  locally closed on this checkout; neither is a model or research outcome.
- Development/excluded Runner paths now exercise sealed, final-only hidden
  conformance, but no signed official hidden/VPP producer or G4b authorization
  surface exists. Development artifacts remain non-official.
- A method-neutral project contract, provenance-bearing requirement boundary,
  and development ambiguity-audit chain exist; signed audit fixtures, official
  execution, and v1.6 positive gate authority remain absent.
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
- making L5, broad Vivado closure, QoR prediction, GA/RL architecture search, or
  Tier-B logit-masked decoding mandatory for the minimum paper;
- training or fine-tuning a model, or claiming a learned treatment;
- treating application-themed shells as proof of application-level RL, vision,
  radar, or SoC realism; or
- rewriting dated plans so they appear to have predicted the current design.

## Done condition

The research design is ready to guide implementation now, but it is ready for
outcome-producing execution only after a positive non-official G3 acceptance
artifact, core G4a manifests, the natural excluded G5 pilot, and an independently
verified G4b authorization receipt. The equal-family M0-M5 comparisons, stopping
rules, missingness and cost reducers must be frozen, and every intended TRETS
claim must map to a named artifact or remain a hypothesis. Model training and an
optional target-profile extension are not part of the minimum done condition.
