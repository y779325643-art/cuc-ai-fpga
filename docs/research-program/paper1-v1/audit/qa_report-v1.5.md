# Paper-1 v1.5 Protocol-Coherence Review

> Review date: 2026-08-26
> Scope: research-plan and experiment-contract coherence only
> Outcome authority: none; this review contains no model, official hidden, RQ,
> L4 campaign, or target-profile result

## Review basis

The review compared the active English freeze against current contracts, code,
tests, `docs/current-status.md`, the subordinate code-architecture specification,
and the historical Paper-1 reasoning workspace. It used separate research-
protocol, experiment-design, and code-architecture passes. The English freeze
remains authoritative; this report records why v1.5 changed and which execution
debts remain.

No external novelty search was run in this revision. Novelty and closest-work
claims therefore remain `needs_external_verification`; v1.5 makes no “first”
claim.

## v1.5 decisions

1. RQ1/RQ2 are the primary M0-M5 empirical line. RQ0 remains a mandatory,
   disjoint bounded conformance audit. RQ4 is secondary OpenXC7 physical-depth
   characterization.
2. Target-profile adaptation is a conditional extension selected by
   `tpa_extension_status`; omission cannot block the core campaign or paper.
3. G3 receives a separate positive, artifact-derived, non-official acceptance
   authority. Existing development outcomes retain `g3_accepted=false` and are
   not promoted.
4. Confirmatory execution uses first-class semantic-instance/seed paired blocks,
   shared initial artifacts, matched hidden commitments, balanced order, and
   actual/standalone/incremental cost views.
5. Hidden execution and hidden semantic status are separate. Semantic failure,
   upstream `not_run`, exhausted infrastructure, and integrity failure are not
   interchangeable.
6. RQ1 gatekeeping runs once on the four-family equal-weight macro estimator.
   RQ2 confirmatory tests are M5-M4 and R_HIS-R_generic with Holm; M5-M1 is
   descriptive.
7. Scientific minimum effects are separated from power design alternatives.
   The excluded pilot estimates nuisance parameters, not treatment-defined
   goalposts.
8. G4b is a verifier-derived, no-side-effect authorization boundary; it neither
   runs nor imports a development outcome.

## Issue ledger

| Issue | v1.4 risk | v1.5 protocol disposition | Execution state |
| --- | --- | --- | --- |
| G3 positive authority | Per-scenario artifacts could only say `g3_accepted=false`; no finite positive reducer | Additive `g3-acceptance-v1`, finite artifact-derived matrix, official flags remain false | Open implementation debt |
| Sample identity | Family/task identity and nominal seed could substitute for independent sample/seed | First-class `semantic_instance_id`, `decoding_seed`, provider seed-control status and `paired_block_id` | Open implementation debt |
| Paired contrasts | Initial project/HIS/hidden seed/cost could differ or be charged by execution order | Frozen shared checkpoints, balanced order, same hidden commitment, three cost views | Open implementation debt |
| Hidden missingness | Exceptions or opaque refs could avoid reducer-visible closure | Two-axis outcome, exactly-once semantic commit, sanitized retry/integrity fields | Open implementation debt |
| RQ1 statistics | “Within each family” implied four gatekeeping sequences | One fixed sequence on the equal-family macro; per-family results descriptive | Resolved in protocol |
| RQ2 statistics | M5-M4 had no confirmatory role; M5-M1 mixed mechanisms | Confirmatory M5-M4 online-repair bundle and paired policy probe; exact estimands/MOIs/selectors | Resolved in protocol; power inputs pending pilot |
| Power design | `delta_min` was also treated as the power alternative | Freeze scientific `delta_c` and separate `Delta*_c > delta_c`; joint simulation uses pilot nuisance estimates | Resolved in protocol; numeric values pending G4a |
| OASA safety gate | Pilot could appear to move thresholds; `not_run` aggregation was ambiguous | Pre-pilot fixed safety thresholds, exact cluster bounds, worst-case `not_run`, seed-level cluster failure | Resolved in protocol; population pending G4a |
| L4 ordering | Runtime ordering could route before hidden/VPP closure | Official L4 only after complete VPP-L3; any eager route is excluded non-crediting diagnostics | Open implementation debt |
| Target-profile scope | Optional adaptation work could block the core paper | Conditional extension with absence semantics and separate artifacts | Resolved in protocol; extension undecided |

## Frozen planning matrix and resource envelope

Core G5 starts from six behavioral categories, four new independent pilot-only
semantic instances per category, three decoding seeds, and M0-M5: 24 clusters,
72 paired blocks, and 432 method episodes. Six balanced execution sequences put
each method in each ordinal position 12 times overall and twice within each
category. The full matrix is attempted; there is no efficacy early stopping,
same-pilot top-up, replacement, or outcome-driven enlargement.

G5 planning ceilings are 720 standalone-attributed initial model-stage calls,
432 unique physical initial requests under checkpoint sharing, 144 M1/M5
repair-or-correction calls, and up to 48 repair-probe calls (`K <= 24`). These
exclude frozen transport retries and evaluator/tool calls.

The current official planning target remains 30 semantic instances per each of
four families until excluded-pilot joint simulation. At that target there are
360 paired blocks and 2,160 method episodes. The standalone-attributed initial
ceiling is 3,600 calls, the shared physical initial ceiling is 2,160, the M1/M5
repair-or-correction ceiling is 720, and the policy probe adds `2K_off`. These
are planning ceilings, not observed consumption or authorization to run.

The separate RQ0 planning population remains 100 independent base clusters with
four counterfactual variants each. Its one-seed intake/replay ceiling is 500
calls; three seeds give 1,500. Zero false proceeds in a 100-cluster non-ready
stratum has a one-sided exact 95% upper bound of about 2.951%, so one false
proceed fails the frozen 3% criterion.

## Remaining hard gates

- Implement and verify positive artifact-derived G3 acceptance without changing
  the fixed semantics of existing development outcomes.
- Make semantic instance, decoding seed, paired block, shared checkpoints, three
  cost views, and two-axis hidden closure real runtime/reducer fields.
- Complete remaining project-repair, hidden, infrastructure, tamper, and
  missingness scenario cells.
- Qualify evaluator-owned independent oracles for `uart_fifo_loopback` and
  `stream_fork_join`; only two of four candidate primary families are currently
  qualified.
- Freeze G4a core benchmark/OASA manifests, scientific MOIs/design alternatives,
  selector rules, and immutable checkpoint.
- Run only the excluded natural G5 pilot, then justify final sample size and
  budget from nuisance parameters.
- Implement the independent G4b verifier and authorization receipt before any
  official side effect.

## Review verdict

The v1.5 research plan is coherent enough to guide the next bounded
implementation milestone: positive non-official G3 acceptance. It is not ready
for an official campaign. No protocol text, test count, fake-provider result, or
development VPP may be treated as empirical support for RQ1/RQ2, and no further
abstract scope expansion should precede G3, core G4a, and the excluded natural
G5 pilot.
