# SR2FPGA Contracts

This directory owns language-neutral schemas and the canonical task catalog. It
must not contain runtime state.

[`manifest.json`](manifest.json) is the registry and the single source of
truth for what is currently registered; the groupings below are a reading aid,
not a second registry. Schemas and the target catalog define contracts and
intent. Current executable evidence remains in
`reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json` plus its
referenced stable artifacts. Do not infer verification from catalog
`implementation_status`.

The active
[`paper1-freeze-v1.7`](../docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
requires schema/checker/fixture conformance and known catalog semantic defects
to close before the M0-M5 official campaign. It targets ACM TRETS and does not
train models.

## System-HIS Layer

- `system-his/system-his-v1.2.schema.json`
- `system-his/system-his-backend-capabilities-v1.json`
- `system-his/system-his-well-formedness-v1.json` — the machine-readable
  W1-W10 stage and applicability matrix
- `system-his/system-his-compatibility-v1.json` — the canonical,
  legacy-quarantine, method-inapplicable, and unknown-representation policy

System-HIS uses three deliberately separate layers:

- the versioned v1.2 Schema is the provider- and task-family-neutral core
  contract;
- the backend-capability profile records the semantic kinds, protocols,
  verification scenarios, and canonical testbench that the current lowerer can
  consume; and
- task-family recipe content is Agent prompt guidance, not part of either
  machine contract and not evidence that an arbitrary requirement is
  supported. Selection is automatic but accepts only exact catalog/runtime
  identifiers or registered whole-phrase triggers: unknown identifiers,
  ownership conflicts, missing recipe content, and a catalog-backed held-out
  deny decision retain generic guidance. For a two-stage System-HIS request,
  the complete selection decision is evaluator-side sample/preflight/freeze
  metadata and does not enter the REQ2HIS prompt, System-HIS, or HIS2PROJECT
  input; only an `applied` decision contributes the recipe body to the REQ2HIS
  prompt. Direct-project and deterministic-reference methods do not record this
  decision. The catalog records the candidate deny set and its policy
  provenance; the set is marked `candidate_g4a_not_signed`, not as a signed G4b
  split.

## Requirement Audit / OASA (RQ0)

- `requirement-audit/requirement-audit-v1.schema.json`
- `requirement-audit/ambiguity-case-manifest-v1.schema.json`
- `requirement-audit/ambiguity-audit-events-v1.schema.json`
- `requirement-audit/clarification-replay-v1.schema.json`
- `requirement-audit/ambiguity-outcome-v1.schema.json`
- `requirement-audit/ambiguity-witness-v1.schema.json`

These contracts separate the sealed evaluator-owned case manifest, Phase A
case-plus-summary outcome, Phase B clarification replay, and the
witness/adjudication basis and cluster-aware final audit reducer. Closed
projections prevent gold fields from becoming generation-visible. Replay
records bind the manifest, Phase A case, one precommitted answer, lineage, and
a persistent one-shot marker while retaining zero model/tool calls and zero
generation-boundary crossings. The outcome reducer keeps `not_run` outside
semantic confusion, separates both ready strata, and makes any repeated
observation false-proceed fail its base cluster. Inferential intervals remain
explicitly `not_frozen` until G4b. The witness artifact binds two independent
annotation commitments, adjudication, material-interpretation commitments,
gold fact/capability/default/assumption IDs, and a private visibility canary to
the sealed manifest. The witness also freezes which ready cases are
unknown-family counterexamples, allowing the reducer to report nearest-family
coercion without post-hoc text classification; repeated questions are detected
against Phase A fact provenance.

The OASA event contract carries Phase A execution status, counters, and
infrastructure status in the evaluator-only completion event. The outcome
contract reports their reconciliation with lineage-bound replay cost and keeps
counterfactual consistency at the base-cluster/observation level.

**Status:** these are development contracts and runtime paths; there is no
signed OASA fixture set or official audit outcome yet.

## Episode, Candidate, And Project Contracts

- `episode-pack/episode-pack-v1.schema.json`
- `episode-pack/paired-block-v1.schema.json` — excluded-development identity
  and execution-order commitment for one semantic-instance replicate across
  M0-M5; it carries no official, pass-credit, G3, or G4b authority
- `episode-pack/development-shared-checkpoint-manifest-v1.schema.json` — exact
  three-node Direct/HIS/complete-project checkpoint DAG for a complete excluded
  block; it carries no official, pass-credit, G3, or G4b authority
- `project-package/project-package-v1.schema.json`
- `project-envelope/project-envelope-v1.schema.json`
- `public-evaluation-candidate/public-evaluation-candidate-v1.schema.json`
- `public-evaluation-candidate/public-evaluation-candidate-v2.schema.json`
- `terminal-candidate/terminal-candidate-v1.schema.json`

`episode-pack-v1` separates a frozen generation-visible requirement context
from audit-only episode and method metadata. The public projection contains
only the ready requirement facts and registered platform/capability profile
commitments; evaluator family metadata is represented only by a hash in the
audit projection. The current builder is deliberately limited to development
and excluded-pilot packs. It cannot create an official pack; that requires a
future signed G4b loader.

`paired-block-v1` binds the semantic-instance and replicate identities, public
projection and model-provenance digests, decoding-control commitment,
independent schedule seed, and the complete M0-M5 execution order. Its pure
builder predicts the exact immutable reference before run-directory creation;
the excluded Runner materializes and verifies that reference, then binds it
through audit-only episode metadata, freeze records, events, trajectory input
hashes, and full-pack reconciliation. Partial blocks and legacy development
samples cannot mint the artifact. It remains a development contract: validation,
registration, or the current runtime path does not accept G3 or authorize an
outcome-producing campaign.

Registry key `development_shared_checkpoint_manifest` resolves
`development-shared-checkpoint-manifest-v1`. It is written by the Agent block-
preparation coordinator and read back by the Runner, method adapters, resume
guard, and cost reconciler. Its verified reader recomputes graph, consumer,
artifact-content, event-partition, and false-authority invariants. A valid shape
does not by itself prove that preparation succeeded or accept G3.

`project-package-v1` is the canonical schema for the candidate package's
`manifest.json`. It declares role-based top/source/interface/build intent and
any package-relative conditional or advisory artifacts. A valid package need
not contain a candidate testbench, predicted QoR report, System-HIS, or timing
constraint unless the episode and manifest make that artifact applicable.
Legacy `top_module` plus string `sources` manifests may be read only through an
explicit compatibility reader; they do not validate as canonical v1.

`project-envelope-v1` is a trusted-builder artifact stored outside the model-
editable candidate package. Its versioned integrity scheme binds a canonical
manifest digest and the complete project Merkle root into the package digest,
then binds method policy and normalized file ownership into a self-excluding
envelope digest. The Agent verifier rechecks the exact path set and actual file
bytes instead of trusting the envelope's own file records. Runtime-unsafe and
case-colliding paths are rejected.

The whole-file builder accepts only `model` or `trusted_builder` policy. A
separate trusted composite builder derives skeleton behavior regions from actual
UTF-8 byte ranges, binds their hashes to the registered method policy and
content-verified append-only events, and verifies complete non-overlapping file
coverage. Evaluator-material references remain fail-closed until CD3 supplies
opaque evaluator-owned commitment handles. Evaluator-owned material is never a
candidate-relative file record, and schema/hash validity alone must
not be interpreted as evaluator provenance or hidden readiness.

`terminal-candidate-v1` records immutable project-blob references after public
terminal selection; its authoritative terminal SHA-256 is the ArtifactStore
reference digest, not a model-supplied field.

`public-evaluation-candidate-v1` is the distinct pre-public-evaluation seal for
one attempt. It binds attempt identity, exact envelope and creation-event
artifact references, and immutable project blobs. It explicitly records that
terminal selection has not occurred and carries no pass-credit authority.
`public-evaluation-candidate-v2` preserves an envelope-invalid attempt for
evaluator-owned L0 diagnosis while forcing its project-envelope reference to
`null`; it can never qualify as a complete terminal candidate.

## Evaluation Contracts

- `evaluation/development-public-l2-harness-v1.schema.json` — hash-bound,
  evaluator-owned trusted public L2 manifest for development/excluded only; it
  fixes top, language standard, timeout and `simulator_exit_zero`, and carries no
  official or G4b authority
- `evaluation/development-hidden-conformance-outcome-v1.schema.json` — reducer-
  only sanitized development/excluded hidden result bound to the immutable
  terminal, public commitments, opaque outcome ref and one-shot ledger; it is
  never generation/repair visible and carries no official or G4b authority
- `evaluation/official-hidden-outcome-v1.schema.json`
- `evaluation/training-qualification-outcome-v1.schema.json`
- `evaluation/full-pack-smoke-report-v1.schema.json`
- `evaluation/full-pack-runner-reconciliation-v1.schema.json` — excluded-only
  companion that re-verifies M0-M5 `trajectory-v2`, cost-summary, matching
  terminal-seal, public-projection, opaque development-hidden lineage and the
  optional sanitized hidden outcome while keeping every official/RQ/G3 flag
  false
- `evaluation/full-pack-runner-reconciliation-v2.schema.json` — current
  additive, versioned successor used by the runtime writer; it retains the v1
  evidence checks while replacing the obsolete closure blocker with
  `runtime_scenario_evidence_reconciliation`; v1 remains registered for existing
  artifacts
- `evaluation/development-paired-block-cost-reconciliation-v1.schema.json` —
  reducer-owned G3b companion that binds the paired block, checkpoint manifest,
  preparation events, six method trajectories and full-pack-v2 linkage, then
  records actual, standalone-attributed and three checkpoint-specific 13-axis
  cost views with all official/pass-credit/RQ/G3/G4b authority fixed false
- `evaluation/development-public-evaluation-v1.schema.json` — sanitized,
  source-hash-bound projection that takes L0-L3 stages from the verified
  terminal-public authority when present and retains Recorder repair/missingness
  facts for compatibility; it is non-official and cannot carry VPP credit
- `evaluation/development-terminal-public-outcome-v1.schema.json` — one-shot
  terminal-shadow public authority output bound to an immutable candidate and
  frozen public/tool hashes; raw logs remain in a separate evaluator store and
  the returned record cannot drive repair or official outcomes and must agree
  with the selected-attempt public stages before hidden dispatch
- `evaluation/development-attempt-public-outcome-v1.schema.json` — the matching
  retained one-shot shadow contract for isolated compatibility checks
- `evaluation/development-authoritative-attempt-public-outcome-v1.schema.json`
  — sanitized evaluator-owned development/excluded repair, terminal-selection,
  and pass-credit source; it cannot mint an official outcome
- `evaluation/development-terminal-selection-v1.schema.json` — fail-closed
  `@1`/`AT_A` selection over verified immutable candidates and authoritative
  attempt outcomes; it is development/excluded only and fixes all official/G4b
  authority flags to false
- `evaluation/development-oracle-run-evidence-v1.schema.json` — evaluator-local
  independent-oracle scenario/run evidence with a closed execution-failure
  origin taxonomy; raw simulator logs remain development evidence and the
  contract fixes pass-credit and official-outcome authority to false
- `evaluation/development-tool-environment-v1.schema.json` — a content-addressable
  development-preflight snapshot of the four core open-source RTL executables,
  their version probes and executable hashes without local absolute paths; it
  explicitly carries no terminal, pass-credit, or official authority
- `evaluation/development-l4-qor-provenance-v1.schema.json` — stage-bound raw
  report/log hashes plus the core-tool snapshot ref for one L4-open or
  L4-commercial QoR record; it remains explicitly incomplete until the exact
  launched L4 tool version is captured and carries no terminal/official credit
- `evaluation/development-l4-tool-environment-v1.schema.json` — exact executable
  and version-output hashes for the OpenXC7 internal tools and Vivado; probes
  that may instantiate WSL/Nix/Vivado are disabled unless explicitly authorized,
  and the development artifact carries no terminal/pass-credit/official authority
- `evaluation/pilot-target-profile-pair-manifest-v1.schema.json` — excluded-only
  RQ4 pair definitions with stable pair/member/profile hashes, one declared
  change axis or explicit compound profile, invariant/change/compliance
  commitments, fixed L3/OpenXC7-L4 endpoints, full-pair cost rule, and no
  official-population or pass-credit authority
- `evaluation/development-target-profile-pair-outcome-v1.schema.json` — one
  development M0-M5 pair outcome retaining baseline and variant results,
  compliance violations, member missingness, verified cost-summary refs and all
  13 paired cost axes; development `TPA-L4` cannot carry terminal or official credit
- `evaluation/development-pre-candidate-stop-outcome-v1.schema.json` — narrow
  excluded M4/H0 design-stop authority that re-reads the frozen episode pack,
  schema-invalid planning artifact, ordered append-only method events, raw cost
  events and terminal-null trajectory; it retains the denominator, derives
  development VPP false, and fixes every official/RQ/G3/G4b flag to false
- `evaluation/development-pre-candidate-stop-outcome-v2.schema.json` — current
  excluded M4 H0-H3 stop authority; it binds the committed platform profile to
  the frozen episode pack, deterministically re-runs the ordered H stages from
  the planning artifact, requires the complete ordered five-event episode stream,
  preserves downstream `not_run`, and retains the same
  non-official/no-pass-credit boundary while v1 remains readable
- `evaluation/development-his-correction-outcome-v1.schema.json` — excluded M5
  development-only correction acceptance; it re-reads the initial and corrected
  HIS artifacts, exact eight-event pre-candidate prefix, correction parent/input
  hashes, corrected candidate and terminal lineage, raw attempt cost events and
  development episode outcome. It requires one complete H0-H3 rerun after one
  correction, exactly `req2his/system_his_repair/his2project`, zero project
  repair, and fixes every official/pass-credit/RQ/G3/G4b flag to false
- `evaluation/development-episode-outcome-v1.schema.json` — excluded-only reducer
  output that re-verifies raw-event trajectory/cost/terminal lineage, reconciles
  repair calls against the cost ledger, retains missingness, derives a separate
  development VPP when sanitized public/hidden inputs are scoreable, and fixes
  official VPP to `not_evaluated` while official authority is absent
- `evaluation/full-pack-outcome-reconciliation-v1.schema.json` — exactly-one
  M0-M5 development outcome aggregation with all six records retained, zero
  replacement, and all official/RQ/G3 flags false
- `evaluation/full-pack-outcome-reconciliation-v2.schema.json` — current
  runtime aggregation contract paired with runner reconciliation v2; it retains
  the v1 aggregate shape and names the remaining runtime-scenario evidence
  reconciliation blocker without rewriting v1 artifacts

Official held-out and training-fold evaluation use deliberately incompatible
`official-hidden-outcome-v1` and `training-qualification-outcome-v1` contracts.
The former is evaluator-only and forbidden from positive training releases.
Registration defines artifact shape only: no signed campaign authority or
official outcome producer exists yet.

`full-pack-smoke-report-v1` is a closed, development-only contract for the
excluded CD9 M0-M5 conformance smoke. It fixes all official, RQ1/RQ2, G3, and
G4b claim flags to false, permits only opaque hidden-outcome references, and
records the remaining G3 blockers. Each method record explicitly carries a
nullable deterministic-skeleton digest: only M4/M5 may populate it, and the
runtime reconciler verifies the referenced skeleton project before comparing
the pair. Final-candidate package equality is not skeleton evidence. Runtime
persistence validates this schema; registration does not make the smoke an
evidence-ledger or campaign result.

The v2 runner/outcome reconciliation contracts validate artifact-derived
runtime-scenario evidence and restrict `open_blockers` to a closed enum that
still includes the live `runtime_scenario_evidence_reconciliation` blocker.
Runner reconciliation v2 additionally permits an optional, all-or-none
paired-block reference plus planned/actual method orders and a verified-order
flag; the runtime recomputes those values from the block, JSONL completion order,
episode packs, freeze, and every trajectory attempt. Old v2 shapes without the
optional group remain readable by the current Schema. The v1 contracts remain
registered as backward-compatible historical shapes and retain their original
blocker values. Contract registration does not establish current G3 closure; use
[`docs/current-status.md`](../docs/current-status.md) for fixture, acceptance,
and open-debt status.

Registry key `development_paired_block_cost_reconciliation` resolves
`development-paired-block-cost-reconciliation-v1`. The Agent cost-view reducer
writes and verifies it; analysis readers consume the verified companion rather
than trusting stored totals. A schema-valid companion is development accounting
data, not functional proof, G3 acceptance, or an official outcome.

## Accounting Contracts

- `accounting/attempt-event-v1.schema.json`
- `accounting/cost-summary-v1.schema.json`
- `accounting/model-gateway-provenance-v1.schema.json`
- `accounting/development-provider-seed-capability-v1.schema.json`
- `accounting/development-block-preparation-event-v1.schema.json`

`attempt-event-v1` binds each cost delta or reservation to one episode,
attempt, M0-M5 condition, stage, visibility class, parent event, artifacts and
candidate-source failure origin. That historical field is closed to
`natural_llm`, `synthetic_injected`, `deterministic`,
`deterministic_template`, `compositional_assembly`, or `null`; it is distinct
from tool/oracle execution-failure classification. An `accounting_closed` event
must declare all 13 frozen cost
axes. `cost-summary-v1` is written only after the Agent reducer verifies the
content-derived event IDs, strict parent/sequence chain, unique final close,
raw-event totals and unavailable reasons. Missing provider usage remains
`unavailable`, not zero. These contracts do not imply that every Runner/tool
producer is connected or that G3 is closed.

Registry key `development_block_preparation_event` resolves
`development-block-preparation-event-v1`, the Agent block-preparation ledger's
method-neutral raw record. Its writer closes one ordered event chain per paired
block; replay readers recompute event identity, parent/sequence lineage,
checkpoint partitions, all 13 cost axes and close totals. Preparation cost is
never assigned to a method or execution ordinal, and a valid event does not grant
pass credit or G3 authority.

`model-gateway-provenance-v1` records the zero-based logical call ID, requested
seed, adapter forwarding, provider support status, system fingerprint status,
and hashed gateway identity for one instrumented development/excluded model
call. It does not infer deterministic support from a successful request or a
reported fingerprint.
`development-provider-seed-capability-v1` binds the complete repeated-call
protocol, documentation snapshot/source/review provenance, and ordered per-call
observations. The application reader recomputes every aggregate conclusion,
including counts, status, output/fingerprint consistency, token totals,
classification, limitations, profile ID, and eligibility. A schema-valid but
semantically inconsistent summary therefore fails closed. Only a complete
matching profile with independently reviewed `deterministic_documented` support
can become a paired-confirmatory candidate; self-reviewed, best-effort,
undocumented, unavailable, or failed profiles remain ineligible.
The v1 probe/eligibility identity is limited to Chat Completions. Responses
requests do not forward seed in the current adapter and therefore fail the
strict paired-confirmatory guard even when the provider/model/gateway match a
v1 capability file. `wire_api`, reasoning effort, response-storage policy and
`max_tokens` are separately frozen in Runner model provenance; supporting a
Responses seed mechanism requires a future versioned capability contract.
Both contracts fix official, pass-credit, G3, and G4b authority to false.

## Training-Release Contracts

These registered contracts are retained repository infrastructure outside
Paper-1. They remain documented for compatibility and safety, but they are not
Paper-1 methods, gates, deliverables, or evidence sources.

- `training-release/training-eligibility-v1.schema.json` — the evaluator-owned
  candidate-pool eligibility certificate
- `training-release/training-view-eligibility-sidecar-v1.schema.json` — the
  release-internal row-to-certificate binding
- `training-release/training-pool-manifest-v1.schema.json` — the matched
  E_final/E_traj candidate-pool manifest
- `training-release/training-release-manifest-v1.schema.json` — the public
  checksum manifest with explicit candidate/promoted authorization state
- `trajectory/trajectory-v1.schema.json`
- `trajectory/trajectory-v2.schema.json` — write-once event-derived attempt and
  cost lineage; it preserves explicit missing terminal-candidate lineage
- `training-views/training-view-row-v1.schema.json` — registered only as the
  legacy converter contract
- `training-views/training-view-row-v2.schema.json` — the canonical
  model-visible candidate-release row

`training-eligibility-v1` binds the frozen episode, initial snapshot, immutable
terminal candidate, project envelope, qualification outcome, source policy, and
evaluator checks. An eligible certificate requires a completed passing
training-fold qualification, zero official-hidden outcome references, and
every registered check to pass; `fail` and `not_run` remain explicit ineligible
inputs.

`training-view-eligibility-sidecar-v1` keeps release-internal proof outside the
model-visible v2 row. It binds the row hash, source episode, snapshot,
treatment, eligibility certificate/evidence bundle and snapshot envelope. M6T
and its matched `M6F_E_TRAJ` endpoint additionally require the same public-
transition evidence hash.

`training-pool-manifest-v1` records canonical sorted E_final/E_traj episode
sets, set hashes, all four treatment row references, and family/source/failure-
origin mixture strata. Its evaluator-owned builder requires identical M6U/M6F
episode sets, identical M6T/`M6F_E_TRAJ` subsets and transition hashes, E_traj
as an E_final subset, one frozen eligibility policy/split, and exact artifact
reconciliation.

`training-release-manifest-v1` inventories every model-visible view and
release-internal pool/sidecar/certificate artifact with exact byte size and
SHA-256. `candidate_unpromoted` fixes `training_authorized=false` and forbids an
authorization record; only the separate promoted shape can carry campaign,
training-plan and promotion-record hashes. The Agent candidate builder emits
only the unpromoted shape under `artifacts/`.

The promoted schema shape and three authorization hashes are not a signature or
promotion authority. `campaign-freeze-v1`, `training-plan-v1`, a signed
promotion record/verifier, and
`training-run-and-checkpoint-provenance-v1` are not registered yet. The current
Training-side inspector can recheck a caller-asserted promoted bundle's internal
shape and bindings, but it cannot authenticate those authority artifacts or
unlock training.

## Task Catalog

- `task-catalog/sr2fpga-task-catalog-v0.2.json` — the canonical task catalog

## Maintenance And Historical Audit Tools

The tools below remain available for controlled maintenance and historical
reorganization verification. Repository reorganization itself is complete; the
cleanup runbook is not active.

- `tools/build_dataset_inventory.py` rebuilds deterministic release checksums.
- `tools/inventory_tracked_tmp.py` inventories tracked legacy temporary files
  without moving or deleting them.
- `tools/plan_legacy_evidence_migration.py` maps active legacy evidence
  references to stable report paths without copying them.
- `tools/verify_phase_a_backup.py` rechecks an explicitly supplied external
  Phase A backup before any cleanup:

```powershell
python contracts/tools/verify_phase_a_backup.py `
  --root . `
  --backup-root $env:SR2FPGA_PHASE_A_BACKUP_ROOT
```

The backup verifier writes only the ignored
`artifacts/reorganization/phase-b4/backup-recheck.json` record after every
manifest, byte-count, checksum, workspace, and restore-sample check passes.
The record pins the verified manifest SHA-256 so later curation rejects a
backup changed after the gate.

After that gate passes, preview the exact legacy evidence selection:

```powershell
python contracts/tools/curate_legacy_evidence.py `
  --root . `
  --backup-root $env:SR2FPGA_PHASE_A_BACKUP_ROOT
```

The preview is also ignored and blocks on API-key-shaped content, private
absolute paths, missing files, hash changes, or destination conflicts. Do not
use `--apply` until the preview and cleanup inventory have received explicit
approval. An approved application must name the tracked manifest explicitly:

```powershell
python contracts/tools/curate_legacy_evidence.py `
  --root . `
  --backup-root $env:SR2FPGA_PHASE_A_BACKUP_ROOT `
  --apply `
  --output reports/reorganization/legacy-evidence-curation.json
```
