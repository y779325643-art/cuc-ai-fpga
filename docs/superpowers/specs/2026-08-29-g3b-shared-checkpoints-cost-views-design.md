# G3b Shared Checkpoints And Three-View Cost Design

## 0. Status And Authority

- **Design ID:** `sr2fpga-paper1-g3b-shared-checkpoints-cost-views-v1`
- **Date:** 2026-08-29
- **Research authority:**
  [`paper1-freeze-v1.7`](../../specs/2026-08-14-sr2fpga-paper1-research-program-design.md)
- **Implementation authority:**
  [`sr2fpga-paper1-code-dev-v1.11`](../../specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md)
- **Scope:** excluded development conformance for one complete M0-M5 replicate
  block and its negative preparation fixtures
- **Out of scope:** paid or real-provider runs, G5, official evaluation, dataset
  promotion, training, G3 acceptance, and G4b authorization

`G3b` is a local implementation-slice name, not a research gate introduced by
the Paper-1 freeze. Completing this design may justify the bounded statement
"G3b development conformance implemented". It cannot justify "G3 accepted",
an empirical method result, provider-seed eligibility, official VPP, or any
Paper-1 claim.

All artifacts introduced by this design fix the following fields to `false`:

- `official_outcome`
- `official_authority`
- `pass_credit_authority`
- `rq1_evidence`
- `rq2_evidence`
- `g3_accepted`
- `g4b_authorized`

## 1. Problem Statement

The Paper-1 freeze defines three sharing relations within one replicate block:

1. M0 and M1 consume one immutable Direct initial project.
2. M3 and M4 consume one immutable generated System-HIS.
3. M4 and M5 consume one immutable complete skeleton-derived initial project.

The current Runner implements the first two relations lazily. The first method
encountered in randomized execution triggers the shared model call inside its
active `AttemptCostLedger`; later methods reuse the artifact. This makes
per-method cost depend on execution order and violates the requirement that a
shared call cannot be charged only to the first method. The current Runner does
not implement the third relation: M4 and M5 independently perform behavior-fill
generation. Equality of their trusted deterministic skeletons is not equality
of the complete initial projects required by the freeze.

The existing `attempt-event-v1` and `cost-summary-v1` contracts are method- and
episode-scoped. They cannot represent a method-neutral block-preparation call
without falsely assigning it to M0-M5. Their aggregate summaries also cannot
reconstruct checkpoint-specific incremental views.

G3b therefore moves shared generation before randomized method execution,
records its physical cost in a separate block ledger, freezes a named checkpoint
DAG, and derives three cost views from verified raw events.

## 2. Goals And Non-Goals

### 2.1 Goals

- Materialize all three shared prerequisites before the first M0-M5 method runs.
- Store Direct and skeleton-derived projects under distinct checkpoint keys.
- Make M4 and M5 consume the same complete, behavior-filled initial project.
- Record block-preparation model calls without a `method_condition` owner.
- Preserve every one of the existing 13 cost axes as measured or unavailable.
- Derive actual block consumption, six standalone-attributed costs, and three
  checkpoint-specific incremental contrasts from verified raw sources.
- Preserve failure cost, dependency-specific blocking, resume idempotence,
  order invariance, and model-visibility boundaries.
- Keep existing partial and legacy Runner paths readable and operational without
  granting them G3b authority.

### 2.2 Non-Goals

- No positive `g3-acceptance-v1` reducer.
- No repair-policy probe or `repair_probe_block_id` path.
- No complete M5 H0-H3 correction or outer-repair scenario matrix.
- No public/hidden two-axis missingness completion.
- No provider capability-to-call binding or real-provider eligibility proof.
- No changes to official method outcomes, campaign authorization, or claims.
- No rewrite of historical paired blocks, episode packs, trajectories, full-pack
  v1/v2 artifacts, or ArtifactStore keys.

The remaining scenario and capability work belongs to G3c. The positive,
artifact-derived acceptance reducer belongs to G3d.

## 3. Canonical Terms

- **Shared checkpoint:** a named immutable artifact-graph node created during
  block preparation. It is not an attempt number, an arbitrary hash, or a
  deterministic skeleton alone.
- **Complete initial project:** the unmodified, behavior-filled project that
  enters public evaluation before any outer repair. For M4/M5 this is distinct
  from the trusted pre-behavior deterministic skeleton.
- **Actual block consumption:** physical development-block cost with every raw
  event counted at most once. The term "campaign consumption" is not used for
  excluded development fixtures.
