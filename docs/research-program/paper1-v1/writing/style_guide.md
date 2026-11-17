# Style guide

> [Terminology, 2026-09-08](../../../specs/2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> now serialized as `sr2fpga-pc-2.1`; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

- Language: Chinese for project guidance; retain stable English identifiers,
  metric names, method labels, and file paths.
- Target reader: expert EDA/LLM collaborators and later reviewers.
- Tone: scientific-question-driven, conservative about results, explicit about
  engineering feasibility.
- Citation style: cite the exact local source/artifact during planning; use
  verified bibliographic records in the manuscript.

## Required terminology

- Use **Design-Space Contract (DSC)** for the design space, **Design Point (DP)**
  for one candidate, **Project Contract (PC)** for its engineering obligations,
  and **FPGA Project Package (FPP)** for the generated package.
- Introduce PC once as serialized by the current implementation as
  **System-HIS v1.2**. Retain that name only for format compatibility, identifiers
  and historical attribution. Do not rename internal `system_his` symbols.

- Use **project generation**, not “project synthesis,” for model output.
- Use **logic synthesis** or **L3 synthesis** for Yosys.
- Use **method-neutral verified project success (`VPP-L3@1`)** for the RQ1
  primary endpoint; hidden conformance is one required component, not the whole
  endpoint.
- Use **deterministic materialization/edit-surface bundle** for the primary
  M4-M3 estimand. It is a joint intervention unless a separately frozen
  orthogonal control isolates one component.
- Use **untrained end-to-end Project Contract value** for the primary M4-M0 estimand;
  do not attribute that system-level difference to one component.
- Use **Project Contract representation bundle** for the secondary M3-M2 estimand; use
  **typed requirement/project contract** only when explaining the
  representation's engineering role, never as a “typing alone” causal claim.
- Use **episode pack** for run control and information privileges.
- Use **HORIZON-motivated Direct-Repair control** until the minimum local
  HORIZON-like semantics are implemented; reserve “reproduction” for the
  original released protocol.
- Use **verified project pass (VPP)** only for the method-neutral frozen composite
  metric in the canonical spec; keep H-stage outcomes conditional on PC methods.
- Use **Target-Profile Adaptation Pass through L4 (`TPA-L4`)** only when the
  optional extension was enabled before outcomes and for a complete signed pair
  whose members preserve declared functional invariants, satisfy profile-
  specific contracts/change policies, and pass the required L3/L4.
- Use **replicate block** only when semantic instance, replicate ID, shared
  initial artifacts, hidden commitment, execution schedule, and cost attribution
  all match the active freeze. Treat requested decoding seed as separate
  provenance and `execution_schedule_seed` as local order control.
- Use `implemented`, `verified`, `target`, `hypothesis`, `not_run`,
  `infrastructure_failure`, and `design_failure` as distinct states.
- Use `ready`, `needs_clarification`, and `capability_gap` for requirement
  disposition. A correct disposition is not a project pass; `not_run` is an
  infrastructure/execution state, not a semantic refusal label.

## Forbidden or restricted expressions

- Avoid “first,” “complete,” “guaranteed,” “production-ready,” “board-ready,”
  “generalizable,” and “state of the art” without direct, scoped evidence.
- Do not write “24/24 L4,” “all mutation qualified,” “H3 24/24 pass,” or
  present compatibility-layer removal as a scientific result.
- Do not use `APPROVED` without naming the audit scope.
- Do not call target-catalog intent current evidence.
- Do not use application names as evidence of application realism.
- Do not claim that a bounded ambiguity audit resolves arbitrary incomplete or
  open-world requirements, and do not call an audit disposition VPP.
- Do not call a single profile pass, a baseline-only result, or survivor-only
  analysis target-profile adaptation or cross-platform portability.

## Result grammar

- Present tense: stable code/contract facts.
- Past tense: a named completed run and its bounded outcome.
- Future/conditional: proposed experiment or expected mechanism.
- Every numeric result must include its denominator, population, tool stage, and
  treatment; every missing stage must remain `not_run` with a reason.

## Comparison grammar

Write comparisons as:

> Under the same base model, requirement information, public feedback, attempt
> budget, and tool flow, treatment X changed metric Y by Z with interval I on the
> frozen held-out set.

If any privilege differs, name it in the same sentence and do not call the
comparison matched.

For RQ1, name the exact supported scope: M4-M3 may support only the
materialization/edit-surface claim, M4-M0 may support only the end-to-end system
claim, and the complete RQ1 claim requires both primary claim-activation rules.
M3-M2 remains secondary and cannot rescue either primary comparison.
