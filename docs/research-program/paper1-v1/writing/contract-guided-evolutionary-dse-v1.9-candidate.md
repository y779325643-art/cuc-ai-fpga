# Contract-Guided Evolutionary Design Space Exploration — v1.9 Candidate

## Status

- Decision date: 2026-09-08
- Decision: user accepted the PI and hardware-architecture corrections
- Target venue: IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems (TCAD)
- Role: candidate Paper-1 redesign in which evolutionary DSE is the central method
- Authority: design proposal only; the canonical Paper-1 specification remains `paper1-v1.8` until this candidate passes affected-scope review and is propagated
- Execution: no implementation, model run, QoR pilot, hidden evaluation, or official experiment is authorized by this document
- Discussion authority: confirmed decisions, unconfirmed protocol proposals, and the next-chat continuation prompt are tracked in `v1.9-discussion-ledger-and-next-chat-handoff-2026-09-10.md`
- Resolved review finding: `LOGIC-001` (2026-09-08); v1.8 is retained as the deterministic-generation and bounded-repair foundation, while v1.9 owns the primary DSE questions
- Resolved review finding: `METH-001` (2026-09-09); LLM semantic mutation produces a sealed concrete RTL patch, EA supplies population selection and inheritance, and bounded public repair is a costed recovery channel
- Resolved review finding: `EVID-001` (2026-09-10); DSC quality uses user intent authority, a presealed independent expert opportunity reference, open-set adjudication of novel proposals, and fixed-policy downstream utility evidence without claiming architectural completeness

## One-sentence argument

SR2FPGA is studied as a hardware-code-generation harness that combines a frozen
design-space contract, domain-aware LLM variation, deterministic project
assembly, bounded public repair, real-tool feedback, and evaluator-separated
validation to explore complete FPGA projects.

This is a candidate contribution. It must not be described as demonstrated until
the registered implementation, excluded pilot, and official experiment exist.

## Harness identity and evidence states

The harness accepts resolved requirement facts, invokes an LLM to produce
candidate hardware code, assembles a complete FPGA project, drives independent
verification and implementation tools, returns public diagnostics for bounded
repair or evolutionary variation, and seals the resulting artifacts and
lineage. Generation remains open: a clear request may produce a candidate even
when some downstream evidence is unavailable. Evidence status, rather than a
single top-level refusal label, determines what may be claimed.

Every attempt records four independent axes:

- `generation_status`: whether a concrete candidate FPP was produced;
- `requirement_status`: whether the governing facts are resolved and coherent;
- `verification_status`: whether independent functional and protocol evidence
  passed, failed, was not run, or is not assessable;
- `implementation_status`: whether synthesis, place-and-route, and target
  measurements passed, failed, were not run, or are not assessable.

Delivery credit is derived from these axes. Producing RTL is not itself verified
delivery, while unavailable verification or implementation evidence does not
erase the generated candidate. Confirmatory EA admits only candidates with the
predeclared public evidence required by its fitness; other harness outputs remain
traceable unverified candidates and receive no verified-performance credit.

## Confirmed narrative and research hierarchy

The research progression is problem-driven rather than a claim that
deterministic generation is itself restrictive. The v1.8 line studies how a
typed contract, deterministic materialization, and bounded public repair can
produce or recover one auditable FPGA project. That foundation makes project
construction reproducible, but it does not represent or compare multiple legal
architecture decisions and does not close real tool-measured QoR around
architecture selection. The v1.9 line therefore lifts the single-project
mapping into a frozen contract-constrained design space and studies whether
evolutionary search can find better feasible alternatives under expensive,
discrete, black-box evaluation.

The absence of a search loop is a methodological gap, not evidence that current
generated projects have poor performance. EA is likewise a tested search
hypothesis rather than an inevitable consequence of the gap; it must be compared
against equal-budget non-adaptive, conventional evolutionary, and applicable
black-box alternatives.

The primary questions are RQ1--RQ4 below. Earlier work is retained through two
secondary questions rather than as a competing primary hierarchy:

- **SRQ1 -- Deterministic project foundation:** under matched requirement facts
  and budget, can the contract and deterministic-materialization pipeline provide
  a valid, reproducible starting FPGA Project Package for architecture search?
- **SRQ2 -- Bounded recovery:** on frozen public-failing projects, can a bounded
  public repair policy recover feasibility without using hidden information?

SRQ1 and SRQ2 cannot unlock or rescue any primary DSE conclusion. The frozen
repair policy may recover an eligible public-failing child, but the original
failure and all repair cost remain recorded; only a fully re-evaluated repaired
child may enter the feasible population. Requirement-boundary auditing remains
a qualification gate rather than a third research question. Existing v1.8
artifacts remain historical or supporting evidence and must not be relabeled as
v1.9 outcomes without a compatible frozen protocol.

## Canonical terminology

Naming follows the [2026-09-08 terminology ledger](../../../specs/2026-09-08-sr2fpga-terminology.md).
This naming synchronization does not change the candidate definitions or review status below.

| Term | Meaning |
| --- | --- |
| **Hardware Code Generation Harness** | The SR2FPGA orchestration boundary that generates candidate RTL/projects and records requirement, verification, implementation, repair, evolutionary, and evidence state |
| **Design-Space Contract (DSC)** | Frozen variables, domains, semantic transformations, invariants, cross-variable constraints, and evaluation commitments |
| **Design Point (DP)** | One sealed candidate record containing its semantic architecture decision, concrete RTL patch, parent lineage, and resulting artifact hashes under the DSC |
| **Project Contract (PC)** | The decoded requirement-to-project obligations for one DP; currently serialized internally as System-HIS v1.2 |
| **FPGA Project Package (FPP)** | The materialized RTL sources, constraints, manifest, build metadata, and declared supporting artifacts |

The paper-facing chain is **Design-Space Contract → Design Point → Project
Contract → FPGA Project Package**. `System-HIS v1.2` remains an implementation
serialization name used only where compatibility or code traceability requires
it; it is not the primary manuscript term.

## Corrected scientific boundary

The method is not gate-level CGP and does not claim that EA, LLM-guided RTL
evolution, structured hardware intent, mutation-oriented IR, or FPGA DSE is new.
CGP may inform indexed representations, inactive material, and genotype-to-
phenotype mapping, but it is not the paper's identity.

The representation layer guarantees only the properties that its validators
actually establish: schema validity, declared structural consistency,
lowerability, bounded edit surfaces, and traceability to frozen requirement
facts. It does not guarantee functional correctness, latency semantics, physical
closure, or Pareto superiority. Those require independent public and final
hidden evaluation.

## Consolidated candidate protocol — design draft 2026-09-11

Status: complete design-level draft, not an operational freeze or execution
authorization. D1-D29 remain the dated user-confirmed decisions in the handoff
ledger. The user subsequently delegated routine methodological judgment and
authorized consolidation; choices identified as **draft judgment** below are
assistant-selected design proposals, not invented individual user confirmations.
This section is the current reading of the candidate's endpoint and analysis
design, replacing the accumulated D12-D29 summary paragraphs. Canonical v1.8,
its gates, and the separately approved PC layered study are unchanged.

### 1. Scope, cohorts, and intended claims

**Confirmed basis: D12-D21, D25-D29.** LLM+EA searches for better PPA subject to
accepted requirements. Single- and multi-FPGA architecture/evaluation design
are in scope; board count has no default priority. Functional/protocol validity,
resource limits, and accepted performance bounds are feasibility constraints.
No missing user preference is invented. Preserve resource/PPA tradeoffs when
preferences do not identify a unique choice.

D32 (2026-09-14) selects FPGA-based AI accelerators as the primary empirical
domain; section 17 specifies this focus without narrowing the generic method
or changing canonical v1.8. The earlier generic task examples are illustrative.

Keep three evidence paths distinct:
- Track G: requirement completion and generation/verification/repair to a
  public-feasible FPP. Report every assigned input, success/failure/missingness,
  and generation cost. Generation is not guaranteed to succeed on arbitrary
  requirements and cannot continue without an operational resource policy.
- Track O: optimization from one common public-feasible seed per paired block.
  It estimates search performance conditional on the declared seed-qualified
  population, not unconditional requirement-to-project success. The seed must
  satisfy all declared public functional, resource, and performance obligations.
- DSC adequacy: presealed independent expert opportunities, blinded mapping,
  open-set adjudication, and downstream utility with the search policy fixed.
  Expert spaces are information references, not fair automation competitors.

The separate PC layered-study design remains the authority for its own A/B/A-R/
B-R study, including its existing correction limits. This draft neither changes
those labels nor adds their outcomes to the EA estimand.

**Draft judgment:** define independent sample inclusion before methods run.
Generation failures stay in Track G; no condition may obtain a different easier
seed after observing its own outcome. Preserve the same seed, target inventory,
public facts, evaluator and budget within each controlled optimization pair.
For a DSC-source contrast only the DSC source changes; direct-phenotype and
external methods are bundle contrasts with explicitly different information.

### 2. Public verification, repair, and sealed terminal validation

**Confirmed basis: D19, D22-D29.** A qualified independent behavioral oracle
defines accepted semantics. Public and terminal verification may share that
oracle and environment, but use separate legal stimuli. Terminal inputs,
results, or diagnostics cannot guide generation, DSC construction, search,
repair, stopping, or replacement. Hidden tests add no new requirements.
Passing is evidence for named checks, never a proof of universal correctness.

Each mutation seals semantic architecture decisions, an RTL patch, and lineage.
Skeletons plus qualified checks protect accepted obligations, child-specific
architecture, and declared edit surfaces; editable implementation details remain
open. Interface/connection, board mapping, clock/reset, state ownership, sharing,
pipeline, flow-control, numeric and project boundaries are checked where
applicable. A structure's existence alone does not prove behavior.

A repaired child has a new identity and repeats full required public checking
before QoR credit. Preserve the failed parent and all cost. Changing sealed
architecture is not preserving repair: stop the branch and use a newly admitted
mutation from a feasible parent. Each repair branch has a local allowance and
consumes common search budget. Stop at either limit. Unknown failures remain
unresolved; infrastructure errors do not trigger RTL repair. Reject out-of-scope
patch requests before application. Actual protected-content changes are integrity
incidents: stop affected evaluation and award no valid credit.