- **Standalone-attributed cost:** the complete observed-to-stop cost attributed
  to one method as if it bore all prerequisites it requires. It is not a physical
  invoice and shared cost is not divided among consumers.
- **Incremental cost:** two non-negative arm costs measured after one named
  checkpoint, plus an optional signed delta. It is not a generic per-method
  field or the difference of two standalone totals.
- **Method-exclusive event:** a raw event produced after block preparation by
  one method's own attempt ledger. Shared producer events are never exclusive.

## 4. Checkpoint Graph And Method Ownership

The checkpoint graph contains exactly three nodes:

```text
S_D: direct_initial_project
  consumers: M0, M1

S_H: shared_system_his
  consumers: M3, M4, M5 and downstream S_P
        |
        v
S_P: skeleton_initial_project
  consumers: M4, M5
```

`S_P` is generated from `S_H` and contains the complete behavior-filled initial
project. Its manifest node binds both the complete project artifact and the
trusted deterministic-skeleton artifact used to constrain behavior fill.

Method prerequisites are frozen as:

| Method | Shared prerequisites | Method-exclusive generation/repair |
| --- | --- | --- |
| M0 | `S_D` | none before evaluation |
| M1 | `S_D` | bounded public-diagnosis project repair |
| M2 | none | untyped plan and free project generation |
| M3 | `S_H` | free project generation from HIS |
| M4 | `S_H`, `S_P` | none before evaluation |
| M5 | `S_H`, `S_P` | bounded HIS correction or project repair |

M5 receives no M4 public or hidden result. It receives only the same frozen
initial artifacts and its own method-permitted public diagnosis. Any M5-specific
correction or repair occurs after `S_P` and belongs to M5-exclusive cost.

## 5. Three Cost Views

Let the 13 cost axes be indexed by `k`. Let `S_D`, `S_H`, and `S_P` denote the
exclusive costs of producing their corresponding checkpoints. Let `U_m` denote
all verified method-exclusive costs for method `m` after block preparation.

### 5.1 Actual Block Consumption

For one replicate block `b`:

```text
C_actual[b,k] = Agg_k(S_D union S_H union S_P union U_0 ... union U_5)
```

- Every raw event ID appears at most once in the actual source partition.
- Shared generation is counted once, irrespective of consumer count.
- `shared_artifact_consumed` is lineage-only and carries measured zero cost.
- Accounting-close events summarize preceding events and are not added again.
- For the current serial Runner, disjoint phase wall times are additive. The
  reducer retains interval boundaries so a future parallel implementation can
  use interval union/makespan without changing count-axis semantics.

### 5.2 Standalone-Attributed End-To-End Cost

```text
M0 = S_D + U_0
M1 = S_D + U_1
M2 =       U_2
M3 = S_H + U_3
M4 = S_H + S_P + U_4
M5 = S_H + S_P + U_5
```

Shared cost intentionally appears in multiple standalone rows. The sum of all
standalone rows therefore does not equal actual physical consumption.

### 5.3 Checkpoint-Specific Incremental Contrasts

| Contrast | Checkpoint | Treatment arm | Baseline arm |
| --- | --- | --- | --- |
| `M1-M0` | `S_D` | `U_1` | `U_0` |
| `M4-M3` | `S_H` | `S_P + U_4` | `U_3` |
| `M5-M4` | `S_P` | `U_5` | `U_4` |

Each record stores both non-negative arm totals. For an axis measured in both
arms, `signed_delta = treatment - baseline` may be negative. If either arm is
unavailable, the delta is unavailable with a derived reason. M4 deliberately has
two different post-checkpoint roles; they cannot be collapsed into one generic
incremental cost.

M3-M2, M4-M0, and descriptive M5-M1 have no common generation checkpoint and
use standalone-attributed costs. The repair-policy contrast is deferred to G3c.

## 6. Cost Axes And Aggregation

Every cost view contains exactly these axes:

1. `logical_model_calls`
2. `input_tokens`
3. `output_tokens`
4. `cached_tokens`
5. `provider_transport_attempts`
6. `planner_parser_schema_retries`
7. `outer_repair_attempts`
8. `public_tool_calls`
9. `hidden_evaluator_tool_calls`
10. `hidden_infrastructure_retries`
11. `wall_time`
12. `eda_time`
13. `hidden_evaluator_runtime`

Aggregation rules:

- An axis is measured only when every source component is measured.
- Any unavailable component makes the dependent aggregate unavailable; zero is
  never substituted for missing measurement.
- Measured zero is permitted only after a closed event set proves the axis did
  not occur.
