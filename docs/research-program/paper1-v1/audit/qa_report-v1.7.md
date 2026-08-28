# Paper-1 v1.7 RQ1 Confirmatory-Hierarchy Review

Status: active pre-outcome protocol-amendment record. The English
`paper1-freeze-v1.7` remains authoritative. This review is not an experiment
result, G3 acceptance artifact, G4b authorization, or permission to run G5 or an
official campaign.

## Amendment timing and scope

The amendment was recorded on 2026-08-27 while G3 remained partial, the G4b
verifier remained missing, and no G5 natural-model or official outcome had been
opened. It changes only the RQ1 confirmatory hierarchy and the corresponding
test, power, result-table, and claim contracts.

It preserves the benchmark population, M0-M5 methods, `VPP-L3@1` endpoint,
information privileges, budgets, equal-family estimator, complete signed data-
collection matrix, RQ2 Holm family, RQ0 audit, descriptive RQ4/OpenXC7 analysis,
gate order, no-training scope, and optional target-profile extension.

## v1.7 decisions

1. `M4-M3` and `M4-M0` form the two-member primary RQ1 Holm family at one-sided
   familywise alpha 0.05.
2. `M4-M3` estimates the deterministic-materialization/edit-surface bundle on
   the same frozen System-HIS. It is not a skeleton-text-only effect.
3. `M4-M0` estimates untrained end-to-end System-HIS value and does not isolate a
   component.
4. Each primary comparison can activate only its matching local claim. The
   complete RQ1 claim requires both primary claim-activation rules to pass.
5. `M3-M2` remains mandatory but is a prespecified secondary representation-
   bundle estimate. It receives no confirmatory p-value by default and cannot
   rescue a failed primary comparison.
6. RQ1 and RQ2 retain separate Holm families. Alpha is not recycled between
   them, and no paper-wide 0.05 familywise-error claim follows from their separate
   control.
7. Multiplicity controls inference, not data collection. Every signed eligible
   M0-M5 condition is still executed and reported.

## Estimand and test audit

The independent unit remains `semantic_instance_id`. Planned replicates,
requested decoding seeds, paraphrases, and hidden-case seeds do not increase the
independent sample size. Each RQ1 effect is a replicate-averaged paired risk
difference, averaged within family and then equally across the four frozen
families.

The primary nulls are:

- `H0_43: Delta_43 <= delta_min_materialization`;
- `H0_40: Delta_40 <= delta_min_system`.

The confirmatory test must resample complete semantic-instance clusters within
family, retain all planned replicates and method outcomes together, and keep
equal-family weights fixed. G4a must freeze the studentized statistic, boundary-
null centering, interval form, number of resamples, analysis seed, tie and
extreme-case handling, and code hash; G4b signs that implementation unchanged.

An ordinary McNemar test over replicate blocks would use the wrong independent
unit. A cluster-swap test may be called finite-sample exact only when an
independent review establishes whole-cluster label exchangeability. Such a test
addresses its declared sharp null and does not replace the nonzero minimum-
effect threshold test. Independent sign flips at replicate, requested-seed,
paraphrase, or hidden-case level are not permitted.

## Claim rule and power audit

For each primary contrast `c`, define the statistical-success indicator `S_c=1`
only when both of the following hold:

1. the RQ1 Holm procedure rejects `H0_c`;
2. the two-sided 95% confidence-interval lower endpoint is strictly above the
   frozen `delta_c`.

Define `G_RQ1=1` only when integrity, leakage, information, budget, hidden-
completion, and infrastructure-missingness gates applicable to RQ1 pass. The
claim-activation indicator is `C_c=1` if and only if `S_c=1` and `G_RQ1=1`.

The result language is therefore:

| Decision | Maximum supported RQ1 claim |
| --- | --- |
| `C_43=1`, `C_40=1` | Complete RQ1: materialization/edit-surface increment and end-to-end system value |
| `C_43=1`, `C_40=0` | Materialization/edit-surface increment only |
| `C_43=0`, `C_40=1` | End-to-end system value only; no component attribution |
| `C_43=0`, `C_40=0` | No confirmatory RQ1 method-value claim |

Before G5 outcomes, G4a freezes each primary minimum effect and a design
alternative strictly above it. The final joint simulation must reproduce the
complete Holm-plus-confidence-bound rule, shared-M4 covariance, family and
replicate dependence, selected decoding-control mode, attrition, missingness,
repair eligibility, and design-outcome coding within the frozen gate-valid
envelope. Claim-invalidating gate failures receive no speculative occurrence
probability in the power model. If the complete RQ1 claim is retained, the
target is `P(S_43=1 and S_40=1 | G_RQ1=1) >= 0.80`, with both conditional
marginal powers also reported; a realized `G_RQ1=0` invalidates claim activation.
Each retained RQ2 confirmatory contrast separately targets at least 0.80 Holm-
adjusted marginal power under its frozen design alternative and applicable
gate-valid envelope; RQ2 imposes no joint-both-contrasts success rule. The v1.6
planning result cannot be inherited after the multiplicity change.

If the resource ceiling cannot support a retained confirmatory claim, G4b must
downgrade that claim before official execution. It may not expand the official
set, replace families, stop early, or report observed power after outcomes.

## Propagation and historical-integrity audit

| Surface | v1.7 obligation | Status |
| --- | --- | --- |
| English and Chinese freeze | Same primary family, secondary role, power and claim rules | Synchronized |
| Code-development spec | Bind v1.7 authority and campaign-analysis fields | Synchronized as design debt |
| Current status and specs index | Name v1.7 without changing empirical status | Synchronized |
| Workspace README and state | Point to v1.7 and this QA record | Synchronized |
| Argument map, section contracts, style guide | Use the accepted RQ1 hierarchy and causal wording | Synchronized |
| Repository, module, config, reports, datasets, reference, and app indexes | Route protocol, current status, historical evidence, non-Paper-1 infrastructure, and demo roles without creating authority | Synchronized |
| v1.5/v1.6 QA and 2026-08-14 foundation | Preserve historical body; update current-authority banners only | Preserved |

The 2026-08-27 repository-wide refresh checked every active protocol-bearing
README, navigation, status, specification, workspace, and QA surface. Generated
ledger views and named-run reports remain evidence for their declared scope;
their enclosing indexes explicitly prevent catalog labels or historical results
from becoming current protocol or official Paper-1 outcomes.

The v1.6 seed-control amendment remains valid history and active inherited
protocol content. Its `replicate_id`, requested-seed provenance,
`execution_schedule_seed`, and single-mode G4b rule are unchanged. Historical
QA and foundation text is not rewritten to imply that it anticipated v1.7.

## Remaining author and gate inputs

The amendment deliberately does not invent:

- numeric `delta_min_materialization` or `delta_min_system` values;
- their design alternatives;
- the final studentized test and interval implementation;
- pilot nuisance parameters, sample size, runtime, token cost, or storage need;
- provider decoding-control eligibility;
- repair-probe minima; or
- G4b signatures and authorization.

Those values follow the G3 -> G4a -> excluded G5 -> G4b dependency chain. Until
that chain closes, the official campaign remains no-go and every RQ1/RQ2 effect
remains a hypothesis.

## Verdict

The v1.7 research-design and derived-document synchronization is complete. The
amendment improves alignment between the central scientific claims and the
confirmatory family without changing methods or data collection. It creates no
implementation, empirical, G3, or G4b evidence.