**Draft judgment:** adaptive public regression is allowed only under a frozen,
common policy. Retain all discovered public counterexamples and revalidate
affected incumbents against the enlarged suite before archive sealing. Do not
feed another method's outcomes into a currently running condition. Record
per-condition public histories; different histories are part of the treatment.
The common sealed terminal suite is unchanged. This is a development-feedback
policy, not permission to recycle official terminal stimuli.

### 3. Archive sealing, seed reference, and delivery selection

**Confirmed basis: D17-D24.** Let b identify a task/profile block, c a condition,
and q an independent execution replicate. Let C_bcq(B) contain all fully
public-feasible evaluated candidates within the optimization budget B, including
the retained seed. Let A_bcq = ND(C_bcq(B)) be the final public Pareto archive.
At search completion seal A_bcq and each artifact hash; evaluate every member
once under the common terminal stimulus commitment. Do not add earlier dominated
candidates after a terminal failure, rerun search, repair, or replace candidates.
Keep a dominated seed as immutable fallback, not necessarily as an archive member.

**Draft judgment resolving the seed-reference gap:** before any terminal outcome
is opened, also register the common seed as a separate reference object, whether
or not it is in A_bcq. Evaluate it at the terminal stage only. Reuse one verdict
for an identical artifact/evaluator/stimulus tuple within the paired comparison;
retain shared accounting. No extra evaluation is needed when that seed is already
an archive member. This does not add a seed back to the scored archive after
observing failures, and does not introduce early hidden seed qualification.

Precommit a single-project selector using only public information and accepted
preferences before terminal outcomes. A selected project's actual PPA is compared
with external methods only if its terminal checks pass. If it fails, report
failed delivery, not the next successful member chosen after seeing outcomes.
Other passing archive members support a set-level claim, not silent replacement
of the preselected project's result. Without an accepted selection preference,
report the set; do not invent a favorable single-project headline.

### 4. Primary score and supporting measures

**Confirmed basis: D18/D24.** With complete terminal decisions for every archive
member, define H(x) in {pass, fail} and:

A_pass_bcq = {x in A_bcq : H(x) = pass}
Y_bcq = NHV_b(A_pass_bcq)
Y_public_bcq = NHV_b(A_bcq)

The primary set-quality quantity is Y, not public NHV. All-completed/no-passing
archive gives Y = 0. Retain public NHV and Y_public - Y as diagnostics. A known
failed candidate contributes no primary credit. No unapproved threshold on the
fraction passing multiplies Y; separately report candidate pass fraction,
all-archive-pass and any-pass status, and terminal project success. These are
different descriptive validity views, not a newly approved mandatory gate.

**Draft judgment:** when the separate seed passes, G_bcq =
Y_bcq - NHV_b({seed_b}) is the D21 terminal-qualified increment. A failed or
unassessable seed makes G not assessable; do not use zero as its baseline.
Retain Y and the original Track O membership even when the seed fails terminal
testing, and report the shared seed defect. G may be negative: a public dominator
can remove the seed from A and then fail terminal testing. Do not clamp negative
increments, insert the seed after outcomes, or claim monotonic hidden improvement.
Public seed-relative progress remains a separate process diagnostic.

Public anytime/AUC, first feasible generation, valid evaluation density, archive
size and raw PPA are secondary diagnostics. Public anytime quality is not
terminal-validated anytime quality; do not retroactively test unsealed past
archives and present that as the prespecified primary experiment.

### 5. Objective signature, normalization, and reference point

**Draft judgment under D12-D18:** before any outcome-producing use, each block
has a common objective signature: metric identities, physical scope, units,
directions, tool stage, workload, resource counting rules, normalization anchors,
reference point, and bounds policy. All paired conditions use it unchanged.
Task needs determine latency versus sustained throughput; frequency remains an
implementation metric. Report LUT/FF/DSP/memory separately, checking every board's
capacity. Sum same-type resources only with comparable definitions and include
communication/control/buffering overhead. Power and energy retain explicit system
boundaries and estimate-versus-measurement labels. No automatic scalar area score.

For a declared minimization-oriented vector g_b(x), use affine coordinates

z_bk(x) = (g_bk(x) - a_bk) / (r_bk - a_bk),  with a_bk < r_bk.
NHV_b(S) = volume of the union over x in S of
           {u in [0,1]^d : u_k >= z_bk(x) for every k}.

Thus the evaluation region is explicitly bounded and the normalized reference is
the all-ones vector. Maximization metrics require a predeclared monotone direction
conversion. Good-side saturation and reference-side zero contribution are
explicit consequences of the bounded region; report raw values and out-of-anchor
counts so that improvements outside it are not hidden. NHV = 0 alone does not
prove an empty passing set: feasibility and score are reported separately.
Do not refit anchors after seeing compared outcomes or replace invalid/missing
power with zero. Anchors require engineering/measurement justification; the
numerical values, especially throughput bounds and multi-device power, are TBD.

This region introduces evaluation preferences and can mask extreme improvements.
Report raw Pareto plots and prespecified anchor sensitivity descriptively; never
pick the anchor yielding the desired winner. If coverage of the declared region
cannot be justified before the cohort, do not promote NHV to operational use.

Do not automatically average NHV across objective signatures, device accounting
conventions, or evidence tiers. The default is separate signature strata.
Per-stratum macro analysis requires a justified common interpretation of the
normalized region; otherwise report block-wise paired effects without a pooled
headline. Reported metrics need not all be optimization dimensions. A block
with unavailable required objective evidence is ineligible for that confirmatory
signature; no outcome-driven removal of the inconvenient objective is allowed.

### 6. Independent units, replicates, and aggregation

**Draft judgment:** a task/profile block is a pairing unit. The independent
benchmark sampling unit is a predeclared base semantic requirement cluster.
Paraphrases, related assumption branches, profile variants, execution replicates,
and descendants do not independently increase n. Audit shared seed/RTL provenance
for additional dependence; merge dependent base instances or account for the
higher dependency cluster before analysis. Named families are fixed strata,
not evidence of generalization to all possible hardware families.

Within a compatible signature stratum, form paired condition differences per
block and replicate; average replicates within block, then use predeclared
profile weights within base cluster. Default equal profile weights apply only
to deliberately balanced comparable profiles. Average clusters within each
family and then use equal-family macro weights. Retain all paired observations
when resampling a base cluster; if dependence crosses families, resample the
higher clusters jointly rather than separately. Do not pool all Design Points,
perform candidate-level t-tests, or treat provider requested seeds as proof of
identical realized randomness. Freeze provider configuration and separately
randomize/balance execution order. Report per-family and per-profile results.

Primary precision estimation uses cluster-respecting uncertainty on paired
effects. Test implementation, interval calibration, minimum relevant effect,
multiplicity and power remain pilot-dependent, not numeric defaults imported
from another protocol. The proposed main contrast is D-LLM-EA minus D-RND on
their common qualified scope; expanded confirmatory contrasts require a
predeclared multiplicity family before official outcomes. No p-value, alpha,
sample count, effect threshold, or achieved power is supplied by this draft.

### 7. Missingness, failures, and terminal incompleteness

**Draft judgment implementing D24/D28/D29:**

| Situation | Primary score and records |
| --- | --- |
| All terminal outcomes complete; some pass | NHV of passing subset; retain failures and costs |
| All terminal outcomes complete; none pass | Zero; retain run in denominator |
| Some terminal outcomes unresolved/infrastructure-failed | Y not assessable; never automatically zero or complete-case success |
| Public evaluator unavailable during search | Record infrastructure-truncated run; distinguish observed archive from a completed-budget outcome |
| Known candidate error within permitted search | Count failed attempt/cost; repair only under declared rules |
| Actual protected/evaluator integrity violation | Stop affected scope; invalidate affected evidence pending an integrity decision |

For terminal incompleteness with known public objective values, let P be known
passing members and U unresolved members. Report bounds [NHV(P), NHV(P union U)]
as sensitivity evidence, not a fabricated observed score. For condition contrasts,
propagate lower/upper bounds without dropping the paired partner. Even collapsed
score bounds do not convert an uncompleted terminal check into a pass record.
Report missing counts/reasons per condition and cluster. Do not claim superiority
from successful cases alone; confirmatory interpretation remains on hold if
missingness can reverse the comparison or its prespecified precision criterion.

Infrastructure retries, if later permitted, use the same immutable artifact,
tool/configuration, and stimulus identity, have a fixed finite limit, and cannot
follow a committed semantic outcome. Retry limits and diagnosis thresholds are
TBD. No rerun is selected for favorable PPA or hidden success. Distinguish
predeclared long-running-design limits from a failed tool environment.

### 8. Search budget and cost ownership

**Draft judgment:** use a predeclared maximum of candidate-construction attempts
B as the primary algorithmic stopping budget for the initial matched-policy
comparison. Count each new proposed realization/repair attempt, including malformed,
rejected, duplicate, and failed outputs; preprocessing or feedback-only model
calls still count in costs, not as extra free candidate attempts. One repair
attempt consumes both its branch allowance and B. Sampling without replacement
and exhaustion behavior are frozen, not chosen after a result. API transport
retries and tool retries have separately frozen accounting. Exact B is TBD.

This is equal attempt opportunity, not equal compute, model calls, dollars,
or EDA effort. Impose predeclared common safety ceilings on model spending and
tool/wall resources. If they bind before B, record the termination reason and
attained budget; describe that analysis as a shared resource-envelope comparison,
not completed equal-B execution. Do not discard such runs as inconvenient.
Pilot feasibility must show whether B is a sensible primary comparator before
the operational freeze; economic-efficiency claims require separately matched
cost analysis, not merely this attempt budget.

Record generation, seed qualification, DSC construction/review, search,
repair, terminal validation, and infrastructure overhead in one physical-event
ledger. Human expert/review time is separately visible. For each cost axis:
- actual shared cost: charge each physical event once;
- standalone-attributed cost: charge each condition all prerequisites it would
  need if run alone, with the attribution rule and shared-event IDs;
- incremental search-policy cost: condition-specific search/repair above the
  same shared preparation, never labeled end-to-end cost.

Terminal verification is held outside feedback-producing search B, but fully
included in evaluation and standalone total cost; larger archives are not free.
Repair gets no free model/tool allowance. Report actual calls, tokens, API price
snapshot/spend, simulation, synthesis/P&R jobs, EDA time, wall time and storage;
their unavailability remains explicit. No estimated runtime or paid budget is
invented. Numeric resource ceilings await evidence and explicit execution consent.

### 9. Archive size and adverse selection