- Count, token, EDA, and hidden-runtime axes sum unique cost deltas.
- Wall time uses disjoint outer stage intervals rather than nested event sums.
- Provider transport retries increase the transport axis but not logical calls
  unless a new logical model request is created.
- Parser/schema retry reservations remain distinct from the subsequent model
  call; the retried call records its own logical/token/transport/time costs.
- Failure and `not_run` preserve all cost incurred before termination.

## 7. Model-Call Budgets

The existing method ceiling is interpreted as a standalone ceiling. Complete
paired blocks split it into attributed shared prerequisites and an exclusive
runtime ceiling.

For a clean gold-ready block without repair:

| Scope | Physical initial calls |
| --- | ---: |
| Block preparation: `S_D + S_H + S_P` | 3 |
| M0 exclusive | 0 |
| M1 exclusive | 0 |
| M2 exclusive | 2 |
| M3 exclusive | 1 |
| M4 exclusive | 0 |
| M5 exclusive | 0 |
| **Actual physical total** | **6** |

The standalone-attributed initial calls are `1+1+2+2+2+2=10`.

- M1 exclusive ceiling is its frozen repair allowance after `S_D`.
- M5 exclusive ceiling is its single shared correction/repair allowance after
  `S_P`; HIS correction and project repair do not receive separate allowances.
- M2 and M3 retain two and one exclusive initial calls respectively.
- M0 and M4 have zero model calls before evaluation after checkpoint injection.
- The block-preparation budget is method-neutral and cannot be borrowed by any
  method. A failed preparation call is still consumed physical cost.
- Partial and legacy tasks retain their current budget implementation and cannot
  produce G3b artifacts.

## 8. Runtime Data Flow

```text
G3a pure paired-block plan
        |
        v
measurement freeze
  - paired-block ref
  - preparation policy hash
  - expected checkpoint IDs and dependency graph
        |
        v
eager block preparation
  1. create S_D
  2. create and validate S_H
  3. create S_P from S_H
  4. close block event stream
  5. write and verify checkpoint manifest
        |
        v
method phase in paired-block method_order
  - inject only method-permitted SharedArtifactRefs
  - use exclusive model budget
  - emit method-specific candidates, envelopes, seals, outcomes, trajectories
        |
        v
existing full-pack-runner-reconciliation-v2
        |
        v
development-paired-block-cost-reconciliation-v1
```

The measurement freeze is written before the first preparation model call. It
binds the preparation policy and planned checkpoint graph, not unknown runtime
artifact hashes. Runtime checkpoint refs are bound by the subsequently closed
manifest and companion reconciliation.

Preflight computes the same preparation policy and planned checkpoint keys as
runtime without calling a provider or creating a run directory.

## 9. Contract Family

### 9.1 `development-block-preparation-event-v1`

A method-neutral append-only raw event with:

- `contract_version`
- `evaluation_scope=excluded_development_conformance_only`
- `event_id`, `parent_event_id`, `sequence`
- complete `paired_block_ref`
- `checkpoint_id` in `direct_initial_project`, `shared_system_his`,
  `skeleton_initial_project`, or block-level close
- `parent_checkpoint_ids`
- `stage` in `block_direct_initial`, `block_req2his`,
  `block_skeleton_initial`, or `accounting_close`
- `event_kind` in budget reserve/exhaustion, axis cost, checkpoint materialized,
  checkpoint failed, checkpoint not-run, and accounting closed
- `status`, `started_at`, `duration_seconds`
- input/output ArtifactRefs and content hashes
- 13-axis `cost_delta` and `unavailable_axes`
- optional model-gateway provenance ref
- `failure_origin`
- fixed false authority fields

The parent chain, sequence, event ID, source set, and close totals are recomputed.
Lineage events carry measured zero cost. Close totals are reconciliation output,
not additional actual cost.

### 9.2 `development-shared-checkpoint-manifest-v1`

The manifest contains exactly the three graph nodes and records:

- paired-block ref and preparation-policy hash
- `complete` or `incomplete` manifest status
- per-node status: `completed`, `failed`, or `not_run`
- enumerated status reason
- artifact ref or null, with completed requiring a ref
- planning/project-package and trusted-skeleton digests as applicable
- exact parent IDs and consumer methods
- source preparation event refs and event-set hash
- producer stage and model provenance refs
- fixed false authority fields

Graph invariants are runtime-verified:

- `S_D` and `S_H` have no parent.
- `S_P` has exactly `S_H` as parent.
- `S_D` consumers are M0/M1.
- `S_H` supports M3/M4/M5 and the `S_P` dependency.
- `S_P` consumers are M4/M5.
- Completed nodes are read back and their content digests are recomputed.

