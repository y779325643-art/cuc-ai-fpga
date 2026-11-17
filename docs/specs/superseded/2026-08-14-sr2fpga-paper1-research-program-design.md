# SR2FPGA Paper 1 Research Program Freeze

> **SUPERSEDED — historical baseline.** The current Paper-1 research plan is
> [`paper1-v2.1`](2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md), adopted
> 2026-09-14. This `paper1-v1.8` specification is retained for traceability and
> is no longer the execution reference. Its confirmatory families, gate sequence
> (G0-G9, EA-G3..EA-G4b), and budget formulas are replaced; see section 16 of the
> current plan for the clause-by-clause migration. Version labels inside this
> file, including remaining `v1.7` references, record its own history and are
> deliberately not rewritten.

> [Terminology, 2026-09-08](2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> currently serialized as System-HIS v1.2; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

> Chinese companion: [`2026-08-14-sr2fpga-paper1-research-program-design.zh.md`](2026-08-14-sr2fpga-paper1-research-program-design.zh.md).
> If the two versions disagree, this English specification is authoritative.

## Status and authority

- Status: **unfrozen; open for research-program revision by user request on 2026-09-07**
- Version: `paper1-v1.8`
- Version role: active pre-outcome EA amendment; execution remains unauthorized
- Effective date: 2026-09-07
- Target venue: **ACM Transactions on Reconfigurable Technology and Systems
  (TRETS)**
- Evidence cut-off: local `develop@bd516c110862`, plus the current working-tree
  documentation/evidence review
- Scope: product/problem boundary, requirement disposition and ambiguity audit,
  research questions, method factors, benchmark population, information
  privileges, metrics, experiment gates, claim rules, and paper exit criteria
- Implementation status: protocol design; outcome-producing experiments have not
  yet been run under this freeze

As of 2026-09-07, the user has lifted this document's research-program freeze.
Research questions, method design, scope and analysis plans may now be discussed
and revised through explicit, traceable proposals; v1.7 no longer prohibits such
revision. This status change does not itself change any substantive protocol,
approve a replacement design, or authorize implementation, model runs, G5,
official evaluation, or campaign execution. Existing execution and evaluator
boundaries remain in force. Prior QA and M3/M4 audits describe their original
v1.7 scope; affected conclusions must be re-reviewed after substantive revision.
References below to a frozen or active v1.7 plan describe the retained baseline
and are subject to this status notice.

The retained baseline is a **research-program specification**, not the signed campaign freeze. The
candidate split, planning sample size, method definitions, and gate order below
become executable only after G4a, the excluded G5 pilot, and the final G4b
campaign manifest. No file may describe the candidate split as an empirical
result or an already runnable benchmark.

The v1.2 amendment was accepted before any official model or hidden outcome was
opened. It added a bounded pre-generation ambiguity audit, separated the product
north star from the Paper-1 estimand, and recorded the common-project,
information-privilege, budget, evaluator, and then-proposed training-pool
obligations. It did not report a new implementation result.

The v1.3 amendment changes the publication objective to TRETS and removes all
model training from Paper-1. RQ3 and M6U/M6F/M6T/M6TR are withdrawn from the
Paper-1 estimand, method ladder, gate sequence, required artifacts, and claim
space. Existing training code and contracts remain repository infrastructure;
they are not deleted, promoted, executed, or presented as Paper-1 work. This
amendment was accepted before any official model or hidden outcome was opened.

The v1.4 amendment adds bounded target-profile adaptation to RQ4. It requires
predeclared pairs that hold the semantic obligation fixed while changing a
named FPGA target profile, and it freezes functional invariants, required and
allowed project changes, L3/L4 endpoints, denominators, and cost accounting
before official outcomes. It does not add model training or authorize general
cross-device, cross-tool, cross-vendor, bitstream, or board-portability claims.
This amendment was accepted before G4b and before any official model, hidden, or
profile-adaptation outcome was opened.

The v1.5 amendment narrows the minimum Paper-1 submission path to the RQ1/RQ2
M0-M5 experiment, with RQ0 retained as a disjoint safety/conformance audit and
representative OpenXC7 L4 retained as bounded descriptive depth evidence. It
turns target-profile adaptation into an optional, separately frozen extension;
omitting that extension cannot block the minimum G4b or Paper-1 exit. It also
defines artifact-derived positive G3 acceptance, first-class paired-block and
seed identities, shared-artifact/cost accounting, sanitized hidden-evaluator
missingness, and unambiguous macro-level confirmatory tests. This amendment
changes no present implementation or empirical result and authorizes no model,
official hidden, or physical campaign.

The v1.6 amendment separates repeated-measure identity, provider decoding-seed
provenance, and local execution-order randomization. G4b must select exactly one
`decoding_control_mode`: documented provider seed control, or a stochastic
blocked design that estimates expected method effects under a frozen provider
configuration without claiming shared realized randomness or bitwise replay.
This change follows a development-only capability diagnostic in which repeated
DeepSeek outputs matched but deterministic seed support remained undocumented;
the observation is not an empirical method result. G3 continues to require an
artifact-derived capability classifier and strict guard, but it need not wait
for a real external provider to qualify. This amendment was accepted before
G4b and before any official model or hidden outcome was opened.

The v1.7 amendment changes the RQ1 confirmatory hierarchy before any G5 natural-
model or official outcome was opened. It replaces the RQ1 fixed sequence with a
two-hypothesis primary Holm family comprising M4−M3 and M4−M0. M3−M2 remains
mandatory but becomes a prespecified secondary estimation contrast. M4−M3 is
interpreted as the joint deterministic-materialization/edit-surface increment,
not a skeleton-text-only effect. This amendment changes no population, method,
endpoint, information privilege, budget, RQ2 family, RQ0 audit, RQ4 analysis, or
data-collection obligation; every signed eligible M0-M5 condition is still
executed and reported.

The v1.8 amendment authorizes a contract-preserving evolutionary architecture
search as RQ5. It retains the M0--M5 ladder, all no-training rules, the
public/hidden evaluator separation, and one-shot terminal evaluation. RQ5 uses
its own `E0` equal-budget random-search and `E1` EA conditions rather than
reviving the withdrawn M6 training line. It requires a separately versioned
Design Point (DP) genotype under a Design-Space Contract (DSC), deterministic
decoding to Project Contract, real public
tool fitness, append-only search lineage, and a predeclared terminal selector.
RL, learned QoR prediction, and general GA/RL search remain outside Paper-1.
This amendment is a research design only: it authorizes no implementation,
pilot, model run, hidden outcome, or official campaign before EA-G3, EA-G4a,
EA-G5, and EA-G4b close.

This document supersedes the earlier Paper-1 reframe, official-evaluation, and
mandatory constrained-decoding proposals. Those superseded documents are
preserved in Git history rather than retained as parallel working-tree
authorities.

It does not supersede machine contracts, runtime behavior, tests, evidence
ledgers, or stable artifacts. When sources disagree, use this order:

1. versioned contracts registered by `contracts/manifest.json`, current code,
   and reproducible tests;
2. artifact-backed evidence in the task ledger and committed reports;
3. `docs/current-status.md` and current project READMEs;
4. this research/experiment specification; and
5. superseded material available through Git history as non-authoritative
   context.

The rationale and claim ledger supporting this freeze are in
[`docs/research-program/paper1-v1/`](../research-program/paper1-v1/README.md).

## 1. Decision summary

Paper 1 will study **contract-grounded FPGA project generation, verifier
separation, and reproducible project-level evaluation**. It will not claim
novelty from repository-level agents, automatic
tool use, iterative RTL repair, executable acceptance gates, or trajectory
recording alone. HORIZON and adjacent systems make those capabilities strong
baselines.

The product north star is broader than the paper's causal estimand: given a
possibly incomplete, ambiguous, or unsupported requirement, the system should
either produce a coherent project with independently established evidence or
stop honestly with `needs_clarification`, `capability_gap`, or `not_run`. Paper 1
does not claim to solve that unrestricted product problem. It evaluates a
bounded requirement-intake audit separately from project generation, while the
official VPP population contains only evaluator-adjudicated, G4b-frozen,
scoreable requirements.

The paper's project-level evaluated object is a complete multi-file RTL project
through the declared L3 flow, not a generally deployable bitstream or board
system. The central empirical question is:

> Under matched model, public requirement facts, feedback privileges, and total
> compute/tool budgets, does contract-grounded deterministic materialization
> improve hidden project-level correctness over free generation from the same
> Project Contract, does the complete untrained Project Contract pipeline outperform Direct,
> does contract-aware public repair survive an evaluator-owned one-shot hidden
> check under a reconciled correctness-cost budget, and does contract-preserving
> evolutionary architecture search outperform equal-budget random search without
> receiving hidden-evaluator feedback?

The minimum paper therefore requires:

1. a shared, versioned requirement-intake boundary plus a disjoint ambiguity
   audit that measures silent proceed, false blocking, provenance, and
   clarification behavior without granting project-pass credit;
2. a method-neutral common FPP delivery contract and a closed, separately applicable
   Project Contract treatment;
3. a frozen family-held-out benchmark with evaluator-owned hidden final
   evaluation;
4. matched direct, untyped-structured, PC, skeleton, and repair conditions;
5. convergence and total-cost accounting for every M0-M5 episode, including
   failures, `not_run`, infrastructure outcomes, and repair attempts, not only
   final pass rate; and
6. representative OpenXC7 L4 confirmation, explicitly separated from general
   L4, Vivado, bitstream, board, and portability claims.
7. a separately gated RQ5 contract-preserving architecture-search comparison
   between equal-budget random search and EA, with public fitness only and
   one-shot hidden final validation.

A predeclared paired target-profile adaptation study may be added as an optional
extension only through the separate freeze obligations in Sections 7.2, 7.5,
9, and 10. It is not part of the minimum confirmatory family and cannot delay
the core M0-M5 experiment.

Model training or fine-tuning, Tier-B constrained decoding, QoR prediction,
broad Vivado closure, `.bit` generation, L5, and RL architecture search are
outside Paper-1. The v1.8 `E1` EA condition is the sole authorized evolutionary
search scope; it may not delay or substitute for the M0--M5 held-out evaluation.

## 2. Why the research line changed

HORIZON demonstrates that a fixed general-purpose agent can evolve hardware
repositories against executable evaluators and drive selected suites to
best-so-far convergence. Its project pack is a control plane, git history is a
replayable state/trace substrate, and its most informative results include the
cost and long tail of convergence. It does not train a policy and does not
report physical QoR/PPA results. It also warns that repair-visible evaluator
feedback can produce over-solving.

SR2FPGA's defensible difference is therefore a combination that must be tested,
not asserted:

- Project Contract as a typed requirement-to-project semantic contract rather than an
  episode control plane;
- explicit separation between repair-visible diagnostics and hidden final
  semantic oracles;
- versioned project episodes and trajectories that make attempts, repair, cost,
  provenance, and missingness auditable; and
- evidence depth from project consistency through synthesis and a representative
  physical subset.

Paper-1 contains no learned treatment. The retained M0-M5 questions are executed
and reported according to the signed protocol even when an earlier contrast is
negative. Negative representation or repair results change the supported claim,
not the denominator, method set, or evidence record.

## 3. Frozen implementation snapshot

Implementation status in this section is the 2026-08-24 snapshot retained with
the freeze; it is not the mutable current-state authority. Later implementation
progress, including development/excluded evaluator-authority migration, is
tracked in `docs/current-status.md` and the subordinate code-architecture spec.
This historical snapshot does not change the frozen estimands, method
definitions, or gate order.

The v1.5 amendment does not refresh this snapshot. Only the positive registered
G3 gate artifact defined in Section 10 can close G3; test counts, prose, or
development conformance outcomes alone cannot.

### 3.1 Implemented capability

- `agent/` supports deterministic and model-backed multi-file generation,
  two-stage `REQ2HIS -> HIS2PROJECT`, H0-H3 result recording, L0-L4 tool
  orchestration, repair hooks, independent oracles, mutation qualification, and
  trajectory/training-view export.
- A shared, provenance-bearing Requirement Envelope and requirement boundary
  now run before every implemented generation method. Non-ready requests stop
  before model-client construction or candidate generation, and Direct methods
  record H0-H3 as `not_applicable` rather than failing for a missing Project Contract.
- Registered requirement-audit case/event/replay/outcome/witness contracts and
  a development Phase A/B runner now exist, including exactly-one replay and a
  cluster-aware reducer. The signed fixture population, frozen interval and
  official audit campaign do not.
- `training/` supports dataset conversion, dry-run validation, manual LoRA/SFT,
  adapter merge, and serving without importing Agent. Its model commands are
  infrastructure, not a formal G4b-gated M6 entry.
- Versioned Project Contract, project/terminal/evaluation, OASA, trajectory,
  candidate training-release, training-view, task-catalog, dataset, and evidence
  files exist. Registration does not authenticate a release or create an
  official evaluator producer.

### 3.2 Verified evidence

- The task ledger covers 71 target families; 31 are implemented and have L3-or-
  higher evidence.
- The 14 catalog-designated Paper-1 core families are implemented, reach L3,
  and are mutation-qualified on deterministic/reference paths.
- Twenty-one families are mutation-qualified and nine have independent Python
  reference evidence.
- Two families, FIR filter and matrix-vector MAC, have curated OpenXC7
  post-route L4 passes.
- Phase C records 9/9 L3, 9/9 independent Python oracle passes, and 45/45
  scoreable mutations killed.
- Phase D is a valid negative pilot: 24/24 live episodes completed, with 12
  generation failures, 12 H2 failures, 0/24 L0-L3 passes, zero repair attempts,
  and no live L4 result.

### 3.3 Research targets, not present results

- signed evaluator-owned requirement-intake fixtures, frozen statistical
  thresholds, and official ambiguity-audit campaign artifacts;
- a Runner-authoritative, end-to-end M0-M5 episode path that consumes the
  method-neutral project contract, immutable terminal seal, and separate public/
  hidden evaluators;
- held-out-family representation or repair-effectiveness gains;
- Tier-B logit-masked constrained decoding;
- calibrated QoR prediction;
- general OpenXC7 L4, any Vivado pass, `.bit` evidence, or L5; and
- application-realistic RL, image, radar, SoC, or host-integrated acceleration.

### 3.4 Blocking inconsistencies in the 2026-08-24 snapshot

The following P0 obligations must close before an outcome-producing official
campaign. Current mutable facts remain in `docs/current-status.md`. G1 and G2
are locally closed on the 2026-08-24 working tree; neither implementation gate
is a model outcome.

- Development OASA has a sealed loader, witness, one-answer replay and reducer,
  but no signed fixture population, frozen interval/threshold or official audit
  execution exists.
- Provider-neutral M0-M5 core adapters now include M2 Structured-Direct and M3
  PC-Free, but the legacy Runner is not their end-to-end campaign authority and
  cannot yet reconcile one frozen pack through public evaluation, terminal
  selection, reseal and official hidden dispatch.
- A separate development hidden boundary consumes a sealed terminal candidate
  once and returns an opaque reference, but it does not mint an official outcome
  or replace the adaptive candidate-TB/oracle path used by the legacy Runner.
- Logical model calls are counted, but provider tokens, transport/parser retries,
  tool/wall/EDA budgets and canonical runtime trajectory reconstruction are not
  closed as one matched episode-level budget.
- Historical trajectories can lack explicit call/patch/rerun evidence; G4b
  still needs a versioned migration or exclusion decision for those records.
- Only two of the four candidate primary held-out families (`matched_filter` and
  `sobel_threshold`) currently have qualified independent-oracle evidence.
- Candidate training eligibility, v2 views, matched pools, and unpromoted
  release tooling exist as non-Paper-1 repository infrastructure. Their
  incompleteness is not a Paper-1 gate, and no Paper-1 run may invoke them.

## 4. Research questions and falsification rules

### RQ0 — Separate bounded requirement-boundary conformance audit

On a sealed case set disjoint from the VPP benchmark and all training views, can
the shared pre-generation requirement boundary distinguish `ready`,
`needs_clarification`, and `capability_gap`; preserve user facts, platform
defaults, system assumptions, and unresolved facts as different provenance
classes; and prevent every non-ready case from crossing the project-generation
boundary?

The audit is evaluator-side and stops before M0-M5 project generation. Its gold
disposition, material-interpretation witnesses, critical-fact IDs, allowed-
default IDs, clarification answer objects, and capability rationale are private.
The system under audit sees only the raw requirement, declared public platform
context/defaults, and the frozen public capability-profile identifier. A
correct disposition is not a project, L-stage, VPP, repair, or training success.

RQ0 is mandatory but statistically and operationally disjoint from the primary
RQ1/RQ2 method estimand. Its outcomes cannot remove, replace, reroute, or
reweight a VPP instance and cannot change a method, prompt, Family Recipe,
budget, information privilege, or terminal-selection rule.

RQ0 is unsupported if the critical false-proceed rate exceeds the G4b threshold,
if an undeclared semantic assumption is represented as a user fact or permitted
default, if an unknown request is coerced to a nearest family, if required
clarification facts are not surfaced, or if a non-ready audit case produces a
project-generation call or candidate write. A positive result supports only
bounded requirement-boundary behavior on the named audit set; it does not prove
arbitrary open-world requirement understanding or project correctness.

### RQ1 — End-to-end contract value

Does the generated Project Contract pipeline improve method-neutral verified project
success beyond direct generation under the same external requirement facts and
total budget? Within the Project Contract path, what increment is attributable to the
joint deterministic-materialization/edit-surface intervention, and what
secondary evidence is associated with the representation bundle?

Comparisons and interpretation:

- M3 versus M2 estimates the **two-stage representation bundle**. It changes the
  plan schema, prompt, checker, and representation length, so it must not be
  described as a pure causal estimate of “typing alone.” Both branches must match
  planner/generator call count, global budget, and effective input facts.
- M4 versus M3 reuses the exact same frozen generated-PC artifact for each
  semantic-instance/replicate block. It jointly changes deterministic project
  materialization and the associated editable-surface policy; without an
  additional orthogonal control it is not a pure skeleton-text, editable-byte,
  or lowerer-rule effect.
- M4 versus M0 is an end-to-end system comparison and does not isolate a single
  mechanism.

RQ1 is unsupported as a complete claim unless both primary contrasts pass their
predeclared rules. A single passing primary contrast supports only its named
local claim. RQ1 is also unsupported if apparent gains merely move failures from
H/L0 into hidden L2 or disappear after effective information and total cost are
reconciled.

RQ1 is a two-hypothesis primary confirmatory family. M4−M3 and M4−M0 use Holm
control in Section 7.5; M3−M2 is a mandatory prespecified secondary estimation
contrast and cannot unlock, rescue, or replace either primary claim.

### RQ2 — Verifier separation and repair

Starting from frozen matched initial states, does bounded public repair improve
terminal `VPP-L3@A`, what total cost does it consume, and does the improvement
survive one-shot hidden evaluation rather than merely optimizing a public
evaluator?

- M5 versus M1 is an **end-to-end system comparison**, not an isolated repair-
  policy effect: their initial generators, artifacts, diagnostics, and edit
  surfaces differ.
- M5 versus M4 measures the incremental success and cost of public-feedback
  repair inside the PC pipeline and is the primary confirmatory online-repair
  bundle contrast.
- The repair-mechanism probe starts from the same frozen failing M4 project and
  pairs a generic repair policy with a PC-aware repair policy. The initial
  state, model, public tool output, edit surface, and global budget are identical;
  only the declared PC-aware diagnostic fields differ.
- Report `P(hidden failure | public acceptance)` for each repair condition. Do
  not subtract rates with different hidden-evaluation eligibility.

The paired R_HIS−R_generic probe is the second confirmatory RQ2 contrast. M1−M0
is a secondary generic-repair diagnostic, and M5−M1 is a mandatory descriptive
end-to-end correctness-cost comparison.

RQ2 is unsupported if no real failure→diagnosis→patch→rerun transition occurs,
if public gains vanish under the one-shot hidden evaluation, or if trusted
artifacts are modified.

### RQ3 — Withdrawn from Paper-1

The former tool-verified training-view question is withdrawn by the v1.3 TRETS
amendment. Paper-1 does not fine-tune a model, create a training treatment,
select a checkpoint, or report learned improvement. Existing M6 and training-
view contracts remain non-Paper-1 repository infrastructure and receive no
Paper-1 method, result, or reproducibility credit.

### RQ4 — Secondary bounded physical-depth characterization

Across the original fixed denominator, how many candidates reach the
predeclared representative OpenXC7 L4 subset, and among L3 survivors what
additional attrition, timing, or resource behavior appears?

RQ4 is secondary and descriptive in the minimum paper. It supports only the
declared tool/device/family subset. Conditional L4 survivor analysis cannot
replace unconditional VPP-L4, and neither result implies bitstream, board,
Vivado, cross-device, or cross-vendor portability.

Total episode cost, including failures and unavailable axes, is a cross-cutting
RQ1/RQ2 outcome rather than a physical-depth estimand owned by RQ4.

**Optional target-profile adaptation extension.** If capacity remains after the
core G4b package is ready, a separately predeclared paired subset may hold the
semantic obligation and hidden functional oracle fixed while changing a named
public FPGA target profile. Every pair then requires a stable
`profile_pair_id`, baseline and variant `target_profile_id`, declared invariants,
required/allowed/forbidden changes, profile-specific L3/L4 endpoints, and an
evaluator-owned compliance oracle. This extension is descriptive unless its own
pre-outcome freeze defines a powered contrast and multiplicity rule. Its absence
does not block the minimum Paper-1 campaign or submission.

### RQ5 — Contract-preserving evolutionary architecture search

Given the same frozen requirement facts, target profile, generated Project Contract
seed, public evaluator, and real-tool budget, does `E1` contract-preserving
evolutionary architecture search improve the predeclared terminal bounded
physical-feasibility endpoint over `E0` equal-budget random architecture search,
while the selected candidate retains one-shot hidden functional conformance?

`E0` and `E1` are separate RQ5 conditions, not changes to the M0--M5 ladder and
not a revival of the withdrawn M6 training conditions. Both consume the same
Design-Space Contract grammar, deterministic decoder, mutation domain, candidate and
tool budget, public fitness, terminal selector, and evaluator commitment. Their
only factor is adaptive EA selection in `E1` versus non-adaptive uniform sampling
in `E0`. `B_EA`, the once-decoded seed, is a descriptive reference only.

Population selection may use only public contract checks and actual public tool
outputs. Hidden cases, identifiers, scores, logs, and outcomes cannot influence
mutation, parent selection, generation count, fitness, terminal replacement, or
any later search decision. The hidden evaluator executes exactly once on the
sealed terminal candidate per condition. A Design Point is a separately
versioned compact genotype governed by the Design-Space Contract and decoded to a
Project Contract. The PC remains serialized as System-HIS v1.2; it is not an EA genotype.

RQ5 has one primary `E1−E0` hypothesis. Before G5, EA-G4a freezes its endpoint,
minimum effect, cluster estimator, interval/test implementation, candidate/tool
budget, public fitness, terminal selector, missingness rule, decoder and grammar
hashes, and evaluator commitment. Public-fitness trajectories, diversity,
invalid-decode rate, cost, resource/timing vectors, public-to-hidden divergence,
and `B_EA` are descriptive diagnostics. RQ5 cannot claim general PPA improvement,
hidden correctness, or portability beyond its signed endpoint and final hidden
outcome.

RQ5 adds EA-G3 development conformance, EA-G4a protocol freeze, EA-G5 excluded
pilot, and EA-G4b authorization before EA-G7 official execution. It does not
authorize implementation or execution at this amendment stage.

## 5. Method and baseline ladder

### 5.1 Reference conditions

- **B_ref — deterministic reference:** trusted project and oracle sanity. It
  proves the benchmark is executable, not that a model solves it.
- **B_template — deterministic skeleton/behavior reference:** engineering and
  QoR anchor. It receives no learned-model credit.
- **Frontier ceiling:** a large closed model under declared direct/repair
  conditions. It is reported separately and never used to estimate fine-tuning
  gain.

### 5.2 Matched model conditions

M0-M5 use the same small/open base model version, tokenizer, quantization,
context limit, decoding family, and episode population. The current code does
not yet implement this complete ladder; G3 is a hard runtime gate.

- **M0 Direct:** the requirement plus the common public project/interface
  contract goes directly to one full-project generator. It produces no
  Project Contract, receives no public evaluator feedback before scoring, and is not
  required to pass H-stages.
- **M1 Direct-Repair:** M0 plus public-evaluator diagnosis/repair under the
  global repair budget. It is a **HORIZON-motivated Direct-Repair control**. It
  may be called HORIZON-like only after G3 implements a project pack, immutable
  evaluator-owned acceptance channel, accepted-checkpoint history, persistent
  session/state policy, and auditable repository trace; it is never called an
  exact HORIZON reproduction without the released original protocol.
- **M2 Structured-Direct:** model stage 1 emits an untyped structured plan from
  the same requirement facts; model stage 2 freely emits the full project. The
  plan has no Project Contract types, cross-field checker, or deterministic skeleton.
- **M3 PC-Free:** model stage 1 emits Project Contract; model stage 2 freely emits the
  full project through a true no-skeleton generator. For the materialization
  comparison, M3 and M4 consume the same frozen generated-PC artifact.
- **M4 PC-Skeleton:** trusted code lowers that generated Project Contract to the
  contract skeleton and the model fills only declared behavior regions. It has
  no outer EDA repair; any planner/parser/schema retry is an explicit budgeted
  model call, not hidden inside “first attempt.”
- **M5 PC-Online:** M4 plus public-evaluator diagnosis and outer repair under
  exactly the M1 global repair/tool budget.
- **R_generic / R_HIS repair probe:** two repair policies applied to the same
  frozen failing M4 project for the mechanism analysis in RQ2. These are paired
  diagnostic conditions, not additional headline generators.

The official unit of matched execution is a versioned **replicate block** keyed
by `(semantic_instance_id, replicate_id)` and a stable `paired_block_id`. Within a
block, M0 and M1 consume the same immutable initial Direct project; M3 and M4
consume the same immutable generated-PC artifact; and M4 and M5 consume the
same immutable initial skeleton-derived project. The complete M0-M5 block uses
one public fact projection, model/inference configuration, tool and evaluator
commitments, hidden-case seed, and global budget policy. The repair-policy probe
uses a separate `repair_probe_block_id` and the exact same failing M4 checkpoint
for both policies. `replicate_id` identifies the planned repeated measurement;
it is not derived from a provider-returned value and does not imply that methods
share the same realized decoding randomness. A comparison is unpaired and non-
confirmatory if any required shared identity or content hash differs.

G4b freezes exactly one decoding-control mode:

- `documented_seed_control`: every replicate maps to a frozen requested seed,
  and a hash-bound, independently reviewed provider capability profile proves
  the requested mechanism is eligible for replay within its documented
  boundary. This does not by itself establish common random numbers across
  different method prompts or token trajectories; that stronger claim requires
  a separately documented cross-request coupling mechanism.
- `stochastic_blocked`: replicate IDs, provider/model/gateway/inference
  configuration, request count, and balanced execution schedule are frozen;
  requested seeds are retained only as request provenance when accepted by the
  provider. Method effects are interpreted over the frozen stochastic decoding
  distribution. No same-randomness, seed-effect, deterministic-replay, or
  bitwise-reproducibility claim is allowed.

Method order is randomized and balanced across replicate blocks using a local
`execution_schedule_seed` that is independent of any provider decoding seed.
Artifact reuse is
an experimental control, not free method cost: the ledger records each shared
event once as block-level actual campaign consumption, attributes the full cost
of every required shared prerequisite to each method's standalone end-to-end
cost, and reports incremental contrast cost after the shared checkpoint. No
shared call may be charged only to whichever method happens to execute first.
G4b freezes these three cost views and the exact reducer before outcomes.

| Inferential role | Frozen comparisons |
| --- | --- |
| RQ1 primary Holm family | M4−M3; M4−M0 |
| RQ2 confirmatory Holm family | M5−M4; R_HIS−R_generic |
| Mandatory secondary/descriptive | M3−M2; M1−M0; M5−M1; per-family effects; stage transitions; correctness-cost frontiers |
| Reference only | B_ref; B_template; frontier ceiling |

M6U, M6F, M6T, M6TR, and `M6F[E_traj]` are not Paper-1 method conditions under
v1.3. Their retained code and contracts are outside this protocol.

**A_req — requirement-boundary audit** is not M7 and is not a project-generation
treatment. It executes the frozen shared intake boundary once per sealed audit
case and is intercepted before any M0-M5 model stage, candidate workspace write,
repair, or project evaluator. It receives no VPP or project-method credit.

The common public project contract is method-neutral. It requires the complete
RTL source set, top/interface declaration, manifest, applicable constraints,
build/tool metadata, and trusted-edit boundary needed by L0-L3. Project Contract,
H0-H3 records, generated requirement traces, candidate testbenches, and predicted
QoR are condition-applicable or advisory artifacts; they may not be universal
admission requirements for M0/M1/M2 or hidden scoring authorities.

Before method assignment, every official VPP instance is independently
adjudicated `ready` and converted into one frozen public requirement-fact
projection. M0-M5 receive content-equivalent fact IDs, values, and provenance;
method-specific serialization may differ, but no method receives extra external
requirement facts. The official VPP run validates and reuses this frozen ready
projection rather than adaptively asking a user or changing the requirement.
The automated intake component itself is evaluated only in A_req.

External skills, retrieval, or persistent memory are separate binary factors.
They are not part of the minimum ladder and must not be silently enabled for
only one condition.

### 5.3 What the model may and may not see

Every run is created from a versioned **episode pack** with a model-visible
public projection and an evaluator-only private projection. It contains:

```text
episode_id
paired_block_id and repair_probe_block_id when applicable
analysis_population: official_vpp | ambiguity_audit
requirement_id, requirement_revision_id, semantic_instance_id,
paraphrase_group_id, and requirement text
requirement-envelope version/hash and public fact IDs, values, and provenance
platform-default profile ID/hash and backend-capability profile ID/hash
family_id, topology_id, generalization_class, and semantic parameters
platform_profile_id
method_condition and model provenance
public artifact contract
allowed edit surface
repair-visible evaluator policy
private hidden evaluator identifier/hash and hidden-case seed
terminal-candidate selection and infrastructure-retry policy
model-call/token/retry/repair/tool/wall/EDA budgets
replicate ID, decoding-control mode, requested decoding seed, provider
seed-control status/fingerprint, execution-schedule seed, and balanced method
execution order
prompt hash and effective-information hash
contract/catalog/tool versions and hashes
base_requirement_cluster_id and ambiguity_case_id when applicable
private gold disposition commitment, critical-fact IDs, allowed-default IDs,
clarification-answer commitment, and capability rationale for A_req only
```

Every episode-pack field has an explicit visibility class. `family_id`, topology
and generalization labels, private disposition commitments, expected
clarification content, recipe decisions, and hidden evaluator identifiers are
evaluator-only unless a different privilege is explicitly frozen. Listing a
field in the pack never makes it model-visible. A family identifier appearing
verbatim in user-provided requirement text remains a user fact; evaluator-added
family metadata does not.

The candidate workspace must not expose:

- `agent/src/` deterministic generators or task templates;
- trusted testbenches, independent reference models, mutation sources, hidden
  vectors/properties, or scoring scripts;
- held-out reference projects, Project Contract answers, trajectories, datasets, or
  retained non-Paper training exports; or
- API keys, private endpoints, vendor artifacts, and unrelated repository state.

All methods are scored by evaluator-owned harnesses. A candidate-generated
testbench is an untrusted artifact and can never be the hidden authority. Public
smoke checks and their declared diagnostics may be repair-visible; hidden
deterministic, randomized-fixed-seed, and stress cases are private.

For each `(semantic_instance_id, replicate_id, method_condition)` the public
stopping rule selects exactly one terminal candidate. At `@1`, every declared
model stage is called once and internal retries are disabled; all calls/tokens
remain visible in cost accounting. At `@A`, freeze the earliest candidate that
meets public acceptance, otherwise the last complete candidate at budget
exhaustion. If no complete project is emitted, the outcome is a design failure.

After the terminal candidate is immutable, the hidden evaluator executes once.
Paired methods receive the same frozen hidden-case seed. A hidden result may not
trigger repair, candidate replacement, prompt/tool/budget change, or a second
evaluation. A predeclared infrastructure retry replays only the same immutable
candidate. No hidden path, case ID, hash, stdout/stderr, status, score, or summary
may enter a model/repair message; a spy test must prove this boundary.

Hidden closure has two orthogonal machine fields:

```text
hidden_execution_status = completed | not_run | infrastructure_error | integrity_error
hidden_semantic_status = pass | fail | null
```

`completed` requires exactly one committed `pass` or `fail`; a semantic failure
is a design outcome with `VPP-L3=0` and can never trigger repair, replacement, or
rescoring. `not_run(reason)` means an upstream condition such as no immutable
terminal made hidden scoring inapplicable; the upstream design outcome, not the
word `not_run`, determines VPP. A pre-commit infrastructure error may retry only
the same terminal hash under the frozen policy; exhausted retries are
unscorable, not model failures. An integrity error invokes the frozen campaign
abort/invalidation rule. Once a semantic result is committed, every retry is
forbidden.

A canonical/oracle Project Contract may be used only in an explicitly labeled ceiling
or content-equivalent representation diagnostic, never in the headline end-to-
end comparison. M2/M3 effective-information audits must list every visible fact;
matching token totals alone does not prove information equivalence.

Family Recipe is a versioned generation-information privilege, not a substitute
for missing requirement facts. Selection occurs only after the shared boundary
has returned `ready`. The full decision and policy hashes remain evaluator-only.
No primary held-out headline condition receives family-specific recipe content;
any catalog-assisted analysis must be predeclared as a separate, secondary,
content-equivalent information treatment available to every compared method.
Recipe text, route decisions, or family aliases may not resolve an A_req gold
ambiguity or enter its private labels.

`semantic_instance_id`, `replicate_id`, and `paired_block_id` are first-class
planned-sample and runtime fields; `family_id` may never substitute for an
instance or replicate ID. `requested_decoding_seed` is a separate provenance
field and may never be silently hard-coded or used as the replicate identity.
The provider adapter records the requested seed, any provider-reported system
fingerprint, and whether deterministic seed control is supported. In
`documented_seed_control` mode, a provider without a reproducible, frozen,
independently reviewed decoding mechanism is ineligible at G4b. In
`stochastic_blocked` mode, unavailable or undocumented seed control is retained
as such and does not block eligibility by itself, but it forbids deterministic
or common-randomness claims and cannot be converted to a nominal capability.

An ambiguity-audit case exposes no gold status, omitted fact, accepted answer,
private capability rationale, or reference artifact. A dedicated visibility spy
test covers those fields independently of the hidden-project-evaluator spy test.

### 5.4 Global budget and retry accounting

The campaign freezes separate ceilings for model calls, input/output/cached
tokens, planner/parser/schema retries, outer repair attempts, public tool calls,
wall time, and EDA time. Every retry is a first-class attempt event and consumes
the relevant global budget. Provider transport retries are infrastructure events
and never silently increase a method's model budget.

`@1` means one call per declared pipeline stage, not “outer attempt zero.”
Comparisons report both the common total budget and stage allocation. Method
execution order is randomized and balanced within replicate blocks by the
frozen local `execution_schedule_seed`, while model gateway, cache policy,
code, and tool versions remain frozen. This schedule seed never enters a model
request and is never reused as `requested_decoding_seed`.

A_req has a separate preflight call/token/wall-time budget and never consumes an
M0-M5 project-generation budget. The cost of constructing the frozen official
ready projection is reported as common benchmark overhead, not charged
differently across methods. Every M0-M5 condition reports online inference,
episode, repair, public-tool, hidden-evaluator, and EDA cost under the frozen
accounting rule.

For planning, every repair-capable condition has one frozen total model-side
repair/correction-call ceiling. An M5 Project Contract correction and an M5 outer
project repair are separately labeled stages but consume that shared ceiling;
they are not two independent free calls. Provider transport retries remain
outside this ceiling only when they satisfy the frozen infrastructure-retry
rule and reproduce the same request without exposing new information.

## 6. Benchmark population and split freeze

### 6.1 Task authority

The denominator is the 14-family `recommended_sets.paper1_core` list in the
canonical contracts catalog. Catalog intent is joined with the evidence ledger;
only families that pass the benchmark-readiness gates enter a run.

The following is the **candidate G4a split**, not an executed or final frozen
split. It becomes final only at G4b, after a machine-readable split manifest
exists and every primary held-out family has qualified evaluator-owned hidden
oracle evidence. G4a must freeze objective exclusion criteria and an ordered
reserve list. Replacement is allowed only before G4b and before any outcome from
an official requirement is visible.

**Development families (9):**

- `sync_fifo`
- `single_dual_port_ram`
- `valid_ready_stream_accumulator`
- `mac_array`
- `matrix_vector_mac`
- `fir_filter`
- `peak_detector`
- `pattern_matcher`
- `p_stream_trigger_filter`

**Primary family-held-out test families (4):**

- `uart_fifo_loopback` — protocol composition
- `stream_fork_join` — stream/control composition
- `matched_filter` — numeric signal processing
- `sobel_threshold` — image pipeline

**Flagship parameter/topology-held-out family (1):**

- `qtable_update_core`; it is reported separately because the catalog does not
  currently permit an S4 family-held-out claim for this family.

The planning target is 30 independent **semantic instances** per held-out family.
G4b freezes the final sample size using no official outcomes: an excluded pilot
supplies paired-discordance, cluster-dependence, attrition, and runtime ranges for
a predeclared power/precision simulation at the minimum effect of interest. If
the planning target survives that analysis, the benchmark contains 120 semantic-
instance clusters. Three replicate blocks are repeated measurements within each
cluster, not 360 independent samples.

Paraphrases, width variants that preserve the same behavior, and repeated hidden
random seeds share one `semantic_instance_id` or `paraphrase_group_id` and never
inflate `n`. Pilot requirements and any prompt used for debugging are excluded
from the official test. With only four deliberately selected held-out families,
inference is conditional on these four named families; a population-level “new
FPGA families” claim requires more held-out families before G4b.

### 6.2 Split and leakage rules

- The test-family IDs, aliases, requirements, canonical HIs, reference projects,
  trajectories, and memory/skill entries are excluded from model-visible
  development context.
- Development and model/configuration selection use requirement-held-out slices
  inside development families only. Official test outcomes remain sealed until
  the model, stopping rule, and analysis code are frozen.
- Exact duplicate hashes and normalized RTL/AST or requirement near-duplicates
  are removed across folds. The similarity method and threshold are fixed in the
  split manifest before G4b.
- Module-level hashes, component-graph overlap, interface signatures, and
  semantic-mechanism clusters are audited across folds. The manifest labels each
  test instance as seen-primitives/unseen-composition, unseen-family/seen-
  mechanism, or unseen-mechanism; these labels bound the generalization claim.
- All source episodes preserve `family_id`, topology/alias, requirement hash,
  `semantic_instance_id`, `paraphrase_group_id`, model/provider provenance, and
  source release.
- T5-T12 are historical topology IDs, not difficulty tiers. Official metadata
  keeps `topology_id`, `family_id`, `difficulty_tier`, and `sample_id` separate.
- Once G4b is signed, no family, semantic instance, or method may be removed or
  replaced after any official model or hidden outcome is observed.

### 6.3 Oracle-readiness gate

Every held-out family requires:

- an evaluator-owned black-box behavioral oracle independent of candidate files;
- hidden/random/stress cases not visible during repair;
- mutation qualification against declared defect classes;
- immutable edit-surface enforcement; and
- a benchmark-readiness artifact with hashes and tool versions.

At this evidence cut-off only `matched_filter` and `sobel_threshold` satisfy the
qualified-independent-oracle evidence requirement among the four candidate
primary held-out families. `uart_fifo_loopback` and `stream_fork_join` must close
this gap before G4b. An embedded or candidate-visible testbench alone is
insufficient for final hidden credit, regardless of a catalog `ready` label.

### 6.4 Disjoint requirement-ambiguity audit population

The ambiguity audit is disjoint from the 14-family VPP join, the four primary
held-out families, the flagship population, all development or retained
non-Paper training views, and
the excluded G5 generation pilot. Its independent unit is
`base_requirement_cluster_id`; variants, paraphrases, answer branches, intake
replicates, and any requested decoding seeds are repeated observations and never
inflate `n`.

The candidate planning target is 100 independently authored base clusters. Each
cluster contains four sealed, counterfactually related public variants:

1. a fully specified `ready` control;
2. a `ready` control with only an evaluator-approved public default omitted;
3. one critical omission or contradiction requiring `needs_clarification`; and
4. one coherent, explicit requirement that the frozen backend profile classifies
   as `capability_gap`.

The perturbation strata cover at least width/depth/storage; clock/reset/CDC;
protocol/handshake/backpressure; simultaneous-event priority and error behavior;
numeric representation; and latency/throughput/acceptance obligations. Unknown
family wording with complete, supported semantics must appear as a `ready`
counterexample to family-lookup coercion. Naturally authored cases are primary;
mechanical deletion and fault injection are auxiliary conformance suites.

For each private case, two hardware-competent annotators independently freeze a
fact graph, materially distinct interpretation witnesses, expected disposition
and reason codes, critical-fact IDs, permitted-default IDs, capability IDs and
profile hash, acceptable clarification fact IDs, and a one-turn answer object.
A third adjudicator resolves disagreement before any audited output is opened.
`needs_clarification` requires at least two materially different interpretations
or an explicit contradiction that changes observable behavior, interface,
constraint, or support status. `capability_gap` requires a coherent resolved
requirement and an exact unsupported capability under the named profile. If one
reasonable interpretation is supported and another is not, the gold status is
`needs_clarification`, not a guessed gap.

The audit has two fixed phases. Phase A produces structured disposition, reason,
critical-fact, capability, default, and assumption IDs and then stops. Phase B
replays one prewritten answer object only for eligible clarification cases and
expects the precommitted `ready` or `capability_gap` result. There is no adaptive
human answer, requirement rewriting, second clarification round, project
generation, repair, or hidden project oracle. `not_run` is reserved for
evaluator/runner infrastructure and is never a semantic gold label or a system-
selected refusal.

Final audit cases, labels, witnesses, answer objects, aliases, and perturbation
templates are excluded from any future training, prompt debugging, Family Recipes,
retrieval, skills, memory, and official VPP inputs. Pilot audit cases never enter
the final audit. Audit outcomes may not remove, replace, or filter an official
VPP instance after G4b.

## 7. Outcome definitions

### 7.1 Headline metric

**Verified Project Pass through L3 (`VPP-L3`)** is the method-neutral binary
project outcome. A candidate receives pass credit only when:

1. it conforms to the common public project/interface manifest and immutable
   edit surface;
2. L0 project consistency passes under a method-neutral project contract;
3. L1 lint and public L2 simulation pass;
4. the one-shot evaluator-owned hidden semantic oracle passes;
5. L3 synthesis completes under the frozen, accurately named Yosys flow; and
6. no trusted-artifact, edit-surface, provenance, or budget violation occurred.

Here “complete project” means the frozen multi-file RTL/build package required
by this L0-L3 contract. It does not imply routed hardware, bitstream generation,
board execution, or satisfaction of an unstated platform constraint. Those
claims require the separately named L4/L5 evidence.

H0/H1/H2/H3 are mechanism outcomes only for methods that emit Project Contract. They
are `not_applicable`, not failures, for M0/M1/M2 and are never a condition-
specific advantage inside the cross-method VPP definition. A PC-stage design
failure that prevents a project from being emitted still makes that method's
VPP outcome zero through the ordinary generation path.

Record explicit machine fields for public L2, hidden L2, evaluator identity,
edit/provenance violations, infrastructure status, and `vpp_l3`. Never infer
VPP-L3 from the legacy `pass_level=L3` label. Report `VPP-L3@1` under the one-
call-per-stage rule and `VPP-L3@A` under the public-repair budget. REQ2FILE rows
never receive project-level credit.

### 7.2 Required secondary metrics

- condition-applicable H0/H1/H2/H3 and common L0/L1/public-L2/hidden-L2/L3
  outcomes separately;
- first failure stage and stage-transition matrix;
- public acceptance and `P(hidden failure | public acceptance)`;
- actual repair attempts, successful repairs, diagnosis and patch presence, and
  oracle-edit violations;
- total/input/output/cached tokens where available, model calls, tool calls,
  attempts, wall-clock time, and EDA runtime for **every** official episode,
  including failed episodes;
- resource-to-first-success capped at the frozen budget, with unsuccessful
  episodes explicitly right-censored and never dropped from cost reporting;
- infrastructure failure, design failure, timeout, and `not_run` as separate
  outcomes; and
- per-family results plus an equal-family macro average.

The observed hidden-failure-after-public-acceptance diagnostic is

```text
HFPA_observed =
  N(public_accept and hidden_execution_status=completed and
    hidden_semantic_status=fail)
  / N(public_accept and hidden_execution_status=completed)
```

It is always accompanied by
`hidden_completion_rate_given_public_accept`, the hidden infrastructure-
unscorable count, and best/worst-case bounds. Rates with different hidden
eligibility or completion denominators are not directly subtracted.

For L4 report both unconditional `VPP-L4` on the original fixed denominator and
`P(L4 pass | VPP-L3 pass)` as survivor attrition. Development,
held-out, and flagship families remain separate. No unregistered PPA
significance test is permitted.

If the optional target-profile extension is activated, report baseline and
variant outcomes separately and the binary **Target-Profile Adaptation Pass
through L4 (`TPA-L4`)**. A pair receives `TPA-L4=1` only if both members preserve
the same declared functional invariants, satisfy their profile-specific project
and constraint contracts, realize every required change without a forbidden
change, and pass their required L3 and OpenXC7 L4 endpoints. Correctness
scorability is independent of cost-axis completeness: a missing token, wall, or
EDA-cost field affects cost/missingness analyses but cannot by itself force a
functionally scoreable `TPA-L4` pair to `not_run`. Report the full pair
denominator, variant failure stage, compliance violations, timing/resource
deltas, paired cost availability, and unavailable reasons. A baseline-only or
survivor-only analysis cannot receive adaptation credit.

Mutation score qualifies an oracle; it is not a model-performance metric.
Generic L3 cell statistics are not called FPGA LUT QoR. Measured QoR is accepted
only from a successful named stage and tool flow.

### 7.3 Ambiguity-audit-only outcomes

For A_req define `proceed=1` if the final intake decision authorizes project
generation, or if any project planner, REQ2HIS, project generator, repair model,
candidate-workspace write, or project-evaluator call occurs, on a gold non-ready
case. The evaluator intercepts an unsafe authorization before executing the
downstream call, but it still counts as false proceed. Any escaped downstream
event is additionally a generation-boundary violation. Generating first and
later emitting `needs_clarification` therefore fails both rules.

Required ambiguity-audit metrics are:

- the complete `ready` / `needs_clarification` / `capability_gap` confusion
  matrix, with `not_run` infrastructure shown separately;
- `FP_amb = P(proceed | gold needs_clarification)`;
- `FP_gap = P(proceed | gold capability_gap)`;
- the primary safety summary `max(FP_amb, FP_gap)` and a generation-boundary
  violation count;
- false blocking on both gold-ready variants;
- precision/recall over critical clarification fact IDs, capability IDs,
  permitted-default IDs, and explicit assumption IDs;
- repeated-known-fact question rate and unknown-family coercion count;
- one-replay closure to the precommitted `ready` or `capability_gap` status; and
- intake calls, tokens, wall time, and infrastructure status.

The candidate planning acceptance target is zero observed false proceed in each
100-case non-ready stratum, with each one-sided 95% upper confidence bound no
greater than 3%; no generation-boundary violation; no undeclared semantic
assumption; 100% critical-fact recall; at least 95% one-replay closure; and no
more than 5% false blocking on each ready stratum. G4b freezes the final sample
size and resource budget using only the excluded pilot, but the 3% false-
proceed, 5% false-block, 95% replay, and 100% critical-fact criteria and the
exact interval rule are scientific acceptance thresholds frozen before G5; the
pilot cannot relax them. Passing supports a bounded conformance statement on
the named set, never a zero-risk or project-correctness claim.

With 100 independently authored clusters and four variants per cluster, the
candidate audit contains 400 cases and 100 observations in each non-ready
stratum. Zero false proceeds gives a one-sided exact 95% upper bound of about
2.95%, so the planning target is deliberately close to the 3% threshold and one
error would fail it. Use one-sided exact Clopper-Pearson bounds on independent
base-cluster outcomes. Requiring both `FP_amb` and `FP_gap` bounds to pass is an
intersection-union safety rule. A non-ready `not_run` counts unsafe in the
primary worst-case gate, while a ready `not_run` counts as false block. If
decoding is stochastic, any unsafe seed fails the cluster. G4b must therefore
freeze the final cluster count from excluded-pilot missingness/runtime without
treating 100 as guaranteed adequate or changing the threshold.

For `N_A` audit clusters and `S_A` intake seeds, Phase A consumes
`4*N_A*S_A` intake calls and the one-answer replay consumes at most
`N_A*S_A`, for a ceiling of `5*N_A*S_A` (500 calls at `N_A=100, S_A=1`; 1,500
at `S_A=3`).

### 7.4 Failure, missingness, and retry rules

- Model generation/parse failure, candidate-invalid output, budget exhaustion,
  and a candidate/tool timeout caused within the frozen resource limit are design
  outcomes: `VPP-L3=0` and they remain in the full denominator. Downstream hidden
  stages may be `not_run`; that label is not itself reclassified as a failure.
- A provider transport outage or evaluator/runner/tool infrastructure failure
  after a candidate is immutable uses the fixed retry count and replays only that
  candidate.
- If fixed retries still cannot score the candidate, neither side of a pair may
  be silently deleted. Mark the semantic-instance/replicate block unscorable,
  report it, and provide complete-pair plus all-unscorable-as-failure sensitivity
  analyses and worst/best bounds.
- Only an outage shared by all paired methods may defer the block. No requirement
  may be replaced after any hidden outcome is seen.
- G4b freezes an unresolved-infrastructure rate and between-method imbalance
  threshold. Crossing it invalidates the campaign and triggers a documented
  rerun; it never licenses a post-hoc exclusion.

Every episode's hidden slot must close to one evaluator-owned sanitized outcome
artifact using the two-axis status above. The artifact records the failed stage,
frozen reason class, retry eligibility/exhaustion, sanitized exception class,
and semantic-commit count where applicable; raw paths, cases, outputs, or
detailed status remain private. Swallowing an exception, returning only an
opaque reference with no reducer-visible closure, omitting an expected outcome,
or committing twice is an integrity failure rather than candidate success or
design failure.

For A_req, a gold non-ready case is intercepted after disposition scoring even
when the system predicts `ready`; record false proceed without executing
generation. If any downstream event escapes that interceptor, also record a
generation-boundary violation. Audit infrastructure failure is
`not_run`, remains in the audit denominator and missingness table, and cannot be
recoded as a correct disposition. Crossing the frozen audit-infrastructure
threshold invalidates that audit run rather than licensing replacement cases.

### 7.5 Statistical contract

The independent benchmark unit is `semantic_instance_id`. Paraphrases, hidden
case seeds, and planned `replicate_id` values are repeated measurements. For a
paired comparison X−Y, compute the binary difference within each replicate
block, average replicate differences within semantic instance, then average
instances within family. The headline estimate is the equal-weight mean of the
four named family means. Under `stochastic_blocked`, this is a randomized-block
estimate over the frozen provider/configuration distribution; it does not claim
that X and Y consumed the same realized random stream.

Intervals use a nested stratified bootstrap that resamples semantic instances
within each family while retaining all method pairs, paraphrases, hidden cases,
and replicates for the selected block. The interval is conditional on the
four frozen families and fixed M0-M5 protocol; it is not an interval over all
FPGA task families.

Confirmatory hypotheses are directional and use one-sided familywise alpha
0.05. RQ1 and RQ2 are separate Holm families; alpha is not recycled between
them, so their separate control does not imply a paper-wide familywise error
rate of 0.05. Every table also reports two-sided 95% confidence intervals and
effects in both directions. A positive claim requires Holm rejection of the
predeclared threshold null, the lower endpoint of the two-sided 95% interval to
exceed the named minimum effect, and all named integrity, missingness, and
budget gates to pass. Multiplicity controls inference, not data collection:
every signed eligible M0-M5 condition is executed and reported.

For RQ1, let `Y1_ifqm` be terminal `VPP-L3@1` for family `f`, semantic instance
`i`, planned replicate `q`, and method `m`. For each primary contrast
`c in {43, 40}`, compute `D_ifc = mean_q(Y1_ifq,a_c - Y1_ifq,b_c)`, then
`Delta_fc = mean_i(D_ifc)` and `Delta_c = (1/4) sum_f Delta_fc`, where
`(a_43,b_43)=(M4,M3)` and `(a_40,b_40)=(M4,M0)`. The directional nulls are
`H0_43: Delta_43 <= delta_min_materialization` and
`H0_40: Delta_40 <= delta_min_system`. The two cluster-respecting one-sided
p-values form the RQ1 Holm family at familywise alpha 0.05. Report raw and Holm-
adjusted p-values; if ordered values are `p_(1) <= p_(2)`, reject the first only
when `p_(1) <= 0.025`, and then reject the second only when `p_(2) <= 0.05`.

M4−M3 estimates the deterministic-materialization/edit-surface bundle. M4−M0
estimates untrained end-to-end system value and does not isolate a component.
For `c in {43,40}`, set `delta_43=delta_min_materialization` and
`delta_40=delta_min_system`. Let `S_c=1` if and only if Holm rejects `H0_c` and
the lower endpoint of the two-sided 95% confidence interval for `Delta_c`
strictly exceeds `delta_c`. Let `G_RQ1=1` if and only if all named integrity,
leakage, information, budget, hidden-completion, and infrastructure-missingness
gates applicable to RQ1 pass, and define `C_c=1` if and only if `S_c=1` and
`G_RQ1=1`. Each `C_c=1` may activate only its corresponding local claim; the
complete RQ1 claim requires `C_43=C_40=1`.

M3−M2 is a mandatory prespecified secondary representation-bundle estimand.
Report its equal-family macro and per-family estimates with two-sided 95%
intervals, but no confirmatory p-value by default; it cannot rescue a failed
primary comparison and cannot be interpreted as a typing-alone effect.

The confirmatory threshold tests use the complete `semantic_instance_id` as the
resampling unit, retain every planned replicate and method outcome together, and
keep family membership and equal-family weights fixed. G4a freezes the
studentized statistic, boundary-null centering, within-family cluster-resampling
rule, interval form, number of resamples, analysis seed, tie/extreme-case rules,
and code hash; G4b signs that implementation unchanged. A finite-sample exact
cluster-swap test may be named only if an independent review establishes whole-
cluster label exchangeability. It tests its declared sharp null and cannot
replace the nonzero minimum-effect threshold test. Replicate-level, requested-
seed-level, paraphrase-level, or hidden-case-level independent sign flips are
forbidden.

Per-family effects and leave-one-family-out analyses are mandatory descriptive
diagnostics; they do not open, close, or rescue a macro claim. Before G5, G4a
freezes `{delta_min_materialization, delta_min_system}`, the corresponding
scientific rationales, and an optional secondary interpretation threshold for
M3−M2. A merely positive point estimate is insufficient. Any later family-level
or confirmatory secondary claim requires a new pre-outcome hierarchical
multiplicity and power contract.

For every signed semantic instance `i` in family `f` and replicate `q`, let
`YA_ifqm` be terminal `VPP-L3@A` for method `m`. Define
`D_if,54 = mean_q(YA_ifq,M5 - YA_ifq,M4)`, `Delta_f,54 = mean_i(D_if,54)`, and
`Delta_54 = (1/4) sum_f Delta_f,54`. This intention-to-treat estimand includes
every signed cluster whether or not M5 invokes repair. Because M5 may spend its
single repair/correction allowance on either Project Contract correction or outer
project repair, M5−M4 estimates an online-repair **bundle**, not either stage in
isolation.

For the repair-policy probe, a frozen selector chooses at most one eligible
failing M4 checkpoint per semantic instance before either repair branch or any
hidden outcome is opened. Eligibility requires an immutable candidate, named
public failure stage, valid repair-visible diagnosis, budget remaining, and no
infrastructure, integrity, or trusted-edit violation. The selector freezes
family/failure-stage strata, tie-break seed, per-family cap `k_f`, and minimum
analysable count `k_min,f`; it selects all eligible clusters up to the cap, never
tops up after outcomes, and never replaces a selected checkpoint. Let `Z_ifr`
be terminal hidden VPP after policy `r` in `{R_HIS, R_generic}`; no-patch,
failed-patch, and budget-exhausted branches remain zero in the selected
denominator. `Delta_R` is the equal-family macro mean of paired
`Z_HIS-Z_generic` differences. If any `k_min,f` is unmet, the probe is
non-rejecting and descriptive rather than silently dropped.

The RQ2 nulls are `H0_54: Delta_54 <= delta_min_54` and
`H0_R: Delta_R <= delta_min_repair_policy`. Their cluster-respecting one-sided
p-values form a two-comparison Holm family at familywise alpha 0.05; report
two-sided 95% intervals and every per-family estimate. M5−M1 is a mandatory
descriptive end-to-end system comparison and correctness-cost frontier, not a
member of that mechanism family. Per-family stage transitions,
catalog-assisted Recipe analyses, and physical results remain secondary.

The minimum RQ4 analyses are descriptive. If the optional adaptation extension
is activated, its unit is `profile_pair_id`, not an individual profile member,
L3 survivor, decoding seed, or routed candidate. Report per-method `TPA-L4`
proportions and 95% intervals by resampling complete profile pairs within the
predeclared family/profile strata while retaining both members and all repeated
seeds. A confirmatory adaptation contrast requires its own pre-outcome freeze,
minimum effect, sample-size justification, and multiplicity rule; no
post-outcome promotion is allowed.

RQ0 is a separate safety/conformance audit and does not enter the VPP
multiplicity families. Its resampling unit is `base_requirement_cluster_id`; all
four variants, paraphrases, answer branches, and intake seeds remain together.
Report raw stratum counts, one-sided interval bounds for `FP_amb` and `FP_gap`,
and cluster-resampled 95% intervals for secondary audit metrics. If intake uses
stochastic decoding, any seed that proceeds on a non-ready case makes that base
cluster fail the primary safety metric; seed averages are diagnostic only.

The M5 versus M1 end-to-end comparison is reported as a correctness–cost
frontier. An efficiency claim additionally requires the frozen correctness non-
inferiority margin and primary cost axis to pass before cost superiority is
examined. Total episode cost includes failures; time to success is capped at the
budget, with the unsuccessful count shown.

For every confirmatory contrast `c`, `delta_c` is the smallest effect that can
support its scientific claim; it is not the effect assumed for power. Before
G5, G4a separately freezes a design alternative `Delta*_c > delta_c` and target
power `1-beta`. The excluded pilot may estimate paired discordance, cluster-
level replicate dependence, repair eligibility, attrition, and runtime, but may not
set `delta_c` or `Delta*_c` from an observed treatment effect. With equal `n`
per family and pilot cluster variance `sigma^2_fc` for replicate-averaged paired
difference `D_ifc`, the planning approximation is
`SE(Delta_c) ~= sqrt(sum_f sigma^2_fc / (16n))` and
`n_c >= (z_.975 + z_(1-beta))^2 sum_f sigma^2_fc /
[16(Delta*_c-delta_c)^2]`. G4b chooses final `n` through a predeclared joint
simulation of the RQ1 and RQ2 Holm families, including the shared-M4 covariance,
the complete Holm-plus-confidence-bound decision rule, attrition, missingness,
repair eligibility, and the selected decoding-control mode within the frozen
gate-valid envelope. Claim-invalidating gate failures are not assigned a
speculative occurrence probability or counted as ordinary negative outcomes in
statistical power. RQ1 planning is conditional on `G_RQ1=1`; a realized
`G_RQ1=0` invalidates RQ1 claim activation. If the complete RQ1 claim remains
planned, its target is joint statistical power
`P(S_43=1 and S_40=1 | G_RQ1=1) >= 0.80`; report both conditional marginal
powers as well. Each retained RQ2 confirmatory contrast also requires at least
0.80 Holm-adjusted marginal power under its frozen design alternative and
applicable gate-valid envelope. If the resource ceiling cannot meet a target, G4b
must downgrade the affected claim before official execution rather than inherit
the v1.6 planning conclusion. Power “at delta” is invalid because it leaves no
separation from the claim threshold, and observed power is not reported.

No official outcome informs sample-size calculation. Failure to exclude an
effect larger than the named minimum is reported as imprecision, not “no
effect.” No early stopping, official-set expansion, or method/family replacement
is allowed after G4b.

## 8. Episode data and artifact contract

Paper-1 records M0-M5 generation, evaluation, repair, cost, provenance, and
missingness as immutable episode evidence. It does not build or release a model-
training corpus and does not invoke any training or merge command.

All natural failures remain in their frozen denominator. Synthetic injectors
and mutations are auxiliary controls/oracle qualification and carry explicit
origin labels; they are never silently mixed into natural failure prevalence or
headline repair effectiveness. A repair transition requires an executed
diagnosis, non-empty valid patch/delta, actual rerun, and reconciled before/after
outcome. A bucket name or H-stage failure alone is not a repair transition.

Every runtime episode artifact must validate against its registered contract,
bind the frozen requirement/method/model/tool/budget identities, preserve
included, excluded, `not_run`, and infrastructure reasons, and keep candidate,
public-evaluator, and hidden-evaluator material in their declared visibility
domains. Raw hidden cases, paths, outputs, status, and score never enter
candidate workspaces or repair-visible records.

The episode evidence binds hidden execution and semantic statuses separately,
the exactly-once semantic-commit event, same-terminal infrastructure-retry
lineage, any integrity violation, and all source references used by the G3 or
campaign reducer. A sanitized downstream outcome never exposes the underlying
hidden case or raw evaluator output.

At G3 and again at G4a, the implementation and protocol baselines are captured
as immutable, checksummed local checkpoint manifests. A Git commit is one valid
carrier but is not required by this document; the essential property is that
all files, contracts, tests, evaluator commitments, and analysis code named by
the checkpoint can be reconstructed without mutating controlled evidence.

Existing training-view, eligibility, pool, and candidate-release contracts are
retained for repository compatibility and possible future work. They are not
required Paper-1 artifacts, do not authorize a dataset release, and receive no
Paper-1 claim credit.

## 9. Physical confirmation and optional target-profile adaptation

Official OpenXC7 L4 dispatch occurs only after the same terminal candidate has
passed the complete `VPP-L3` path, including one-shot hidden L2; it is not the
headline denominator. Any eager pre-hidden route is isolated as excluded
development diagnostics and cannot influence terminal selection, repair,
hidden eligibility, VPP, official cost, or Paper-1 physical results. The
predeclared representative families are:

- `fir_filter`
- `matrix_vector_mac`
- `single_dual_port_ram`
- `stream_fork_join`
- `sobel_threshold`
- `qtable_update_core` (separate flagship topology/parameter holdout)

This set spans numeric, memory, stream/control, image, and the catalog-designated
flagship shell. If `qtable_update_core` cannot enter the physical protocol, G2/G4b
must resolve the catalog flagship designation before outcomes; it may not be
silently omitted. For each
eligible candidate, record routing status, timing/Fmax, declared resource fields,
tool versions, constraints, and failure classification.

If the optional target-profile extension is activated, its own pre-outcome
manifest nominates pairs from these representative families. Each pair holds
`semantic_instance_id`, functional obligations, and hidden-oracle semantics
fixed while changing one predeclared profile axis or one explicitly defined
compound profile. Candidate axes include device/part, clock target,
resource-mapping policy, interface policy, and build constraints. The evaluator
validates profile compliance and functional preservation independently of
model-produced files. Profile changes may not expose private family labels,
hidden cases, or evaluator internals. Absence of this optional manifest does not
block the core G4b or G8 physical-depth stage.

Vivado on the same frozen RTL is an optional commercial reference and is not a
TRETS submission gate. Without it, report only OpenXC7 post-route evidence.
`.bit` generation and L5 board execution require separate protocols and may not
be inferred from FASM or routed reports.

## 10. Ordered work packages and gates

No model pilot may skip G1-G4a. No official run may skip the post-pilot signed
G4b freeze. Paper-1 authorizes no training run.

### G0 — Documentation and authority freeze

- This spec is linked from `AGENTS.md`, `docs/README.md`,
`docs/current-status.md`, and `docs/specs/README.md`.
- Superseded Paper-1 proposals are absent from the working tree and remain
  recoverable through Git history.
- Acceptance: clean-link audit and no competing file labeled current Paper-1
  authority.

<a id="g1--system-his-contract-closure"></a>
### G1 — Project Contract closure

**Current gate status (2026-08-18): locally closed for this checkout.** The
registered conformance matrix includes Schema, H0-H2, reset, lowerer,
compatibility aliases, legacy quarantine, and all deterministic writers. A
real Direct project reaches common L0 with H0-H3 `not_applicable`, and the full
  lightweight regression is green. This does not authorize a model
pilot, official hidden evaluation, or any Paper-1 result claim. G2 was locally
closed on 2026-08-24; G3-G4b remain open.

- Select and implement one JSON-Schema/H0 authority relationship.
- Make canonical positive fixtures and official examples pass schema, H0, H1,
  and H2, or relabel non-lowerable examples explicitly.
- Add negative fixtures for every frozen rule; unify reset; define and test the
  compatibility/quarantine envelope.
- Separate the method-neutral common FPP delivery contract from optional Project Contract,
  H-stage, candidate-testbench, and predicted-QoR artifacts. Direct and untyped
  controls must reach common L0 without Project Contract and record H0-H3 as
  `not_applicable`.
- Acceptance: schema/checker/fixture/lowerer conformance matrix is green, a real
  Direct→common-L0 regression proves no H-stage dependency, and the full
  regression passes.

### G2 — Catalog, evidence, and stage semantics

**Current gate status (2026-08-24): locally closed for this working tree.** The
canonical catalog/ledger now resolve the named alias, stage-semantics and L4
provenance defects below. This is an implementation/evidence-integrity gate, not
a model result or signed campaign artifact.

- Fix `clock_divider`; unify T7; create alias/sample-level T10/T11 evidence.
- Keep `contracts/task-catalog/` as the sole catalog location; do not retain a
  catalog copy under `docs/`.
- Align the L3 name/definition with the actual runtime or change the runtime with
  tests; repair ledger dates, source references, and L4 provenance.
- Acceptance: semantic contract tests fail on the former defects and the human
  status view regenerates from the ledger.

### G3 — Measurement and episode-pack closure

- Register and runtime-validate versioned benchmark-split, episode-pack, method-
  condition, model/gateway provenance, attempt-event/trajectory, campaign-freeze,
  paired-outcome, and cost-summary contracts.
- Register and runtime-validate requirement-envelope, requirement-disposition,
  ambiguity-case, clarification-replay, and ambiguity-outcome contracts.
- Implement first-class M0-M5 adapters; keep `source` separate from
  `method_condition`; add external requirement/semantic-parameter loaders, M2's
  untyped-plan path, and M3's true no-skeleton generator.
- Replace invisible internal retries with explicit globally budgeted events.
- Persist the shared requirement intake for every success and stop outcome;
  record all fact/provenance/default/assumption IDs, route/profile hashes, and
  pre/post clarification lineage rather than only the first three questions.
- Add stop-before-generation interception, no-nearest-family tests, and a
  visibility spy test proving no private ambiguity label/answer reaches model,
  Recipe, PC, project, repair, or any retained non-Paper training context.
- Split the public evaluator from an evaluator-owned hidden harness. Hidden runs
  once on the terminal immutable candidate, candidate testbenches are never
  trusted, and spy tests prove no hidden datum reaches repair.
- Count repair only after an actual diagnosis/patch/rerun transition; gate QoR by
  successful stages; preserve explicit episode inclusion/exclusion reasons.
- Record pre/post state hashes, artifact deltas, visibility class, calls, tokens,
  cached tokens, duration, acceptance, failure origin, and all cost axes; promote
  freeze/state/audit bundles outside `tmp/`.
- Add a registered, additive `g3-acceptance-v1` authority. Its positive verdict
  is rebuilt only from write-once artifact/event references, registered contract
  versions, checksummed test/evidence manifests, and a finite required-scenario
  matrix; caller-declared scenario names, success booleans, or narrative status
  cannot grant acceptance. Older development outcome contracts keep their
  fixed non-official semantics and cannot be rewritten into this authority.
- Any development/excluded VPP projection is a non-official conformance
  diagnostic only. It cannot by itself grant `g3-acceptance-v1`, official
  pass-credit authority, an official VPP outcome, or G4b authorization, and it
  cannot be promoted into any of those authorities.
- The required G3 matrix covers: one gold-ready M0-M5 replicate block; explicit
  `semantic_instance_id`/`replicate_id`/`paired_block_id`, requested-seed
  provenance, and independently seeded balanced order; M0/M1 shared initial
  project; M3/M4 shared PC; M4/M5 shared initial project; real public failure→
  diagnosis→patch→rerun transitions for M1 and M5; M5 H0-H3 correction paths;
  public and hidden pass/fail; sanitized provider/public/hidden/L3
  infrastructure `not_run`; raw-to-summary reconciliation for all three cost
  views; and fail-closed tamper, lineage, ordering, budget, trusted-edit, and
  visibility cases. Each scenario closes to a registered outcome even when no
  candidate exists.
- G3 additionally requires a reducer-derived provider-capability classifier,
  positive deterministic/fake fixtures, real or synthetic negative fixtures,
  and a strict pre-dispatch guard. Counts, match flags, classification,
  limitations, profile identity, and eligibility must be recomputed from frozen
  protocol, documentation-review, and per-call observation artifacts rather
  than trusted from submitted summary booleans. A real external provider need
  not be eligible for G3 because G3 proves excluded implementation conformance;
  G4b owns the real-provider mode decision.
- G3 acceptance requires every matrix cell to be artifact-derived and green,
  plus ready/default/clarification/gap audit fixtures that reconcile to a
  confusion matrix with no project-generation event on non-ready cases and no
  private/hidden leakage. The acceptance artifact explicitly sets
  `official_outcome=false`, `official_authority=false`,
  `pass_credit_authority=false`, and `g4b_authorized=false`. G3 therefore proves
  excluded development conformance only. G4a prepares the candidate benchmark
  and evaluator/oracle commitments; G5 is an excluded natural-model feasibility
  pilot; G4b signs and independently authorizes the no-outcome campaign; G6
  materializes it without official outcomes; and G7 executes the official M0-M5
  held-out L0-L3 experiment. None of these later-gate deliverables is a G3
  acceptance prerequisite.

G3 may use deterministic or fake model clients with real parsers, registered
contracts, evaluator/tool adapters, and reducers. It establishes implementation
conformance only. G5 is the first natural-model feasibility run eligible to
inform paired discordance, attrition, runtime, or sample-size assumptions.

### G4a — Candidate benchmark and analysis protocol

- Create the candidate 14-family join, semantic-instance requirements, split,
  ordered reserve list, objective exclusions, generalization labels, episode
  packs, evaluator commitments, analysis code, and planning sample-size model.
- If the optional target-profile extension is activated, create its candidate
  pairs with stable pair/member IDs, declared functional invariants,
  required/allowed/forbidden changes, profile-compliance commitments, L3/L4
  endpoints, objective exclusions, and planning pair count. This item is not a
  core G4a acceptance dependency.
- Create a disjoint candidate ambiguity-audit manifest with base clusters,
  paired variant/perturbation strata, independently adjudicated private gold
  commitments, critical facts, allowed defaults, answer objects, capability
  profile hashes, objective exclusions, and an ordered reserve list.
- Before any G5 outcome, freeze the RQ1/RQ2 contrast-specific minimum effects,
  design alternatives strictly above those thresholds, target power of at least
  0.80, RQ1/RQ2 Holm implementations, the RQ1 gate-conditional full-claim
  joint-power rule,
  threshold-test and interval implementations, repair-probe
  eligibility/selector/caps/minima, and the RQ0 scientific acceptance
  thresholds/interval implementation. G5 may estimate nuisance parameters and
  resource needs, not move these scientific goalposts.
- Freeze the common official ready fact projection and the Family Recipe
  information policy. Primary held-out headline methods receive no family-
  specific Recipe body.
- Seal official requirement/oracle contents before the pilot; only hashes and
  readiness state are visible to implementation work.
- Acceptance: reference conditions dry-run on every candidate family and a
  checksummed candidate manifest that contains no model outcome.

### G5 — Excluded paired feasibility pilot

- The starting planning proposal is six core behavioral categories, four new
  independent non-official semantic instances per category, M0-M5, and three
  replicates: 24 semantic instances, 72 replicate blocks, and 432 method-
  outcome episodes. This is an excluded planning floor, not an authorized run or
  final sample size; G4a may revise it before any pilot outcome is opened.
- Use a six-sequence balanced Williams/Latin order: across 72 blocks each method
  occupies each ordinal position 12 times, and within each category's 12 blocks
  each position twice. Shared prerequisites are materialized in a block-
  preparation phase before randomized method-specific execution. Attempt the
  complete fixed matrix with no efficacy early stop, outcome-driven enlargement,
  sample replacement, or same-pilot top-up.
- Exercise M0-M5 with the same replicate-block identities and shared checkpoints
  intended for the official protocol, including at least one real diagnosis→
  patch→rerun transition in M1 and in M5 and complete provenance, missingness,
  and three-view cost accounting.
- If the optional profile extension is active, exercise at least one pilot-only
  pair for every candidate change axis. Those pairs never enter an official
  extension population and are not part of the core pilot scale criterion.
- Before the pilot, freeze the repair-probe eligibility/selector and set
  `k_c <= 4` per behavioral category, so `K <= 24`. One one-call
  R_generic branch and one one-call R_HIS branch add exactly `2K` probe branches
  and at most `2K <= 48` model calls, plus their public reruns and one-shot hidden
  evaluations. No outcome-driven top-up is allowed.
- The core G5 planning ceilings are 720 standalone-attributed initial calls,
  432 unique physical initial provider requests under the three sharing rules,
  144 M1/M5 repair-or-correction calls, and at most 48 repair-probe calls,
  excluding frozen transport retries and public/hidden/tool invocations.
- Scale only if the reference paths are 100% executable, every model episode
  produces an auditable outcome bundle even when it ends in `GEN_FAIL`, and at
  least one model treatment reaches L0 so downstream measurement is informative,
  and both M1 and M5 contain a genuine diagnosis→patch→rerun transition.
- Those two transitions establish mechanism feasibility only; confirmatory RQ2
  readiness also requires the frozen probe minimum-count rule and the Holm-
  adjusted marginal-power rule for each retained RQ2 contrast.
- Model-quality failures remain results; infrastructure/contract failures reopen
  the relevant gate. Pilot requirements never enter the official test.
- Stop immediately and reopen the relevant gate for hidden/private leakage,
  trusted-edit, duplicate hidden commit, artifact/lineage/budget failure, or an
  unresolved infrastructure failure after frozen retries. These integrity stops
  do not remove already attempted model-quality outcomes from the ledger.
- Use pilot-only paired discordance, cluster dependence, attrition, hidden/public
  divergence, and runtime to size and budget the final protocol. Any adapter,
  prompt, evaluator-visibility, budget, or schema change invalidates G4a and
  requires a versioned candidate-protocol revision.
- On separate pilot-only ambiguity clusters, exercise every disposition,
  permitted-default, contradiction, capability-gap, and clarification-replay
  path. Any post-pilot change to the fact taxonomy, default/capability profile,
  Recipe ordering, metric, visibility, question policy, or replay semantics
  invalidates the corresponding G4a audit protocol.

If any scale criterion fails, do not enlarge the pilot, add prompt privilege, or
open an official campaign to manufacture downstream events. Either version G4a
and repeat a new excluded pilot, or pursue the benchmark/evaluation or bounded
negative-result track. Pilot model-quality failures remain evidence about
feasibility; integrity/infrastructure failures remain gate failures.

### G4b — Final signed campaign freeze

- Freeze the final split/sample size, semantic clusters, three replicate IDs,
  `decoding_control_mode`, requested-seed provenance, independent
  `execution_schedule_seed`, method order, prompts, effective-information
  hashes, base model and inference
  configuration, global budgets, tools,
  evaluator hashes/case seeds, candidate selection, infrastructure retry/abort
  thresholds, the unchanged pre-pilot RQ1/RQ2 minimum-effect vectors and design
  alternatives, correctness non-inferiority margin, primary cost axis, fully
  specified estimators/tests, and multiplicity rules.
- Freeze the final ambiguity-audit clusters and perturbation balance, private
  commitments, default/capability profiles, A_req budget, infrastructure rule,
  `FP_amb`/`FP_gap` interval implementation, unchanged false-block/replay
  thresholds, and leakage checks. Sign that audit outcomes cannot alter the VPP population or
  any method, prompt, Recipe, budget, or candidate-selection rule.
- Freeze the RQ1 primary Holm family (`M4-M3`, `M4-M0`), the mandatory secondary
  M3-M2 analysis, the separate RQ2 Holm family (`M5-M4`,
  `R_HIS-R_generic`), repair-transition definition, correctness non-inferiority
  rule, and online model/tool/cost reporting. Each family retains its own alpha;
  no cross-family alpha recycling is permitted.
- Freeze the equal-family macro estimator, threshold-test implementation,
  confidence-interval implementation, Holm reducer, RQ1 gate-conditional
  joint/marginal-power report, descriptive M5-M1 analysis, paired-block
  identities, seed-control
  eligibility, balanced order, shared artifacts, and the three cost views.
- Freeze the final sample size from excluded-pilot simulation; 30 semantic
  instances per family remains a planning target until then. At that target,
  four families × 30 instances × three replicates × six methods yields 360 paired
  blocks and 2,160 method-outcome episodes. More generally, with `n` instances
  per family, `B=4*3*n=12n` blocks and `E=6B=72n` episodes. The standalone
  method-attributed initial-stage ceiling is `10B=120n` calls (3,600 at `n=30`),
  while the three sharing relations give a unique physical initial provider-
  request ceiling of `6B=72n` (2,160). Upstream design stops can reduce actual
  later-stage calls, so these are ceilings, not minimum consumption. The one-
  per-M1/M5 repair/correction ceiling adds at most `2B=24n` calls (720), and the
  repair-policy probe adds `2K_off`. Maximum model-side totals are therefore
  `144n + 2K_off` standalone-attributed and `96n + 2K_off` physical provider
  requests, excluding frozen transport retries and tool calls. The ledger also
  reports public-tool, hidden, EDA, token, and wall-time budgets.
- If the optional target-profile extension is activated, freeze its pair
  population, axes, invariants, change policy, compliance oracles, `TPA-L4`
  estimator, full-pair denominator, L3/L4 policy, cost/missingness accounting,
  sample-size justification, and confirmatory/descriptive status in a separate
  signed extension section. Its absence cannot block core G4b acceptance.
- Freeze `tpa_extension_status=disabled|enabled`. `disabled` requires no pair
  artifact and forbids later adaptation claims; `enabled` activates every
  extension obligation above. The field cannot change after any official side
  effect or outcome.
- Require qualified evaluator-owned independent oracles for all four primary
  held-out families and a passing M0-M5 full-pack dry-run.
- The signed no-outcome manifest binds the v1.7 freeze hash, positive G3
  acceptance reference, G4a core benchmark/OASA manifests, G5 provenance,
  model/prompt/information hashes, `decoding_control_mode`, replicate blocks,
  requested-seed provenance, independent schedule seed/order, budgets/tools,
  public/hidden commitments, missingness/abort policy, analysis code, oracle
  readiness, and `tpa_extension_status`.
- In `documented_seed_control`, the manifest must bind an independently reviewed
  eligible provider-capability profile. In `stochastic_blocked`, it instead
  binds the complete replicate plan, frozen provider/model/gateway/inference
  configuration, balanced schedule, missingness policy, and the prohibition on
  deterministic/common-randomness claims. Any hybrid or unspecified mode is
  invalid.
- Acceptance: an independent verifier derives a registered
  `g4b-authorization-receipt-v1` containing the campaign ID/freeze hash,
  verified prerequisite references, signer policy, extension status,
  `side_effects_before_verification=0`, and `authorized=true`. The author of the
  manifest cannot self-declare this value. Any missing/mismatched/unsigned input
  fails before a run directory, model client, candidate, public evaluator, or
  hidden-evaluator side effect exists. G4b neither executes nor promotes a
  development outcome. After authorization, amendment of a primary
  method/family/metric invalidates the campaign rather than editing a
  result-facing document.

### G6 — Official campaign materialization

- Materialize the signed M0-M5 episode packs, model/provider configuration,
  public/hidden evaluator commitments, tool environment, budget ledger, and
  analysis environment exactly from the G4b manifest.
- If an optional target-profile extension was signed, materialize its pairs and
  evaluator-owned compliance commitments without changing functional
  obligations or hidden-oracle semantics across members. Otherwise no profile-
  pair material is required.
- Reject a missing, mismatched, or unsigned split, method, prompt, model,
  evaluator, tool, budget, or analysis hash before any official model call or
  hidden evaluation.
- Acceptance: a sealed no-outcome campaign package and inference preflight on
  non-official dummy tasks. No training dataset, checkpoint, adapter, merge, or
  model-training process is created.

### G7 — Official held-out experiment

- Execute the frozen conditions without changing prompts, tools, budgets,
  oracles, or model weights.
- Execute the signed ambiguity audit as a separate, stop-before-generation
  population after intake code, profiles, labels, and analysis are frozen. Audit
  results may not trigger adaptation, official-instance exclusion, or reruns.
- Acceptance: every semantic-instance cluster in the signed G4b manifest has a
  reconciled design outcome or declared infrastructure status; each terminal
  candidate receives at most one hidden evaluation; analysis regenerates every
  confirmatory table from immutable events.

### G8 — Physical confirmation and optional target-profile adaptation

- Run the predeclared OpenXC7 subset for eligible frozen candidates; optionally
  run the same RTL through Vivado.
- Core acceptance reports unconditional VPP-L4, conditional L3-survivor
  attrition, timing/resource outcomes, train/test/flagship strata, `not_run`,
  missing-tool, and design failures separately.
- If a target-profile extension was signed, run every pair under its profile-
  specific project, constraint, L3, and OpenXC7 L4 flow without adapting prompts,
  budgets, model weights, invariants, or compliance rules after outcomes. Its
  separate acceptance additionally reports `TPA-L4`, baseline/variant outcomes,
  full-pair denominator, compliance violations, cost availability, and
  unavailable reasons; extension failure does not erase completed core results.

### G9 — Paper claim freeze

- Select the supported TRETS claim track from the observed evidence.
- Bind every result sentence/table/figure to artifact IDs and denominators.
- Bind every ambiguity claim to the named audit manifest, base-cluster
  denominator, disposition confusion matrix, false-proceed bounds, assumption/
  default provenance, and leakage audit. Never describe an audit disposition as
  a generated-project result.
- Run citation, leakage, statistics, reproducibility, and claim-language audits.

## 11. Result-contingent publication tracks

- **Track A — contract/evaluation method paper:** one or both frozen RQ1 primary
  contrasts and/or the RQ2 contrasts support bounded value beyond their matched
  controls, hidden/public separation and missingness audits pass, and the
  relevant lower confidence bounds exceed the G4b rule. Center the supported
  contract, materialization, system, repair, and evaluation contribution without
  learned-model language.
- **Track B — benchmark/evaluation methodology paper:** method effects are mixed
  or imprecise, but the evaluator-owned hidden protocol, requirement-boundary
  audit, reproducible project benchmark, failure transitions, and cost evidence
  form a defensible TRETS contribution. Do not claim method superiority.
- **Track C — artifact or negative result:** neither treatment improves the
  controls or the protocol cannot support the planned inference. Publish or
  retain the benchmark, cost/failure analysis, and negative evidence without a
  method-superiority claim.

The signed ambiguity audit is reported under every track. Passing permits only
a bounded claim for its named cases and frozen profile. Failure is a reportable
negative result and forbids claims that the system safely handles arbitrary
short, incomplete, ambiguous, or unsupported requirements; it does not license
removing audit cases or official VPP instances.

The target venue is ACM TRETS. Venue positioning centers RQ0/RQ1/RQ2/RQ4,
project-level hidden evaluation, reproducibility, failure/missingness semantics,
and cost. Training and TCAD-specific extension requirements are outside this
Paper-1 program.

## 12. Claim rules

### Allowed now

- SR2FPGA implements a typed contract and project-level tool/evidence pipeline.
- Deterministic/reference evidence reaches the bounded counts in current status.
- Oracle/mutation infrastructure and two representative OpenXC7 L4 results exist.
- Phase D is a completed integrity audit with a strict negative model outcome.
- HORIZON is the closest outer-loop baseline and motivates verifier separation
  and convergence-cost reporting.

### Allowed only after the named gate

- “development conformance for the frozen G3 scenario matrix” only after a
  positive `g3-acceptance-v1`; this never permits a method-effect, repair-
  effectiveness, or official-hidden-performance claim;
- “bounded requirement-boundary performance” only after G7 reports the signed
  ambiguity manifest, full disposition confusion matrix, false-proceed interval,
  clarification replay, provenance violations, and leakage audit;
- “closed Project Contract” after G1;
- “frozen official benchmark” after G4b;
- “deterministic-materialization/edit-surface benefit” only when the M4−M3
  primary claim rule passes;
- “untrained end-to-end Project Contract value” only when the M4−M0 primary claim rule
  passes; the complete RQ1 claim requires both primary rules;
- “repair effectiveness” after real transitions plus the paired repair-policy
  and end-to-end RQ2 analyses;
- “physical improvement” only for the G8 tool/family subset; and
- “target-profile adaptation” only after G8 reports the signed pair manifest,
  full-pair denominator, invariant/compliance outcomes, L3/L4 results, and cost;
- “commercial reference” only for successful Vivado artifacts.

### Forbidden without new evidence

- resolving arbitrary incomplete or ambiguous hardware requirements;
- treating `ready`, `needs_clarification`, `capability_gap`, a declared default,
  or a correct clarification question as a project/VPP success;
- inferring project correctness from an A_req case for which no project and no
  hidden semantic evaluation were executed;
- first repository-level/hands-free/tool-feedback RTL agent;
- first hardware IR or untyped CPPL;
- a “typing alone” correctness effect from M3−M2 rather than the frozen
  Project Contract representation-bundle interpretation;
- a skeleton-text-only, editable-byte-only, or lowerer-rule-only causal effect
  from M4−M3 rather than the frozen materialization/edit-surface bundle;
- a complete RQ1 claim when only one RQ1 primary rule passes, or use of the
  secondary M3−M2 estimate to rescue a failed primary rule;
- full JSON-Schema H0, full W1-W10 H1, or universal by-construction correctness;
- trained-model, training-view benefit, held-out, repair, or QoR-prediction
  results that do not exist;
- 24/24 L4, general L4, `.bit`, Vivado, or L5 claims;
- general target-profile portability, cross-device or cross-vendor adaptation,
  or adaptation credit from baseline-only/survivor-only results;
- application-realistic RL/vision/radar/SoC claims from synthetic shells;
- transferring T10 evidence to T11 or catalog intent to evidence;
- comparing HORIZON's iteration-0/best-so-far convergence with independent
  Pass@1 as if they were the same metric; and
- treating `APPROVED`, `not_run`, infrastructure failure, or
  `repair_trajectory` bucket labels as model success.

## 13. Required artifacts

Each outcome-producing campaign must preserve, under stable controlled paths:

```text
research_freeze.json
g3_acceptance.json
requirement_disposition_contract.json
ambiguity_audit_manifest.json
ambiguity_oracle_commitments.json
ambiguity_audit_events.jsonl
ambiguity_audit_outcomes.json
ambiguity_audit_summary.json
benchmark_split_manifest.json
candidate_protocol_manifest.json
campaign_freeze_manifest.json
g4b_authorization_receipt.json
paired_block_manifest.json
episode_pack_public_manifest.json
episode_pack_private_commitments.json
method_condition_contract.json
prompt_and_contract_hashes.json
model_and_gateway_provenance.json
tool_versions.json
run_state.json
per_attempt_events.jsonl
paired_outcomes.json
hidden_evaluation_outcomes.json
cost_summary.json
infrastructure_missingness.json
leakage_audit.json
artifact_audit.json
analysis_environment.json
```

An activated target-profile extension additionally requires
`target_profile_pair_manifest.json`, `target_profile_commitments.json`, and
`target_profile_outcomes.json`. These files are not empty placeholders and are
not required when the extension is omitted.

Candidate projects retain their public requirement projection, generated PC
when applicable, files, diagnoses, patches, public tool outputs, measured QoR,
and trajectory links. Hidden score summaries are retained only in evaluator-
owned outcome bundles, never in candidate workspaces or repair-visible logs.
Raw hidden oracle contents remain protected and
physically separate from public pack material and repair-visible logs.

Every paper table must be regenerable from these artifacts and must show its
population, denominator, negative count, `not_run` count, infrastructure count,
tool stage, and method condition. If the optional extension is active, every
adaptation table additionally shows `profile_pair_id`, baseline/variant
profiles, change axis, invariant/compliance status, full-pair denominator, cost
availability, paired cost, and unavailable reasons.

## 14. Relationship to implementation work

This is a research and experiment contract, not a step-by-step runbook. Current
commands live in `agent/README.md`, `training/README.md`, and their config/script
READMEs. After this spec is accepted, each gate may receive a narrow dated
implementation plan. No historical plan is reactivated by this document.

Changes to the research question, held-out families, primary metric, baseline
privileges, or outcome-dependent stopping rules require a versioned amendment
before official results are opened. Mechanical path corrections and additional
non-primary diagnostics may be recorded without redefining the primary test.

The subordinate code-architecture specification may define implementations and
tests, but it may not add G3 acceptance rows, official prerequisites, scientific
contrasts, or information privileges beyond this v1.7 freeze without a
versioned research amendment.
