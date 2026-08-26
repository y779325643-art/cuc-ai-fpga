# QA report

> **Status: 2026-08-14 program-design QA snapshot.** Counts and repository
> inventory below describe the pre-cleanup review that produced the research
> freeze; they are not current validation totals. Use
> [current status](../../../current-status.md) for mutable facts and the
> [English Paper-1 freeze](../../../specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
> for the active `paper1-freeze-v1.6` protocol. This report predates v1.5;
> training-related QA below is historical only. See
> [`qa_report-v1.6.md`](qa_report-v1.6.md) for the current decoding-control and
> protocol-coherence review.

## Review scope

- Artifact reviewed: canonical Paper-1 research-program spec plus the research
  foundation, documentation indexes, current-status guidance, HORIZON reader,
  current code/contracts/evidence, and the complete pre-existing `docs/`
  population.
- Review modes: researchwrite argument/evidence QA, adversarial experimental-
  design review, code-feasibility mapping, documentation/navigation QA, and
  statistical-design audit.
- Evidence cut-off: 2026-08-14 local checkout and working-tree documentation.
- Boundary: this QA validates the **program design**. It does not validate a
  campaign, trained model, held-out outcome, or physical result that does not yet
  exist.

## Rubric

| Dimension | Score / 10 | Basis |
|---|---:|---|
| Research-question clarity | 9.2 | One central question, four falsifiable RQs, and result-contingent exits |
| Scientific tension | 9.1 | HORIZON makes repository repair a strong baseline; the remaining typed/hidden/learning gap is explicit |
| Evidence match | 9.1 | Implemented, verified, target, and forbidden claims are separated and tied to current artifacts/code |
| Logic chain | 8.9 | Direct, untyped, HIS-free, skeleton, repair, and three training views close the main alternative explanations |
| Method feasibility | 8.1 | Ordered gates are executable in principle, but M2/M3, hidden separation, episode contracts, and two oracles remain unimplemented |
| Innovation framing | 8.6 | Novelty is the tested combination and learning effect, not generic agent/tool-loop claims |
| Risk boundary | 9.5 | Hidden leakage, missingness, retries, family scope, survivor bias, and negative-result tracks are explicit |
| Language/terminology | 8.8 | Method-neutral VPP, bounded HORIZON wording, and stable project/EDA terminology are consistent |

**Mean score: 8.9 / 10.** The foundation exceeds the 7.5 readiness threshold
and the program spec exceeds the 8.0 final-polish threshold. Experiment execution
does not pass its own gates yet.

## Major issues found and resolved in the spec

1. The former hidden oracle could use candidate testbench material and return
   diagnostics to repair. The spec now requires an evaluator-owned public/hidden
   split, one hidden run on an immutable terminal candidate, common hidden seeds,
   and leakage spy tests.
2. The former HVPP required H0-H2 for untyped baselines. The headline metric is
   now method-neutral `VPP-L3`; H-stages are mechanism outcomes only for methods
   that emit System-HIS.
3. M2, M3, independent semantic-instance loading, and first-class method/episode
   contracts do not exist. G3 now makes them hard acceptance requirements.
4. M3-M2 and M5-M1 were overinterpreted as isolated causal mechanisms. The spec
   now labels bundled/end-to-end estimates, reuses identical HIS for M3-M4, and
   adds a paired generic-versus-HIS repair-policy probe on the same failed project.
5. A single learned condition could not attribute gains to verification or
   trajectories. The design now uses matched M6U outcome-blind, M6F verified-
   final, and M6T verified-trajectory views, with at least three training seeds
   for Track A.
6. Internal retries broke `@1` and budget matching. All retries are now explicit
   events under global call/token/tool/time budgets; `@1` is one call per declared
   stage.
7. Requirements, paraphrases, decoding seeds, training seeds, and families were
   not fully separated statistically. `semantic_instance_id` is the benchmark
   unit; repeats stay nested; inference is conditional on the four named
   held-out families.
8. Failure, infrastructure missingness, visible/hidden eligibility, physical
   survivor bias, and total failed-episode cost now have predeclared handling.

## Statistical contract readout

- Independent benchmark unit: `semantic_instance_id`.
- Repeated measurements: paraphrases, hidden-case seeds, and decoding seeds.
- Training replication: at least three independently trained checkpoints per
  claimed learned treatment; checkpoint-specific effects remain visible.
- Primary aggregation: within-instance pairing, equal-family macro average over
  the four named families, nested stratified cluster bootstrap.
- Confirmatory learning order: M6F–M4, M6F–M6U, then M6T–M6F only for a trajectory
  claim; fixed two-sided 0.05 gatekeeping.
- RQ2 multiplicity: Holm control for the two predeclared repair comparisons.
- Cost: total resources for all episodes are primary; time to success is capped/
  right-censored; an efficiency claim requires correctness non-inferiority first.

## AUTHOR_INPUT_NEEDED at G4b

These values must come from scientific judgment plus the excluded G5 pilot and
must be frozen before any official outcome. They were deliberately not invented:

- numeric `delta_min` and its practical rationale;
- correctness non-inferiority margin for M6T/M6TR versus M1;
- final semantic-instance sample size and target precision/power;
- primary cost axis and conversion/accounting rule;
- global model/token/tool/time budgets and fixed infrastructure retry count;
- unresolved-infrastructure rate/imbalance abort thresholds;
- exact base model, tokenizer, quantization, prompts, gateway/cache policy, and
  tool versions; and
- minimum real repair-transition count required to activate M6T.

## Validation snapshot at program-design freeze

- The review covered the pre-cleanup 104-path `docs/` population.
- At that snapshot, 57 local Markdown links resolved and six `docs/` JSON files
  parsed.
- At that snapshot, `git diff --check` reported no whitespace error and the
  full local regression passed 1,060 tests plus 349 subtests.
- The snapshot recorded a generated Markdown table-separator defect and routed
  it to G2; current disposition must be checked against the renderer and task
  ledger rather than inferred from this report.

## Reviewer-risk note

A reviewer may still challenge the limited number and deliberate selection of
held-out families, the feasibility of producing independent semantic instances,
the stability of three training seeds, and the physical subset. The spec bounds
all current inference to the four named families, requires pilot-based sample-
size justification, exposes checkpoint-level results, and treats L4 as a
confirmatory depth analysis. Broader claims require a larger family-level design.

## Stop decision and next action

The design/documentation objective is complete enough to stop revising prose.
Outcome evidence is absent by design, and further numerical specification would
invent pilot/model facts. The next action is G1 System-HIS contract closure,
followed by G2 and G3. No model campaign, training run, or official benchmark run
is authorized before the signed G4b freeze.