### 9.3 `development-paired-block-cost-reconciliation-v1`

The companion references:

- paired-block ref
- checkpoint-manifest ref
- ordered raw preparation event refs
- six method records with trajectory/cost refs or explicit blocked status
- existing full-pack-runner-v2 ref for a complete success block, otherwise null
- reducer implementation/policy hash

It stores:

- actual block axes
- six standalone-attributed method records
- three incremental contrast records with two arms and signed deltas
- exact source-event partition and source-set hash
- method completion/missingness status
- recomputed reconciliation booleans
- fixed false authority fields

A positive complete G3b record requires all three checkpoints, six method
trajectories, and full-pack-v2. An incomplete preparation record remains a valid
development cost/missingness artifact but cannot satisfy G3b positive
conformance or any G3 scenario-outcome requirement.

## 10. Failure And Resume Semantics

Preparation nodes are dependency-scoped:

- If `S_D` fails, M0/M1 are `blocked_by_shared_checkpoint`; M2 and the HIS branch
  continue.
- If `S_H` fails, `S_P=not_run`; M3/M4/M5 are blocked; M0/M1/M2 continue.
- If `S_P` fails, M4/M5 are blocked; M0/M1/M2/M3 continue.

There is no fallback to method-local regeneration. Actual cost retains every
pre-failure event. Standalone-to-stop cost includes the failed prerequisite cost
for every dependent method and excludes unexecuted downstream work. Any affected
incremental contrast is unavailable with a named checkpoint reason.

For G3b, a blocked method is represented in the cost companion with null
trajectory and measured-zero exclusive cost from a closed no-start set. This is
not a registered episode outcome and does not close the G3 scenario matrix; G3c
adds the required episode-level scenario outcome authority.

Resume rules:

- A complete manifest may be reused only when paired-block, policy, graph,
  ArtifactRefs, content digests, event chain, and close totals all match.
- Reuse creates no provider call and no duplicate cost event.
- A partial, corrupt, or mismatched preparation cannot resume in place. The run
  fails closed and requires a new run ID.
- Existing legacy runs lacking G3b artifacts remain readable but cannot be
  upgraded in place or receive G3b/G3 credit.

## 11. Visibility And Trust Boundaries

The following never enter model prompts or repair feedback:

- paired block/replicate IDs
- schedule seed, method order, or execution ordinal
- checkpoint graph, refs, status, cost, or sibling method state
- block event IDs, reconciliation output, hidden commitments, or outcomes

Only method-contract-permitted shared content is provided:

- M0/M1 receive the same initial Direct project.
- M3 receives `S_H` and performs its own free project generation.
- M4/M5 receive the same `S_H` and complete `S_P` initial project.
- M1 never receives M0 evaluator results.
- M5 never receives M4 public or hidden results.

Candidate snapshots, project envelopes, terminal selection, public outcomes, and
hidden outcomes remain method- and episode-specific even when initial project
bytes are shared. Candidate repair cannot modify checkpoint manifests, raw block
events, cost reducers, trusted tests, or evaluator material.

## 12. Module And File Ownership

New focused modules:

- `agent/src/sr2fpga_agent/block_preparation.py`
  - pure preparation plan
  - dependency-aware eager executor
  - checkpoint materialization and verified read-back
- `agent/src/sr2fpga_agent/block_cost_accounting.py`
  - method-neutral preparation ledger
  - event-chain validation and replay
- `agent/src/sr2fpga_agent/paired_cost_views.py`
  - checkpoint-manifest verified reader
  - actual/standalone/incremental reducer and verified reader

Existing modules change only at their ownership boundary:

- `method_adapters.py`: explicit checkpoint kinds/keys and compatibility-preserved
  lazy methods
- `generation/context_his.py`: injection of prepared HIS/project without
  re-materialization
- `model_budget.py`: minimal ledger protocol accepted by attempt and block ledgers
- `runner.py`: preparation orchestration, freeze policy, exclusive budgets,
  checkpoint injection, and event references
- `full_pack_smoke.py`: a new companion assembler that leaves v2 unchanged
- `contracts/manifest.json` and owning READMEs: registration and status

New contracts live under:

- `contracts/accounting/development-block-preparation-event-v1.schema.json`
- `contracts/episode-pack/development-shared-checkpoint-manifest-v1.schema.json`
- `contracts/evaluation/development-paired-block-cost-reconciliation-v1.schema.json`