**Draft judgment:** retain the full nondominated archive of fully evaluated
candidates within the finite attempt budget; do not introduce a post-outcome
archive cap. Freeze exact-duplicate policy using artifact identity and the full
required objective record. Objective ties between different artifacts remain
distinct until a predeclared tie policy is justified; they may have different
terminal behavior. No favorable member is chosen after terminal outcomes.

Primary Y deliberately evaluates the delivered public-frontier subset, not the
best hidden-valid frontier among all past candidates. A public-failing or public-
dominated design is not backfilled after terminal failure. Therefore known
public-hidden divergence can reduce delivered archive quality; this is a result
of the declared product selection policy, not a reason to rewrite the archive.
Report archive size, duplicate counts, validation attrition, and terminal costs.
If full archive validation is infeasible in the excluded pilot, revise its
prospective policy before freezing a new cohort; do not truncate after outcomes.

### 10. DSC adequacy, baseline qualification, and physical evidence

D9's expert opportunity references and open-set adjudication remain mandatory
design elements. Add a diagnostic panel for raw/legal DSC cardinality, reachable
variable/domain coverage, realized transformation coverage, architecture diversity,
unique phenotype ratio, duplicate rate, and valid objective-bearing tool
evaluations per attempted candidate plus tool resource used. Legal density alone
cannot establish useful search-space quality. Archive or reference coverage
requires an independently defined reference and explicit denominator.

A finite DSC assignment grid does not enumerate all open LLM RTL realizations.
Exhaustive assignment enumeration is at most a reference for a frozen deterministic
realization mapping; it cannot establish a global Pareto ceiling for unrestricted
LLM patches. FPP hash uniqueness is artifact uniqueness, not functional or
architectural novelty. Report those separately; no result is imputed when reference
coverage is unavailable.

Multi-FPGA feasibility is checked per device/resource and per physical link,
using declared topology, bandwidth and timing obligations. Evaluate end-to-end
latency/throughput and system power boundaries. No board count or target inventory
is invented. Synthesis estimates, routed evidence and board measurements remain
separate strata; a simulation model of a link is not measured board throughput.
PPA route qualification and required physical stage remain unresolved, so no
batch-QoR readiness or board-delivery claim is made by this draft.

Baseline design identifiers below are candidate-document labels only. They do
not rename runtime methods, skeleton levels, contracts or the PC layered study.
All external methods need identity/version, native smoke, adapter conformance,
common-evaluator and budget gates before being called runnable fair comparisons.
REvolution remains the highest-priority adapted baseline. CRADLE/FinHardBench
remain published comparators; POET, EvoVerilog, EvolVE and Dr. RTL are conditional
adaptations; Ares is a cost-protocol reference pending artifact qualification;
HINT/HORIZON are representation/harness references; FPGAgent/AutoDSE are
cross-paradigm references. These roles reuse the dated audit, not newly asserted
release status. Human/exhaustive references are not fair automation competitors.
No cross-paper PPA headline ranking is authorized.

### 11. Prospective readiness sequence and remaining decisions

**Draft judgment, not replacement gate authority:** the dependency sequence is:
1. acceptance requirements, oracle/stimulus qualification and protected boundaries;
2. child-decision, patch assembly, architecture-preservation and lineage closure;
3. bounded tool-only repeatability/failure/throughput assessment design;
4. preliminary candidate protocol with metrics, cohorts, budgets and comparisons;
5. explicitly authorized excluded pilot, disjoint from official requirements;
6. evidence-based operational parameters, affected-scope review and versioned
   propagation plus signed campaign authorization;
7. official public search, then archive sealing and per-member terminal validation;
8. registered physical analyses, sensitivity checks and claim freeze.

Required public physical metrics are produced during search before fitness;
step 8 is not permission to defer required feasibility/QoR until after selection.
Steps 3/5 are not authorized to run by being listed here. Whether tool-only
qualification needs implementation is a separately scoped decision.
Canonical G/EA-G receipts are not inherited by this proposed v1.9 sequence.

Still evidence-locked: actual device/link inventory, qualified tool/physical stage,
block objective signatures and numerical anchors, B and repair/resource limits,
generation stopping rules, provider qualification, oracle coverage, baseline
commits and comparable realization routes, variance/missingness and cost pilot,
effect/multiplicity/power/sample size, and signed propagation/execution authority.
No missing decision is silently marked complete.

This draft resolves the structural reading of EXPT-PROTOCOL-001 but does not
close its operational blocker. EXPT-FAIR-001 has an atomic draft matrix, not
qualified executable methods. TERM-001 is addressed in candidate prose only.
EXPT-AGG-001 and COST-001 have explicit design rules, not measured closure.
EVID-002 still requires actual batch-QoR evidence. GATE-001 has prospective
dependencies, not new approved gates.

Methodological basis: the registered Auger et al. hypervolume source
[auger-hypervolume-2012] cautions about reference-region preferences. For the
cluster-aware design rationale, see [Lazic et al., 2020](https://www.nature.com/articles/s41598-020-59384-7).
The latter is a method reference used for this draft; it is not promoted into
the local claim-ready citation registry. The draft makes no SR2FPGA outcome claim.

### 12. Task/platform boundary specification — refinement draft 2026-09-12

User scope correction (D30, 2026-09-12): do not restrict the architecture-design
method to the example task families, a particular board model, one/two boards,
homogeneous devices, or a single link type. Treat workload semantics and platform
capabilities as explicit inputs. The table below supplies illustrative existing
entry points, not a closed benchmark list or a restriction to streaming/exact
arithmetic. Accepted semantics determine appropriate numerical and state checks.

Represent a supplied platform as a finite device/link graph: nodes carry device
identity, usable resource capacities, memory, clocks and tool/evidence routes;
edges carry endpoints, transport, bandwidth/latency and flow-control assumptions.
This is a conceptual design input, not a new implemented schema. LLM+EA can
explore architecture and placement over the declared graph while preserving
accepted requirements. The graph may be heterogeneous and contain more than two
devices. Platform facts are not invented or mutated by search. Each comparison
still instantiates and freezes a finite platform and legal DSC domain.

General method scope is distinct from qualified execution coverage. Missing
backend, oracle, link or power evidence limits the corresponding claim and is
recorded explicitly; it does not justify an artificial global task/board cap.
No claim of universal hardware support or unbounded physical resources is made.

| Workload class | Existing entry point | Architecture opportunities to assess | Required new evidence |
| --- | --- | --- | --- |
| FIR/filter bank | fir_filter; matched_filter as a separate existing family | sharing/parallel taps, pipeline, local accumulation before transfer | independent bit-exact stream oracle, rate/overflow bounds, nontrivial opportunity set |
| Matrix-vector/reduction | matrix_vector_mac | row/column partition, replicated inputs vs partial-result transfer, compute/memory balance | accepted reduction/overflow semantics, bandwidth model and full resource accounting |
| Windowed image pipeline | sobel_threshold | stage/tile partition, line-buffer organization, boundary transfer | frame/tile boundary oracle, halo/accounting and sustained-stream checks |
| Flow-control qualification | stream_fork_join | ordering and backpressure across partition boundaries | liveness under declared fairness, no-loss/duplication checks; not standalone evidence of rich PPA search |

The catalog is an inventory of definitions, not proof that expanded workloads,
architectures, or multi-FPGA versions are qualified. FIR and matrix-vector have
representative historical tool routes in current documentation; those small
historical instances are development references, not new official test items.
Do not place variants of a development instance or reference seed into an
independent held-out split merely by changing width, wording, or board mapping.
Freeze lineage-aware development/pilot/official assignments before outcomes.

Do not preset an initial one/two-device, homogeneous-board, or single-link
envelope as the research boundary. A later experimental cohort selects and
reports concrete configurations sufficient to test its claims, without claiming
they exhaust the method's scope. Inventory rows for that cohort include
board/part/revision/count, usable resources after
shell reservation, clock/reset/I/O, link endpoints and protocol, payload rate/
latency, flow control, tool/license availability, and measurement facilities.
Unknown entries remain unknown; do not assume direct DDR sharing, lossless links,
or a physical interconnect from a board-profile name.

Current configuration evidence: agent/configs/current/
sr2fpga_line_a_l4_representative.example.yaml names XC7Z020CLG484-2,
ac820_zynq and openxc7_nextpnr. It establishes a configured target, not ownership,
available board count, real link bandwidth, or board-tested timing. The earlier
request for an inventory is not a prerequisite to continue general design.
Concrete inventory remains necessary only when qualifying a particular execution
cohort; no current hardware possession is inferred.

Before main methods run, classify workload pressure from independent engineering
screening into: single-device feasible; near resource/performance limits; and
no qualified single-device implementation found within the declared preparation
procedure. The last category is not a proof of single-device impossibility.
Do not generate only cases on which multi-device placement wins. Preserve cases
where communication makes multi-device architecture worse. Track O still requires
a common public-feasible seed; a multi-device seed is allowed when it meets the same
declared inventory/requirements. Failed seed acquisition belongs in Track G,
not silently removed from an end-to-end success claim.

For each selected block, produce a reviewable record (no new runtime schema here):
requirement/semantic-cluster IDs and provenance; split; accepted facts; available
inventory; seed identity and public evidence; candidate DSC source/hash; legal
variables; reference/terminal stimulus commitments; objective signature and
anchor provenance; budget accounting and declared exclusions. Do not invent
task sizes, clock targets, throughputs, or sample counts to fill the record.

### 13. Minimal comparison and realization-parity specification

The proposed priority order is core internal search evidence, a qualified external
comparison, and explanatory ablations. It does not promote any row to executable.
Keep D-LLM-EA, D-RND and D-LLM-LOCAL as the first open-realization design checks.
Retain D-EA, D-COV, D-SA, D-BO and P-PC/P-RTL in the plan, but resolve realization
support before committing scarce evaluation budget or claiming isolated effects.

| Comparison | Required common factors | Critical difference / credit boundary |
| --- | --- | --- |
| D-LLM-EA vs D-RND | requirement, seed, DSC, public tools, model/version, accounting, terminal suite | joint adaptive architecture/realization policy vs nonadaptive assignment sampling; not pure selection causality |
| D-LLM-EA vs D-LLM-LOCAL | same mutation message interface, admissible edits, public diagnostics, repair limits | population/parent/survivor mechanism versus single incumbent |
| D-EA vs D-RND on common transform subset | identical deterministic realization map, domain and evaluator | conventional search-policy effect; subset result not extrapolated to open RTL |
| LLM/expert/generic/ablated DSC | fixed qualified search and realization route | space-source effect; expert condition keeps information-reference status |
| REvolution-adapted vs main method | shared accepted task and evidence/output contract, model and counted budget | end-to-end optimizer bundle; preserve native algorithm rather than installing our DSC into it |
| Multi-FPGA mapping-only vs joint architecture search | same seed, inventory/link, top-level semantics, verifier and accounting | benefit of opening compute/communication architecture decisions beyond placement |

Add D-MAP-ONLY as a separately named multi-FPGA mechanism control: freeze the
seed's compute architecture, vary only admitted placement/mapping and required
link wrappers under the same resource constraints. A bounded legal mapping
enumerator or a qualified mapping solver can implement this control; the
specific solver and supported graph are not yet selected. Main D-LLM-EA may
jointly vary compute architecture and mapping. This is explicitly a change in
design freedom, not an assertion that the methods searched the same DSC.
Count common wrapper and mapping overhead; do not give mapping-only zero-cost
implementation or count extra boards as algorithmic superiority.

For each method, prepare an input/decision/realization/feedback/output/cost
crosswalk. Every externally chosen assignment must produce one traceable concrete
patch/FPP through the registered route; generated and repaired failures consume
attempts. Common prompts exclude expert reference opportunities and terminal
stimuli. Pure EA-selection claims require a fixed common variation/realization
operator; otherwise retain the bundle interpretation. No fix to a baseline is
hidden in its adapter, and no native strategy is silently replaced.

For REvolution, first inspect the paper-linked release and emitted records; then,
only under separate authorization, perform native smoke and adapter qualification.
Reading/rerendering author logs is evidence reconstruction, not a new search run.
If native PPA fitness needs replacement for FPGA targets, register this substantive
adaptation before use, preserve the native structure, and never call it exact
reproduction. Its ASIC PPA figures cannot be ranked against FPGA resource totals.

Multi-FPGA related-work scope was checked at bounded source level on 2026-09-12:
[TAPA-CS v2, section 4](https://arxiv.org/html/2311.10189v2) takes a TAPA-format
C/C++ dataflow graph plus cluster topology, performs inter/intra-FPGA mapping
and inserts communication logic. It is a mapping/compiler comparator or
cross-paradigm reference, not a natural-language open-RTL baseline by default.
[RePart v1](https://arxiv.org/html/2604.00780v1) addresses topology-aware
hypergraph partitioning with logic replication. Its partition metrics do not
by themselves establish functionally verified system PPA.
These checks constrain novelty claims; they are not complete feature audits,
local claim-ready source chains, native reproduction, or release qualification.
The [official REvolution repository](https://github.com/kmcho2019/REvolution)
provides code, environment instructions and author-result/reporting paths;
this establishes availability, not that the adapter or results have been verified.

### 14. Evaluator qualification and excluded-pilot specification

No step below is authorized to execute. Produce an evidence package for each
route before treating it as operationally qualified:

| Route | Fixed inputs and check | Required evidence / rejection trigger |
| --- | --- | --- |
| Functional oracle | accepted numeric/transaction semantics; independent reference | positive known designs and injected defect classes; candidate cannot author final authority |
| Architecture preservation | sealed child decisions plus protected edit surfaces | positive repair and deliberate revert/split/share violations; ambiguous preservation is not a pass |
| Streaming/liveness | declared ready/valid, reset, environment fairness and finite transaction bounds | no-loss/duplicate/order and bounded completion; timeout alone is not a root cause |
| Multi-FPGA composition | same role obligations and explicit link model | payload/framing/flow-control, reset and boundary cases; no ideal-link performance assumption |
| Physical QoR | exact device, shell, constraints, tool version and seeded run policy | complete resource/timing reports and failure taxonomy; synthesis-only is not routed closure |
| Power/energy | workload/activity, measurement point and included components | estimate-confidence inputs or instrument evidence; absence does not become zero |
| Terminal isolation | fixed evaluator/stimulus commitments and sealed identities | no feedback/reselection; semantic results separate from infrastructure/integrity status |
| Cost/lineage | original and repaired artifacts plus physical-event IDs | exact actual/shared/standalone/incremental reconciliation and no missing failed attempts |

For the first tool-only repeatability pilot, use excluded, fixed qualified FPPs,
not adaptive LLM search. Repeat identical build conditions to assess determinism;
separately vary implementation seeds to characterize tool variation. Keep those
two questions separate. Measure stage runtimes, resource/timing dispersion, tool
failures, concurrency/throughput, and complete archive-evaluation cost.
No number of repeats, timeout, throughput, or budget is guessed in advance of
the resource/instrument inventory.

For the subsequent excluded search pilot, exercise seed acquisition, at least
the core common-realization controls, architecture-preserving repair, finite
branch/common stopping and sealed archive evaluation. Use only disjoint pilot
stimuli and instances, never official hidden cases. Revisions after pilot
outcomes apply to a new frozen official cohort; the pilot is not included in
formal effect estimates. Pilot evidence supports budget feasibility, missingness,
variance and interval/power calibration. A minimum meaningful improvement must
have an engineering rationale, not be set just below the observed method gain.

The primary objective record has two layers: active optimization dimensions and
all reported/constraint metrics. Candidate profiles may emphasize latency or
throughput, but resource conversions and power evidence cannot be invented to
force a uniform PPA score. No reduced metric profile may be advertised as full
PPA superiority. A profile without qualified power can support a separately
declared limited QoR claim only; it does not satisfy the power-bearing cohort.
Profile choice is made before comparative outcomes, and the main PPA claim stays
open until required measurements qualify.

Resource planning uses explicit symbolic counts:
N_search = sum over registered blocks of (conditions x replicates).
N_terminal = sum of sealed unique archive objects plus precommitted reference
objects not already checked under the identical evaluator/stimulus identity.
Terminal costs are estimated from the excluded archive-size/runtime distribution;
the maximum candidate-attempt budget bounds generated objects but does not make
verification cost equal across methods. Common hardware, software, and activity
assumptions are mandatory. Terminal tests follow public physical qualification;
later physical analysis does not retroactively make an unqualified search valid.

### 15. Design closure checklist and evidence ownership

The next reviewable deliverables are now specified:
1. task/platform/link/metric records, with real inventory sources and unknowns;
2. method-by-method realization parity and adaptation crosswalk;
3. evaluator qualification matrix and separately authorized two-stage pilot plan.

A design row is ready for operational freeze only when it names the artifact
and reviewer responsible for each prerequisite, passes requirement/lineage and
measurement checks, and has calibrated resource/statistical parameters.
Do not substitute a catalog row, model narrative, or public repo link for those
artifacts. Known scope limits remain in the report even if the main method wins.
Independent clusters/signature strata from section 6 are unchanged; no new
family-level sample count or inferential threshold is approved here.
The multi-FPGA source review is partial, and EXPT-FAIR-001/EVID-002 remain open.

### 16. Requirement, platform, and architecture objects — 2026-09-12

D31 confirms the three-object separation below. Fields and the impact/check
matrix are analyst-developed specifications under delegated judgment, not new
runtime schemas or contracts.

| Object | Contents and provenance | Mutation authority |
| --- | --- | --- |
| Requirement contract R | accepted functional/numeric/protocol/timing obligations, legal environment, preferences, provenance | user/accepted derivation authority; search cannot rewrite requirements |
| Platform graph P=(V,E) | devices/resources/memory/clocks, links/modes/service assumptions, tool/evidence routes | external facts; search cannot invent devices, capacities, or links |
| Architecture proposal A | role realization, modules, parallelism/sharing, scheduling, storage, placement, channels and concrete patch | LLM+EA inside DSC and R/P; repair preserves sealed child decisions |

R/P are frozen within a comparison block. Available devices and physical
connections are inputs; active-device selection and distribution of work are
architecture outputs. Selecting another declared device or supported configurable
mode is allowed within DSC. Adding a device, changing physical connectivity or
inventing bandwidth requires a new accepted platform record/block. No global
board-count, task-family, homogeneous-device or transport restriction is imposed.

#### Field responsibilities and provenance

R records obligation IDs, observable semantics, accepted numeric tolerance or
bit-exact behavior, legal inputs/environment, acceptance criteria, check mapping,
source and acceptance state. Hard constraints and optimization preferences are
separate. Unresolved semantics require resolution or distinct assumption branches,
not mixing functionally different candidates. Terminal assets remain evaluator
references, not candidate-visible content.

Each P node records device identity, resource units and usable capacity, reserved
shell overhead, memory interfaces, available clock/reset domains, legal I/O and
tool/evidence routes. Each edge records endpoints, supported transport modes,
payload units, latency/service characterization, flow control/reliability and
evidence status. Configurable modes have finite declared domains. Properties have
sources/versions and documented, measured, accepted-assumption, or unavailable
status. Assumed communication models do not establish measured board throughput.

A binds to R/P/DSC and parent hashes. It records role-to-realization mapping,
realization-to-device placement, state/storage owners, replication/consistency
obligations, logical channels and physical routes, implementation parameters,
sealed architectural invariants, allowed patch surfaces, concrete RTL changes
and public-feedback lineage. Decisions must agree with realized artifacts:
module names and LLM explanations alone cannot prove correspondence.

#### Integration with DSC -> DP -> PC -> FPP

R/P constrain the DSC's legal architecture choices. Each DP seals A and its
concrete patch/lineage. PC records realized obligations; FPP carries implementation
and evidence. LLM variation emits architecture decision and patch jointly once.
Deterministic assembly binds facts and applies the patch; it cannot silently
choose an owner or complete a missing architecture decision for the model.

A multi-device candidate is one system-level FPP whose manifest links per-device
projects, boundary obligations, inter-device channels, build inputs and evidence.
Per-device PC views may be derived from the system decision, but current PC
schemas are not claimed to implement these views. New schema design and execution
require separate work. Passing each board alone does not establish system passing.

#### Constraint closure

Check role coverage and state ownership; placement on available devices; logical
channels mapped to legal physical edges/modes; consistent interface/framing/
ordering/numeric semantics; per-device resources including shell/communication;
and end-to-end behavior, clocks/resets, timing and required physical evidence.
Predicted resource sums and traffic-rate inequalities are prechecks, not measured
feasibility. Link bandwidth alone does not prove liveness, burst safety or latency.
Demand and service must share the same workload/time units.

Missing checkers or platform facts remain explicit and deny affected evidence
credit. They do not authorize fabricated scores or globally prohibit generation.
The corresponding confirmatory cohort cannot execute until its required routes
qualify.

#### Architecture change -> obligations -> re-evaluation

This is a conservative scheduling design. Every modified/repaired child still
requires the full public acceptance suite; rows add affected checks rather than
authorize testing only one module.

| Change | Obligations to preserve | Additional checks and renewed evidence |
| --- | --- | --- |
| Module split/merge or role relocation | role coverage, interface, ownership | structural correspondence, whole-system reference comparison, affected builds/QoR |
| Parallelism/resource sharing | values, ordering, arbitration and rate | sharing/instance evidence plus arbitration/stall tests; timing/resources/workload power |
| Pipeline/scheduling | accepted latency, order, reset/stall state | transaction-aware timing/equivalence; latency, II/throughput and physical QoR |
| Storage/buffering/tiling | ownership, address/range, lifetime, overflow | ports and boundaries, memory and flow-control tests; resources/system performance |
| Placement/active-device set | fixed inventory and role semantics | affected per-device builds, link/reset/ordering checks; system PPA accounting |
| Routing/framing/transport mode | legal edges and service assumptions | payload integrity, serialization, ordering, backpressure/liveness; link/system performance |
| Clock/reset assignment within allowed domains | protected domain definitions and reset behavior | legal mapping, CDC/reset/timing constraints and affected implementation checks |
| Numeric/arithmetic realization | accepted exactness/tolerance and overflow | range/precision checks and independent oracle; arithmetic QoR |
| Internal bug repair | sealed architecture and edit permissions | architecture preservation, complete public validation, current QoR and new identity |
| Unauthorized R/P/evaluator change | authority/integrity | reject before application; actual protected changes stop evaluation |

State replication needs an explicit consistency/merge rule; permitting module
replication does not make it safe. External latency changes must already fit
accepted requirements. A behavioral requirement change is not PPA optimization.

#### Evidence dependencies and reuse

Map decisions to affected obligations, artifacts, checkers and metric producers.
Schedule the union of impacts plus full system acceptance. Placement or channel
changes require end-to-end checks even if arithmetic RTL is unchanged.
Do not inherit a parent's QoR score for a changed child.

Any future evidence cache must be separately qualified against exact artifact,
constraint/platform, workload, tool/configuration and checker-input identities.
Identical unaffected board-build evidence may be reusable; new system validation
remains required. Never reuse terminal verdicts as public fitness/feedback.
D23/D24 govern final sealed terminal evaluation unchanged.

Illustrative, not executed: changing pipeline depth changes A and requires
latency/order checks without changing R/P; moving a role changes placement and
communication but does not increase physical link bandwidth; replacing shared
compute with duplicated compute during repair changes a sealed decision and
must not receive preserving-repair credit.

Exact schemas, invariant checkers, domains and tool compatibility remain open.
This specifies design responsibilities, not current implementation capability,
canonical propagation or permission to run code/model/QoR/terminal experiments.

### 17. FPGA-based AI accelerator empirical focus — 2026-09-14

D32 confirms that the new task focus is AI accelerators implemented on FPGAs,
not ASIC tapeout. Preserve the generic LLM+EA/DSC method and R/P/A separation;
AI acceleration is the primary candidate empirical domain. Existing generic
RTL families remain engineering/qualification references, not sufficient by
themselves to support AI-accelerator system claims. D30's absence of preset
board/model/count/topology caps is unchanged. The exact benchmark suite and
operational protocol are not yet frozen.

The designing LLM and the accelerated AI workload are distinct objects.
This focus does not authorize training/fine-tuning either model, changing a
fixed workload for a favorable hardware result, or executing model/tool runs.
Workload mode (such as inference), model/subgraph identity, and system boundary
must be explicit in each experimental block. Using already trained fixed
weights as workload inputs is not evidence of training or a learned search
method.

#### AI-specific R/P/A responsibilities — design elaboration

| Object | Required information | Design boundary |
| --- | --- | --- |
| R: workload and requirements | operator/graph semantics, tensor dimensions/layouts, data types, rounding/overflow or error tolerance, inputs/weights, batching/sequence conditions, accepted performance and accuracy obligations | no silent precision reduction, omitted operators, changed weights or altered reference computation |
| P: FPGA platform | per-device resources, memory capacity/interfaces, effective service assumptions, clocks, link topology/modes, measurement/tool routes | externally supplied facts, not search-created resources |
| A: implementation | PE shape/parallelism, sharing, dataflow, tiling, memory banking/buffering, fusion, scheduling, device mapping and communication | LLM+EA variables under DSC with concrete RTL and evidence |

These are candidate field responsibilities, not implemented schemas. R permits
approximation only when the user explicitly accepts its error/accuracy contract.
Arithmetic reassociation, quantization and nonlinear approximations require that
contract or bit-exact preservation; functionally incorrect shortcuts never earn
PPA credit. A source framework's output is a reference only after its numerical
semantics and comparison tolerance are qualified.

#### Evidence levels within the AI workload family

Use operator, multi-operator subgraph, and complete workload as separate evidence
levels rather than treating a MAC demonstration as a complete accelerator.
Illustrative design opportunities include GEMM/GEMV or convolution, reductions
and attention-related blocks, and complete model execution. These examples are
not a closed task whitelist or a claim of support.

| Level | What it can establish | Additional evidence for the next level |
| --- | --- | --- |
| Operator | arithmetic correctness and local implementation tradeoffs | layout conversion, intermediate buffering, scheduling and composition |
| Subgraph | fusion/dataflow and inter-operator communication tradeoffs | full model coverage, weights/input handling and end-to-end control |
| Complete workload | system latency/throughput, accuracy or exactness, and total resource/energy at the declared boundary | broader-workload or platform generalization requires additional independent evidence |

Same-model layer shapes, parameter variants and random inputs do not automatically
constitute independent workload evidence. Retain the cluster/provenance policy
and hold out workload structure deliberately rather than creating many nominal
tasks from one seed.

#### Evaluation and comparison consequences

Keep the confirmed terminal-passing Pareto/NHV design. Actual PPA reporting
must include workload latency/sustained throughput, energy per completed work
unit, resource types, memory traffic and multi-FPGA communication where relevant.
Peak frequency or theoretical operation throughput alone is not the end-to-end
result. Do not introduce a default weighted PPA score.

For accelerator search, distinguish a fixed architecture's parameter tuning,
fixed-compute placement, and open architecture/RTL changes. D-MAP-ONLY and
same-realization policy controls remain relevant. REvolution retains priority
as an open-RTL evolutionary comparator on overlapping tasks, but does not by
itself cover the AI-accelerator architecture claim. SECDA-DSE, GPT4AIGChip and
traditional accelerator DSE, plus system-level co-design references such as
HSCO-Bench, require a task/abstraction-aware comparison map. Their literature
roles do not confer runnable-baseline status or authorize direct ranking of
published results from different devices/models.

The scientific emphasis is whether generated architecture freedoms and
architecture-preserving realization improve verified compute/memory/communication
tradeoffs under common requirements and resource accounting. Merely replacing
generic RTL examples with AI operators is not a new contribution.

Exact workload selection, model/weight provenance, numerical contracts, active
objective signatures, tool evidence and budgets remain open. This scope update
does not amend canonical v1.8, the independent PC study, code/contracts, LaTeX,
or execution permissions.

## Method objects

### Design-Space Contract

The LLM proposes, and the pre-search gate validates and freezes, one design-space
contract per requirement/profile block. It contains:

- accepted hard obligations and selected environment facts with provenance; functional, interface, clock/reset, ordering, precision, protocol, timing, and target properties are frozen only when explicit, necessarily derived, or accepted for the block;
- design variables and finite domains;
- allowed semantic decisions and edit boundaries for folding, sharing, replication, pipeline insertion, memory binding, arithmetic implementation choice, and other DSC-admitted changes;
- cross-variable compatibility constraints;
- allowed ranges for latency, initiation interval, throughput, resource use, and clock target;
- deterministic decoding and failure rules;
- public evaluator and terminal-selection commitments.

All fixed-space policy-comparison conditions consume the identical frozen design-space
contract. Search-space generation is not repeated per condition and receives no
outcome feedback.

### Requirement completion and DSC derivation

The user's natural-language request is not treated as an already complete
Requirement Envelope. Before DSC construction, the harness separates five
provenance-bearing classes:

| Class | Meaning | Harness treatment |
| --- | --- | --- |
| `explicit_hard` | Externally observable behavior or constraint stated by the user | Preserve and freeze |
| `derived_hard` | A necessary consequence of explicit semantics | Record its derivation and freeze |
| `proposed_default` | An interface, numeric, target, or engineering choice proposed by the harness | Expose with provenance; allow confirmation or replacement |
| `design_variable` | An implementation choice that preserves the accepted observable semantics | Place in the DSC for search |
| `unresolved_semantic` | A choice whose alternatives change the function or externally observable contract | Clarify or create explicit assumption branches |

`proposed_default` is not a synonym for a user requirement. Its record must
retain the proposed value, proposing component or policy and version, rationale,
considered alternatives, and its confirmation or replacement status. User
acceptance freezes the value but does not rewrite its provenance as
`explicit_hard`. A missing choice whose alternatives change externally
observable semantics is `unresolved_semantic`, not a default; an implementation
choice intentionally left open for optimization is a `design_variable`, with
any default recorded only as its seed value and source.

This separation lets a non-expert describe the required function without first
choosing pipeline depth, resource sharing, memory binding, arithmetic structure,
or other architecture decisions. The LLM is expected to discover such
implementation freedoms and propose them as search variables. It must not
silently turn an optimization opportunity into a user requirement or change
precision, ordering, loss behavior, protocol, or another externally observable
semantic without an accepted branch.

There is no implementation-independent single best design. If the user supplies
a priority such as a minimum frequency followed by minimum resource use, the
harness records the first term as a hard constraint and the second as an
objective. If no preference resolves the tradeoff, the harness preserves a
multi-objective Pareto set instead of inventing a hidden weighted score.

The frozen input to search is therefore the accepted observable intent plus
provenance-bearing engineering defaults and LLM-discovered architecture
freedoms. Unresolved semantic branches remain distinct requirement/profile
blocks. They cannot be mixed as functionally equivalent Design Points in one
search population.

### DSC qualification and deterministic validation

The DSC must be an executable control artifact rather than a prose description.
Its minimum schema contains: versioned references and hashes for the accepted
Requirement Envelope, seed FPP, and selected target profile; accepted hard
obligations and environment facts with provenance references; typed design variables with finite domains,
defaults, and declared affected obligations; cross-variable constraints; an
edit policy for allowed and protected paths, interfaces, clocks, resets, and
artifacts; and coverage rules mapping affected obligations to versioned public
checkers. The LLM may propose variables and architectural decisions, but it
cannot authoritatively assert requirement facts or approve its own DSC.

The deterministic validator is a staged compiler for that artifact:

1. **Schema and canonicalization:** check required fields, types, unique IDs,
   references, defaults, and domain structure; emit canonical JSON and a stable
   DSC hash.
2. **Domain validation:** require every Design Point to assign exactly the
   declared variables, preserve the block's accepted obligations and selected
   environment, and choose values inside the frozen domains.
3. **Constraint closure:** evaluate only a small auditable expression set such
   as equality, membership, Boolean implication, ordered comparison, and
   divisibility. For the intended finite spaces, enumerate combinations to
   prove that the legal space is non-empty, the default point is legal, and no
   declared value is unreachable; report raw and legal cardinality.
4. **Seed and capability binding:** verify top-level interface, clock/reset,
   target, seed hashes, evaluator-derived facts, and the availability and
   versions of required public checkers and tool routes.
5. **Patch-boundary validation:** after LLM mutation, verify that the concrete
   patch touches only allowed files and symbols, preserves protected artifacts
   and interfaces, introduces no forbidden clock domain, and matches the sealed
   parent, patch, Project Contract, and child FPP lineage hashes.
6. **Evaluation-plan compilation:** compute the conservative affected-obligation
   set and emit the required staged public checks. Cheap schema, domain,
   constraint, and edit-surface checks run before simulation or expensive EDA;
   functional validity must pass before real-tool QoR is eligible for selection.

Coverage rules give the DSC direct engineering effect. For example, a pipeline
change affects latency, timing, and ordering and therefore maps to the frozen
latency monitor, sequence oracle, and timing flow; an arithmetic or datapath
change maps to the functional oracle before resource and timing extraction. A
missing checker does not block candidate generation: it sets the corresponding
verification or implementation state to `not_assessable`. A confirmatory search
block whose predeclared fitness evidence is unavailable is ineligible for
official execution until that evidence route is qualified.

The validator emits replayable `dsc_qualification` and per-candidate
`dp_validation` records containing hashes, cardinality, failed rule IDs,
required checker IDs and versions, the staged execution plan, and the decisive
status. These records drive mutation admissibility, early rejection, validation
scheduling, cost accounting, and identical replay across search conditions.

Deterministic validation does not judge whether an architecture is good, prove
that folding or sharing preserves behavior, predict QoR, or anticipate hidden
success. Those claims remain the responsibility of independent public
simulation/formal/tool evidence and the final one-shot hidden evaluation. A
`DSC-valid` result means well-formed, bounded, and evaluable, not functionally
correct by construction. Open-world tasks without adequate oracle coverage may
still produce candidate projects, but their affected verification claims remain
`not_assessable` rather than self-certified by the proposing LLM. UVM-style
drivers, monitors, predictors, scoreboards, assertions, and scenarios operate on
the realized candidate RTL; they do not validate the DSC itself.

### Frozen obligations, observations, and design variables

Immutability is determined by acceptance and provenance, not by mere presence in
the user's initial description, seed project, target profile, or a tool report.
The DSC keeps the following quantity classes distinct:

- accepted obligations: `explicit_hard`, justified `derived_hard`, and any
  `proposed_default` accepted for this requirement/profile block;
- selected environment facts: the clocking environment, target, tool, and
  integration assumptions chosen for this block;
- seed observations: the current FPP structure and measured baseline properties,
  which establish the starting point but may be changed by admitted architecture
  decisions;
- design variables: finite architecture or realization freedoms available to
  search;
- derived quantities: deterministic functions of accepted obligations,
  environment facts, observations, and design variables;
- observed outcomes: verification status and measured frequency, latency,
  initiation interval, throughput, power, and resource use returned by public
  tools;
- unresolved or provisional choices: facts that remain outside a frozen search
  block until accepted or separated into explicit assumption branches.

Seed observations and measured outcomes are evidence, not user requirements.
They cannot be rewritten as facts by the LLM, but architecture search may improve
or otherwise change them. The available platform/profile is fixed to make QoR
comparisons meaningful within one block. Changing that inventory or physical
facts creates a separate block; changing active-device selection or placement
within the same declared inventory is an architecture Design Point under DSC.

Each design variable must identify one interpretable hardware decision and
declare a stable ID, architecture/realization/backend layer, finite typed domain,
default, physical meaning and unit, applicability condition, affected
obligations, mutation topology, permitted realization surface, and required
checker coverage. Composite labels that hide several decisions are prohibited;
for example, parallelism, folding, storage binding, multiplier binding, and
pipeline depth remain separate variables with explicit compatibility
constraints. Every declared value must occur in at least one legal Design Point,
and every variable change must be capable of producing an observable phenotype
or evaluation difference. Backend tool strategies remain frozen in the primary
architecture comparison unless separately predeclared, so tool tuning cannot be
misattributed to architecture search.

External interface width, signedness, rounding, overflow behavior, output
precision, protocol, and latency become fixed only when they are explicit,
necessarily derived, or accepted as the common observable contract for a search
block. If the user has no preference, the harness may propose alternatives. An
alternative that preserves a common observable semantics through a frozen
adapter may be a design variable; otherwise it forms a separate assumption or
profile block and is not compared as the same Design Point population. Pipeline
depth, resource mapping, internal buffering, storage organization, and internal
product, accumulator, state, or memory widths remain design freedoms unless an
accepted obligation constrains them.

Internal numeric choices may enter the design space only within a
deterministically established numeric-safety or error-tolerance envelope. For an
exact design, range analysis derives the minimum safe width from the accepted
input and coefficient bounds, accumulation depth, signedness, and overflow
semantics; search may use only values at or above that bound. Prefer relative
variables such as `accumulator_guard_bits` or `product_lsb_drop` over raw
task-specific widths, while retaining the derived absolute width in the
candidate record.

Truncation, reduced fractional precision, alternative rounding, saturation, or
other approximate arithmetic is admissible only when the frozen
requirement explicitly permits approximation and predeclares its error metric
and acceptance threshold. Width changes require signedness and propagation
checks, static range/overflow analysis, corner-case assertions, bit-exact
differential testing or the predeclared numerical-error oracle, and real-tool
QoR evaluation. An EA candidate cannot obtain a better area or timing score by
silently weakening numeric correctness; a precision violation fails feasibility
before Pareto ranking.

### Functional roles and evolving realization architecture

A Functional Role is a stable semantic obligation, not an RTL module or module
instance. Roles are derived from atomic accepted obligations and
describe what the project must do at its boundary and internally: accept and
deliver transactions, compute results, own and update state, store data, move or
buffer data, schedule work, propagate backpressure, and implement clock/reset or
CDC obligations where applicable. A role records a stable `role_id`, a human
`display_name`, requirement and fact references, typed input/output semantics,
state and reset behavior, numeric semantics, rate and timing obligations,
protocol guarantees, and required checker coverage. A role without requirement,
algorithm, or necessary engineering provenance is invalid.

The frozen Functional Role Ledger and typed Role Graph are distinct from the
evolving realization graph. The Role Graph records semantic data, control, and
state dependencies. Each Design Point supplies a many-to-many
`role_realization_map`: one role may be partitioned or replicated across several
realization nodes, and one fused node may implement several roles. Realization
nodes carry candidate-local IDs and RTL paths; role IDs do not change when
modules are renamed, split, fused, shared, replicated, pipelined, buffered, or
remapped to storage. Architecture search changes this realization mapping and
its concrete RTL patch while preserving the required role set.

Role qualification requires six closure checks. Every externally observable
requirement obligation must map to at least one role; every role must trace to a
requirement, algorithm definition, or necessary engineering obligation; every
role input and required output must have a closed typed data path; every state
object must have explicit read, write, reset, stall, and ownership semantics;
handshake, ordering, backpressure, transaction-boundary, reset, and CDC duties
must be assigned; and every required role or necessary role composition must
have an executable public verification path. A role class that is genuinely
absent is recorded as `not_applicable` with a reason rather than silently
omitted. A missing obligation is a DSC qualification failure. A missing checker
is recorded on the affected verification or implementation axis and prevents
only the corresponding evidence claim or confirmatory fitness use.

The minimum frozen artifacts per requirement/profile block are a
`functional_role_ledger`, a `functional_role_graph`, and the requirement-to-role
coverage record. Each candidate adds its own `role_realization_map`. Removing a
required role, adding an externally observable function, or changing role-level
numeric, protocol, ordering, reset, or timing obligations is not an architecture
mutation; it requires an explicit Requirement Envelope and DSC amendment and a
new search block.

### Functional assurance for architecture changes

The method does not guarantee that an LLM-authored structural change is correct
by construction. It guarantees that an unverified change cannot receive
feasible QoR credit, enter the feasible population, or become a terminal
candidate. Functional acceptance is defined at the transaction level: output
values and order, no loss or duplication, reset and state behavior, numeric and
overflow semantics, ready/valid and backpressure behavior, and latency,
initiation interval, and throughput within the frozen envelope. Cycle-exact
equivalence is required only when latency is frozen; legal pipeline changes use
value-, order-, protocol-, and bounded-timing equivalence.

An independent mathematical or algorithmic reference model is the preferred
functional authority. A qualified seed FPP may additionally serve as a
differential reference but cannot be the sole oracle when that would preserve a
seed defect. Candidate validation proceeds from cheap to expensive:

1. static structural, interface, width, driver, connectivity, combinational-loop,
   clock/reset, CDC, protected-surface, and lineage checks;
2. local assume-guarantee checks for changed roles and the composition that must
   refine the original role contract;
3. end-to-end transaction-aware differential simulation over fixed boundary,
   reset, stall, sustained-throughput, overflow-near, and randomized cases;
4. applicable combinational, bit-vector, sequential, latency-aware refinement,
   ordering, no-loss/no-duplication, schedule, or range proofs;
5. frozen assertion, constrained-random, metamorphic, and coverage obligations;
6. real-tool QoR only after public functional feasibility, followed at search
   completion by D23/D24 terminal validation of the sealed public Pareto set.

Each candidate records its achieved assurance tier, for example a qualified
certified transformation, a formally equivalent patch, or a public
simulation-validated open patch. The guarantee comes from the named checker or
proof artifact, not from the LLM rationale. Unavailable proof remains explicit;
passing a bounded public suite supports only scoped public conformance, not
universal functional correctness.

Architecture mutation and repair retain distinct semantics. Mutation starts
from a public-feasible parent to explore an implementation tradeoff. Bounded
repair starts from an eligible public-failing child and attempts only to restore
the frozen obligations. The failed child and all cost remain in the denominator,
and a repaired child receives a new identity and must repeat the complete
required public validation before entering the population.

### DSC adequacy authority and evaluation

No single actor certifies that an LLM-proposed DSC contains every useful
architecture. The user owns intent and preference decisions; deterministic
validation establishes structural soundness; a presealed independent expert
reference supplies bounded opportunity coverage; open-set adjudication handles
valid proposals outside that reference; and candidate verification plus real
EDA measurements establish downstream utility.

For each benchmark block \(b\), at least two hardware experts independently
author an architecture opportunity set \(\mathcal{O}^{ref}_b\) before any LLM
DSC is observed. Each opportunity records its architecture axis, applicability,
choices, affected obligations, expected tradeoff, technical basis, and
`essential`, `useful`, or `optional` importance. The resulting reference and
adjudication procedure are sealed before DSC generation and remain unavailable
to the LLM. They are a bounded reference, not a complete architecture truth.

After the LLM output \(\mathcal{O}^{LLM}_b\) is frozen, blinded raters map it to
the reference set. Weighted opportunity recall is

\[
Recall_b=
\frac{\sum_{o\in\mathcal{O}^{ref}_b}w_o
\mathbf{1}[o\text{ is covered}]}
{\sum_{o\in\mathcal{O}^{ref}_b}w_o},
\]

where \(w_o\) is the predeclared importance weight. Proposal validity is

\[
Precision_b=
\frac{N_{\mathrm{valid\ LLM\ opportunities}}}
{|\mathcal{O}^{LLM}_b|}.
\]

An LLM proposal absent from \(\mathcal{O}^{ref}_b\) is not automatically an
error. A separate post-freeze review classifies it as a valid novel opportunity,
invalid proposal, duplicate/rephrasing, or not assessable. Its bounded yield is

\[
NovelYield_b=
\frac{N_{\mathrm{valid\ novel\ opportunities}}}
{|\mathcal{O}^{LLM}_b|}.
\]

Independent agreement is reported with a predeclared categorical agreement
statistic and disagreements are adjudicated by a third reviewer. Agreement
quantifies reference reliability; it does not convert expert judgment into an
absolute completeness proof.

Downstream evaluation holds the model, seed FPP, search policy, public
evaluator, candidate/tool budgets, and terminal selector fixed while changing
only the search-space source:

| ID | Search space | Evidence role |
| --- | --- | --- |
| `SPACE-LLM` | Frozen LLM-proposed DSC | Tested harness component |
| `SPACE-EXPERT` | Frozen expert reference DSC | Human-information ceiling/reference, not a fair automation competitor |
| `SPACE-GENERIC` | Frozen generic implementation knobs | Weak space-construction baseline |
| `SPACE-ABLATE` | LLM DSC with one predeclared information class removed | Mechanism ablation |

The comparison reports feasibility density, unique phenotype ratio, first
feasible evaluation, architecture diversity, anytime/terminal Pareto quality,
improvement beyond the seed, and total LLM/simulation/EDA cost. Search policy
and search space cannot change together in a comparison intended to attribute a
space effect; random selection within each space is also reported. This follows
the evaluation warning that downstream winners alone conflate search policy and
search-space advantages [yu-nas-search-evaluation-2020;
yang-nas-evaluation-2020].

The expert reference is opened only after the LLM DSC hash is sealed. Its
omissions cannot be repaired before the official comparison, and search outcomes
cannot be used to revise either space. A positive result supports high bounded
reference recall, valid additional opportunities, and useful downstream search
on the evaluated blocks. It does not support a claim that the DSC is complete or
contains the globally optimal hardware architecture.

### Mathematical foundation of the DSC and search

The minimum theory stack is contract-based design, finite-domain constraint
satisfaction, feasibility-first multi-objective evolution, and a
counterexample-guided bounded repair loop. These formulas define artifacts and
decision rules; they do not substitute for RTL verification or real-tool
measurement.

Let the accepted observable contract be

\[
\mathcal{C}=(A,G),
\]

where \(A\) is the set of admissible environment assumptions and \(G\) is the
set of externally observable guarantees. A realized candidate \(x\) is eligible
for contract credit only under the implication \(A\Rightarrow G(x)\). In the
current harness this relation is checked by bounded public and hidden evidence;
it is not a formal proof unless a separately declared formal engine establishes
it. This assumption--guarantee framing follows contract-based embedded-system
design [benveniste-contracts-2007; cimatti-tonetta-contract-refinement-2015].

For typed design variables \(\mathbf{z}=(z_1,\ldots,z_n)\), with each
\(z_i\in D_i\), the raw product space and the legal DSC space are

\[
\mathcal{Z}_{\mathrm{raw}}=\prod_{i=1}^{n}D_i,
\qquad
\mathcal{Z}_{\mathrm{DSC}}
=\left\{\mathbf{z}\in\mathcal{Z}_{\mathrm{raw}}:
\bigwedge_{j=1}^{m}C_j(\mathbf{z})\right\}.
\]

The deterministic DSC validator evaluates the finite-domain predicates
\(C_j\), proves that \(\mathcal{Z}_{\mathrm{DSC}}\) is non-empty, confirms that
the seed point is legal, and reports raw and legal cardinality. This establishes
constraint consistency, not architectural completeness or RTL correctness.

Given parent FPP \(x_t\), legal decision \(\mathbf{z}\), and permitted public
history \(h_t\), the LLM mutation operation emits one sealed child:

\[
x_{t+1}=M_{\theta}(x_t,\mathbf{z},h_t),
\]

where \(M_{\theta}\) returns the semantic decision, concrete RTL patch, and
lineage-bound artifact hashes together. There is no second stochastic
realization call for the same Design Point.

Public feasibility is a hard conjunction:

\[
\Phi(x)=
\phi_{\mathrm{req}}(x)\land
\phi_{\mathrm{build}}(x)\land
\phi_{\mathrm{func}}(x)\land
\phi_{\mathrm{protocol}}(x)\land
\phi_{\mathrm{physical}}(x).
\]

Only candidates with \(\Phi(x)=1\) enter QoR selection. A feasible candidate
always outranks an infeasible candidate; functional or protocol failure cannot
be traded against PPA through a soft penalty. Among feasible candidates, the
task/profile block freezes a compact objective vector \(\mathbf{f}(x)\), chosen
from measured latency, initiation interval, throughput, frequency, power, and
resource axes. Candidate \(x\) Pareto-dominates \(y\) when

\[
x\prec y
\iff
\left[\forall k,\ f_k(x)\leq f_k(y)\right]
\land
\left[\exists k,\ f_k(x)<f_k(y)\right].
\]

The minimum EA uses constrained nondominated sorting, elitism, and a diversity
rule; NSGA-II is the reference algorithmic basis rather than a novelty claim
[deb-nsga2-2002]. When the user has not supplied a preference that selects one
tradeoff, the harness returns the nondominated set instead of inventing a hidden
weighted sum.

For an archive \(\mathcal{P}_t\) after public evaluation step \(t\) and a
pre-outcome reference point \(r\), anytime search quality may be summarized as

\[
HV_t=HV(\mathcal{P}_t;r).
\]

The reference point, objective directions, normalization, failed-candidate
treatment, and aggregation unit must be frozen before outcome-producing runs.
Hypervolume changes the effective preference over solution sets and is not a
neutral plotting choice [auger-hypervolume-2012].

DSC adequacy diagnostics include

\[
\rho_{\mathrm{legal}}
=\frac{|\mathcal{Z}_{\mathrm{DSC}}|}{|\mathcal{Z}_{\mathrm{raw}}|},
\qquad
\rho_{\mathrm{realize}}
=\frac{N_{\mathrm{assembled}}}{N_{\mathrm{attempted}}},
\]

\[
\rho_{\mathrm{feasible}}
=\frac{N_{\Phi(x)=1}}{N_{\mathrm{attempted}}},
\qquad
\rho_{\mathrm{unique}}
=\frac{|\{\operatorname{hash}(FPP(x))\}|}{N_{\mathrm{assembled}}}.
\]

These quantities expose over-constrained spaces, failed realization, low valid
search density, and genotype-to-phenotype collapse. They do not show that the
DSC contains every useful architecture.

Bounded repair is counterexample-guided. For public counterexample or diagnostic
\(c_t\),

\[
x_{t+1}=R_{\theta}(x_t,c_t),
\]

and the repaired child must be re-evaluated from the beginning. Because the
current verifier is generally bounded rather than complete, this is described as
a CEGIS-inspired repair loop, not formal CEGIS [jha-seshia-ogis-2017].

Hardware-specific theories are optional DSC plug-ins. For synchronous dataflow
regions, actor repetition counts \(q_u,q_v\) and edge production/consumption
rates \(p_e,c_e\) may be required to satisfy

\[
q_u p_e=q_v c_e,
\]

which checks static rate balance before realization
[lee-messerschmitt-sdf-1987]. For compute/memory-bound accelerators, an FPGA
Roofline-style upper bound

\[
P(x)\leq\min\left(P_{\mathrm{compute}}(x),\ BW(x)\,AI(x)\right)
\]

may guide which variables expose parallelism, locality, or bandwidth, but it is
only used where operations, traffic, and bandwidth are meaningfully defined
[nabi-vanderbauwhede-roofline-2019]. MAP-Elites remains an optional future
diversity mechanism if Pareto evolution demonstrably collapses to one
architecture family; it is not part of the minimum method
[mouret-clune-map-elites-2015].

### Design Point

A Design Point seals the semantic decision, the concrete RTL patch emitted for
that decision, its parent identifier, public-feedback provenance, and the hashes
of the resulting Project Contract and FPGA Project Package. It is not claimed as
a new general-purpose hardware IR. The LLM emits the decision and patch together
once as the evolutionary variation operation; a second stochastic realization
call is prohibited. Registered deterministic transformations may be used as
reliable general-purpose fast paths, but the method does not require a complete
family-specific RTL template library.

### Project Contract and FPGA Project Package

The Project Contract records the obligations retained or changed by one Design
Point. Its current implementation serialization is System-HIS v1.2.
Deterministic project assembly applies the sealed patch and fixes declared
interfaces, protected sources, constraints, build metadata, edit boundaries, and
lineage. It does not generate the architecture through a family template.
Model-authored RTL remains subject to functional verification; a valid Project
Contract, patch application, or project skeleton is not a correctness proof.

## Search and evaluation flow

```text
accepted requirement and available platform inventory
  -> Track G: generation / public verification / bounded repair
  -> common usable seed (public evidence, no early hidden qualification)
  -> freeze DSC and complete comparison protocol
  -> Track O: public-only LLM+EA or qualified comparator search
       -> decision + concrete patch -> protected deterministic assembly
       -> public checks -> bounded eligible repair or recorded failure
       -> feasible child -> required public QoR -> selection/archive
  -> seal public Pareto set, seed reference and any single-project selector
  -> per-candidate terminal validation with sealed stimuli
  -> D24 NHV of passing archive subset + public/terminal divergence
  -> qualified seed increment and preselected-project PPA
```

No terminal results affect search, archive membership, repair or replacement.
Register all terminal object identities before opening any outcomes. Seed-reference
and missingness details are draft judgments, not implemented features. Canonical
v1.8 remains unchanged.

### Evolution and bounded repair

The EA operates over a population of sealed FPGA Project Packages. Public
feasibility and real-tool QoR determine Pareto ranking, diversity retention,
parent selection, and survivor selection. Selected parents are inherited by
their children, and the LLM acts as the semantic mutation operator by emitting
one bounded RTL patch from the parent, frozen DSC, and permitted public feedback.
Mutation-only evolution is the minimum design; RTL crossover is not required.

Architecture mutation and repair have separate roles. Mutation starts from a
public-feasible parent and explores an architectural or implementation tradeoff.
Repair starts only from an eligible public-failing child and attempts to restore
the frozen functional, interface, protocol, or tool-validity obligations. Repair
cannot change the DSC, hard requirements, target, protected files, or hidden
authority. Each repair creates a new child record rather than overwriting its
failed parent, is capped by a predeclared call/tool budget shared across fair
conditions, and must pass the complete public evaluation before entering the
feasible population. The unrepaired failure and all attempted cost remain in the
assigned denominator.

## Research questions

### RQ1 — Contract-valid search density

Does the Design-Space Contract plus deterministic decoding reduce invalid,
unlowerable, unscorable, and requirement-inconsistent candidates relative to
equal-budget direct Project Contract/RTL phenotype evolution?

This tests the representation/materialization bundle. It does not isolate
typing alone and cannot use functional correctness as a by-construction claim.

### RQ2 — Evolutionary search effectiveness

Within the identical frozen design space and public evaluation budget, does
domain-aware LLM variation improve feasible Pareto discovery and anytime search
quality over random/covering sampling, conventional evolutionary variation, and
an appropriate black-box optimization baseline?

### RQ3 — Public-to-hidden validity

Do members of the sealed public Pareto archive retain terminal conformance,
and how does terminal attrition change archive quality by search condition?

### RQ4 — FPGA physical quality and cost

For the signed tool/device/family scope, what L3/L4 attrition, timing, latency,
initiation interval, throughput, LUT/FF/BRAM/DSP use, Pareto quality, and total
search cost are observed? Conditional survivor QoR cannot replace the original
assigned denominator.

## Minimum comparison matrix — atomic design draft

Identifiers below are analyst-selected candidate-document labels, not runtime
methods. Qualification is frozen before outcomes; unsupported methods are out of
scope, not relabeled after seeing their performance.

| ID | Representation and policy | Role / qualification boundary |
| --- | --- | --- |
| SEED | Common usable FPP, no optimization | Reference; no early hidden-qualified starting point |
| D-RND | Uniform legal DSC assignment sampling | Primary internal policy comparator; sampler and realization route must be qualified |
| D-COV | Predeclared coverage-driven legal assignment schedule | Separate nonadaptive policy; no outcome-directed coverage changes |
| D-EA | Conventional EA with registered non-LLM variation | Mechanism comparator only on common realizable domain |
| D-LLM-EA | Population/selection plus joint LLM decision-and-patch variation | Proposed method with bounded public repair |
| D-LLM-LOCAL | One incumbent with LLM local variation | Population-value comparator with matched variation/repair |
| D-MAP-ONLY | Fixed compute architecture; legal mapping and required link wrappers vary | Multi-FPGA design-freedom control, not same-DSC policy contrast |
| D-SA | Simulated annealing on a legal assignment neighborhood | Secondary; neighborhood/acceptance rule TBD |
| D-BO | One registered mixed-domain Bayesian optimizer | Secondary; concrete optimizer and domain support must qualify |
| P-PC | LLM Project Contract variation without generated DSC | Bundle comparator; concrete PC-to-RTL realization required |
| P-RTL | Direct LLM RTL variation without generated DSC | Separate bundle under common requirement/protected shell |
| X-ENUM | Finite assignment enumeration with deterministic realization | Small-space reference, not an oracle for open RTL implementations |

Sharing a DSC does not establish realization fairness. D-RND/D-COV/D-SA/D-BO
need an assignment-to-RTL route. If an LLM realizes sampled assignments, use
matched policies among those controls and charge all calls. D-LLM-EA still emits
decision and patch jointly once; do not add a second stochastic realization.
If the joint operator and controls differ in realization policy, call the
comparison a search/realization bundle, not a pure selection effect.

A D-EA transform library covering only a subset cannot claim full-domain
fairness. Qualify common expressiveness before comparison or report a separately
labeled common subset. P-PC must produce a concrete evaluated FPP; schema edits
alone earn no credit. Adapters cannot add free repair, privileged DSC knowledge,
or extra budget. Archive extraction records native evaluated outputs without
changing the native search; missing candidate records permit only a qualified
single-terminal comparison, not an invented archive result. External baseline
roles follow protocol section 10. No row declares a runnable implementation.

## Claim-linked ablations — design draft

| Contrast | Held fixed | Interpretation |
| --- | --- | --- |
| D-LLM-EA vs D-RND | Qualified DSC, seed, evaluator, model privileges, budget, terminal rules | Proposed primary search/realization-policy contrast |
| D-EA vs D-RND | Common realizable domain and realization route | Conventional adaptive selection value |
| D-LLM-EA vs D-EA | Qualified common domain and controls | LLM variation increment only with matched realization privileges |
| D-LLM-EA vs D-LLM-LOCAL | Variation interface, public feedback, repair, budget | Population/selection bundle value |
| D-LLM-EA vs D-MAP-ONLY | Seed, available inventory/link, top-level semantics, evaluator, accounting | Joint architecture freedom beyond fixed-compute mapping |
| SPACE-LLM vs SPACE-EXPERT/GENERIC/ABLATE | Same qualified fixed search/realization policy and seed | Space-source utility; expert is an information reference |
| D-LLM-EA vs P-PC; vs P-RTL | Requirements, platform, evaluator, model, accounted resources | Two distinct representation/materialization bundles |

Hidden-feedback leakage is prohibited, not a fair ablation. Changing accepted
obligations changes the task. Factorial interactions require a declared design.
These labels do not rename A/B/A-R/B-R in the separate PC study or runtime M0-M5.

## Operational endpoint freeze still required

The consolidated protocol supplies set definitions, D24 filtering, draft
normalization, missingness, pairing/aggregation and budget/cost design. It replaces
the unspecified binary-gate-plus-public-Pareto/anytime proposal. Actual objective
signatures/anchors, operational budgets, qualified comparisons, uncertainty/test
implementation, minimum effects, multiplicity, power and signed scope remain
unfrozen. EXPT-PROTOCOL-001 is not operationally closed; execution is unauthorized.

## Infeasibility and requirement-failure semantics

Search must not silently trade away a frozen requirement to report a more
resource-efficient design. A candidate is `requirement-inconsistent` when it
violates a declared functional, interface, protocol, precision, latency,
initiation-interval, throughput, resource, clock, or ordering obligation, even
if it is schema-valid, lowerable, or synthesizable.

When every candidate has the required assessable evidence and none satisfies all
hard requirements, the outcome is `no_feasible_design` rather than a best-effort
success. When required evidence is unavailable, no feasibility conclusion is
drawn; the affected verification or implementation axis is `not_assessable`.
The record must retain every attempted candidate, failure, and cost. Distinguish:

- `design_space_exhausted`: all permitted candidates were evaluated without a feasible point;
- `requirement_conflict`: frozen hard obligations are jointly incompatible;
- `physical_infeasibility`: valid candidate projects cannot meet the named device/resource/timing constraints;
- `infrastructure_unavailable`: tool or environment failure prevents a design conclusion.

Only an explicit, versioned requirement amendment may change a hard requirement,
the target device, permitted transformations, or the design-space contract and
begin a new search. Such an amendment must not relabel previous infeasible
candidates as successful.

## Resource status

No run count, wall time, API cost, or storage estimate is currently defensible.
Current-status separates representative-family OpenXC7 L4 records from later
excluded development checks. Neither supplies a qualified batch-search runtime
or repeatability distribution; counts must retain their source scope. Resource planning therefore requires a separate
excluded tool-repeatability and throughput pilot. Any estimate before that pilot
is `not_assessable`, not zero.

## Implementation and execution hold

No execution script is supplied because the design-space schema, endpoint,
fitness, selector, and tool-repeatability evidence are not frozen and the user
has not authorized implementation or outcome-producing runs. The next legal
step is an affected-scope design review, followed by a read-only batch-QoR route
audit. Only a later explicit implementation authorization may open EA-G3 work.

## Acceptance criteria for propagation into the canonical specification

- every research question has one scientific job and a named evidence role;
- every fair comparison has matched information and budgets;
- the primary endpoint and aggregation path are fully defined;
- Project Contract/H-stage claims are limited to implemented validators;
- public search and hidden final authority are mechanically separated;
- the QoR tool path has repeatability and failure-semantics evidence;
- the target-venue comparison and literature matrix support only combination-level novelty;
- no result, runtime, scalability, superiority, or correctness claim is filled without evidence.