## 13. Compatibility And Migration

- `paired-block-v1` remains byte-for-byte unchanged.
- Episode-pack-v1, trajectory-v2, attempt-event-v1, cost-summary-v1, and
  full-pack-runner-v2 gain no required fields and retain current readers.
- G3b uses companion linkage rather than optional authority fields on v2.
- Existing lazy coordinator behavior remains available to partial and legacy
  tasks. Complete paired blocks use explicit checkpoint kinds and eager prep.
- Direct and skeleton project checkpoints use distinct keys:
  - `paired/<digest>/direct-initial-project`
  - `paired/<digest>/system-his`
  - `paired/<digest>/skeleton-initial-project`
- Historical refs and runs are not rewritten.
- A new producer encountering an existing pre-G3b run ID fails freeze/resume
  validation rather than adding missing artifacts.
- Future official/G4b contracts require new versions and cannot relax the false
  authority constants of these development contracts.

## 14. Validation Matrix

### 14.1 Positive Conformance

| Test group | Fixed factors | Varied factor | Required result |
| --- | --- | --- | --- |
| Order invariance | block, prompts, fake responses, tools, budgets | two nontrivial Williams rows | physical initial calls=6; standalone initial calls=10; three views identical by method |
| Checkpoint identity | one gold-ready block | each checkpoint relation | one producer, exact consumer refs, complete DAG |
| M4/M5 sharing | same HIS and skeleton policy | M4 vs M5 | complete initial project ArtifactRef identical |
| Resume | complete manifest and event store | first run vs resume | zero repeated provider calls and zero duplicate charges |
| Visibility | same public requirement | M0-M5 prompt capture | no block/order/checkpoint/cost/sibling metadata |

### 14.2 Failure And Missingness

Each test changes one factor while holding all other configuration fixed:

- fail `S_D`, `S_H`, or `S_P` separately;
- make one cost axis unavailable at one checkpoint;
- exhaust block model-call budget;
- fail one provider call after a reservation;
- present a partial or corrupt resume manifest.

Assertions cover dependency-specific blocking, no fallback, retained physical
cost, standalone-to-stop attribution, unavailable contrast status, and absence
of authority escalation.

### 14.3 Tamper Matrix

Independent negative tests alter one item at a time:

- paired-block ref or identity
- checkpoint artifact ref or content digest
- consumer set, parent edge, missing parent, or graph cycle
- raw event ID, parent chain, sequence, close event, or source-set hash
- duplicate event across shared and method-exclusive partitions
- shared cost divided among consumers or omitted from standalone cost
- pre-checkpoint event inserted into an incremental arm
- M4 after-HIS and after-project views collapsed
- missing/unknown axis, unavailable changed to zero, or missing reason
- preparation cost assigned to ordinal zero or a method condition
- retry or repair ceiling misclassified
- trajectory/checkpoint/full-pack cross-lineage substitution
- execution-order-dependent attribution
- any false authority field changed to true
- wrong version or unknown field

## 15. Verification And Resource Estimate

No real API, GPU, training, or official evaluator is used.

- Focused contract/accounting tests run first.
- Fake-provider Runner integration runs two complete blocks under different
  Williams rows.
- Existing full repository validation remains:

  ```powershell
  python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q -p no:cacheprovider
  ```

- Changed-file Ruff, documentation-path tests, `git diff --check`, and sensitive
  content scans run before completion.
- Based on the current 1,815-test baseline, focused iterations should take a few
  minutes and the final full suite is expected to take approximately 10-12
  minutes after G3b tests are added.
- Test artifacts remain ignored under `artifacts/`; no dataset or report evidence
  promotion is authorized.

## 16. Completion Criteria

G3b development conformance is implemented only when all of the following hold:

1. Three explicit checkpoint kinds are registered, eagerly materialized, and
   content-verified before method execution.
2. M4/M5 consume the identical complete initial project.
3. Block preparation uses a method-neutral raw ledger and no shared cost appears
   in the first method's attempt ledger.
4. A clean block has six physical and ten standalone-attributed initial calls.
5. All 13 axes reconcile for actual, standalone, and three contrast-specific
   incremental views.
6. Two method orders produce identical per-method attribution and physical
   initial-call totals.
7. Failure, unavailable-axis, resume, visibility, and tamper tests fail closed.
8. Old contracts/readers/runs remain readable without G3b or G3 credit.
9. Full repository tests and changed-file quality checks pass.
10. Documentation states `G3b implemented, G3 not accepted` and retains G3c/G3d
    blockers.
