# SR2FPGA Contracts

Current PC2.1 development exchange boundaries also include runtime config/report,
model project/repair proposals, bounded public-feedback v2, explicit synthetic replay fixtures, and analysis
manifest/results/policy/report under `execution/`. They are registered only in
[`manifest.json`](manifest.json); see the [current runtime](../agent/src/sr2fpga_agent/execution/README.md).
Their scope flags do not authorize official experiments or promote local tests.

PC2.1 development now registers `development-public-context-v2`,
`pc21-development-capability-v1`, `pc21-development-target-v1`, and
`pc21-behavior-bundle-v1`. The public context extends the existing public
projection with the PC2.1 boundary, explicit fact roles and hash-bound assets;
it is development-only and grants no readiness or official outcome credit.
See the [PC development guide](../agent/src/sr2fpga_agent/pc/README.md).

> [Terminology, 2026-09-08](../docs/specs/2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> now serialized as `sr2fpga-pc-2.1`; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

Active schemas are registered by [`manifest.json`](manifest.json) and resolved
by key through `ContractRegistry`; projects exchange versioned files rather than
importing each other. Registration proves a format exists — never that a runtime
path implements it, that a family is qualified, or that a result is official.

Development public boundary (2026-09-16):
[`development-public-boundary-v1.schema.json`](episode-pack/development-public-boundary-v1.schema.json)
is registered as `development_public_boundary`, with a
[shape-only example](episode-pack/development-public-boundary-v1.example.json).
The wrapper requires `validation_scope: boundary_shape_only`. Its boundary has
`rtl_top`, `signature`, concrete `parameter_values` and `abi`; value mappings
use `signal`, stream mappings use `payload`/`valid`/`ready`, and domain mappings
explicitly name clock/reset pins or use null for nonconsuming slots.

Signature types reuse the registered PC2.1 schema by URI, resolved only from
local registered dependencies through `ContractRegistry`. No duplicate type
schema or network fallback is used. Dependency file identity participates in
validator caching. Use `ContractRegistry().load_schema("development_public_boundary").validate(payload)`;
an empty error tuple means shape conformance only. Bare JSON Schema readers must
also supply the PC2.1 resource locally.

For the first semantic slice, call
`sr2fpga_agent.public_boundary.check_public_boundary_ports(payload)`.
It runs the registered schema first, then checks exact logical-port/ABI-map
coverage and stream/value mapping form. It returns a tuple of diagnostics;
an empty tuple covers only those checks and does not mutate the document or
change its `boundary_shape_only` format marker into a readiness verdict.
The separate `check_public_boundary_domains(payload)` entry checks schema,
exact domain-map coverage, clock/reset pin presence (name versus null), and the
rule that `clock: none` requires `reset.kind: none`. Both entry points live in
`sr2fpga_agent.public_boundary` and return scoped diagnostics without mutation.
Passing the domain check does not qualify async reset, prove reset waveforms,
or establish target support. Port-to-domain references, parameter ranges,
physical-name collisions and reserved HDL words still require further checks.
JSON number spelling and duplicate-key rejection belong to the future strict
file reader. This schema does not register `public-context-v2` or a ready AI task,
and the PC CLI's opaque-source loader does not yet consume it. It is a reusable
boundary fragment for that future context, not a second source of requirements.

**On the gate names below.** Many section and field names still use the
`G1`-`G4b` / `RQ0` / `M6` vocabulary of `paper1-freeze-v1.7` and `paper1-v1.8`,
because those strings are frozen inside registered schemas and recorded
evidence. The current
[`paper1-v2.2`](../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
plan replaces that sequence with seven work packages `WP0`-`WP6`, makes the
requirement audit and EA optional extensions that default to disabled, and makes
`M5-M1@B4` and `M4-M3@initial` the two primary comparisons. **Contract
identifiers are not renamed to match** — renaming them would invalidate existing
artifacts. Read a `g3_` prefix as an identifier, not as a claim about the
current work-package sequence.

| Directory | Registered | Holds |
| --- | --- | --- |
| [`pc/2.1/`](pc/2.1/) | **yes** | **The current Project Contract serialization**, `sr2fpga-pc-2.1`: complete PC and model-authored design projection |
| `system-his/` | yes | The superseded serialization, W1-W10 matrix, capability and compatibility policy. Registered so existing artifacts stay readable; barred from new runtime paths |
| [`pc/`](pc/README.md) | yes | The System-HIS-era PC decision interface: decision, execution-source, assembly-record. Superseded by PC 2.1, still registered |
| [`pc/2.0/`](pc/2.0/README.md) | **no** | The PC 2.0 format design candidate — never adopted, resolved by nothing |
| `evaluation/` | yes | Public/hidden evaluation, terminal candidate, outcome and acceptance records |
| `requirement-audit/` | yes | The A_req / OASA case, event, replay, outcome and witness formats |
| `episode-pack/`, `accounting/`, `trajectory/` | yes | Episode identity, three-view cost accounting, attempt and trajectory lineage |
| `project-envelope/`, `project-package/`, `public-evaluation-candidate/`, `terminal-candidate/` | yes | FPP delivery, candidate submission and sealing |
| `training-release/`, `training-views/` | yes | Retained non-Paper-1 infrastructure |
| `task-catalog/` | yes | The task family catalog — **intent, not capability** |
| `tests/`, `tools/` | n/a | Registry conformance tests and maintenance tooling |

Natural-model M4 pre-candidate stops use
`evaluation/development-pre-candidate-stop-outcome-v3.schema.json`, retaining
`natural_llm` origin and measured local calls (0 for shared PC, otherwise 1).
The reducer replays frozen H stages, method events and raw cost lineage.
Legacy v1/v2 remain synthetic-only and require one local call. All three remain
excluded development records without official or pass-credit authority.

## Development closure contracts (`g3_` identifiers)

> These close **development conformance only**. Their acceptance artifacts set
> `official_outcome=false`, `official_authority=false`,
> `pass_credit_authority=false` and `g4b_authorized=false`, and nothing here
> grants an official outcome. Under v2.1 this work sits in `WP2`/`WP3`; the
> `g3_` identifiers are retained names, not the current sequence.

The [PC decision interface v1](pc/README.md) adds separate decision, execution-source
and assembly-record schemas. Its model payload excludes host-owned fields; its
assembly records never grant official experiment or pass-credit authority.

M5 PC correction outcomes retain the standalone three-call v1 reader. The
additive `development-his-correction-outcome-v2` records shared-PC local calls
and separately costed outer project repairs, rebuilt from verified raw events.
It does not recharge shared generation or grant additional repair budget.
When no terminal candidate exists, Runner retains the verified trajectory and
an explicit `not_evaluated` correction-outcome status instead of fabricating a
success receipt. Missing or corrupt lineage still fails closed.

The manifest additionally registers `g3-test-evidence-v1`, `g3-acceptance-v1`,
`development-checkpoint-stop-outcome-v1`, and
`development-hidden-execution-state-v1`. The first two bind executable local
evidence to a finite acceptance matrix; the latter two close no-candidate shared
preparation and evaluator-private execution/semantic state respectively.
Only the additive G3 acceptance artifact can set `g3_accepted=true`, and its
verdict must be reproduced by the Agent reducer. All four contracts keep official
outcome, official authority, pass-credit authority, and G4b authorization false.
Existing development outcome contracts are not promoted or redefined.

`unparsed-system-his-output-v1` preserves an unusable model reply and its parse
diagnostic as a provisional planning record. It is not a Project Contract:
the existing H0 schema check rejects it, and only a method with an explicitly
budgeted PC-correction privilege may attempt a new model-produced contract.

This directory owns language-neutral schemas and the canonical task catalog. It
must not contain runtime state.

[`manifest.json`](manifest.json) is the registry and the single source of
truth for what is currently registered; the groupings below are a reading aid,
not a second registry. Schemas and the target catalog define contracts and
intent. Current executable evidence remains in
`reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json` plus its
referenced stable artifacts. Do not infer verification from catalog
`implementation_status`.

The current
[`paper1-v2.2`](../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
research plan requires schema/checker/fixture conformance and known catalog
semantic defects to close before the M0-M5 official campaign; its WP0 inventory
records the catalog inconsistencies located so far.

`pc/2.1/` holds the **registered** [PC 2.1](../docs/specs/PC-2.1-AI-stream-contract-design.zh.md)
schemas: `project_contract_2_1` binds `schema_version: sr2fpga-pc-2.1`, and
`design_proposal_2_1` binds `$id: urn:sr2fpga:pc-design:2.1` because that
projection is a `$ref` wrapper carrying no version field. `ContractRegistry`
resolves both and rejects PC 2.0 and System-HIS documents — PC 2.1 ships no
reader, alias, or conversion path for either.

Registration establishes format identity only. The current `pc/` implementation
also provides typed public loading, listed configuration/tensor checks,
deterministic structure construction and real-parser-protected composition.
The [LLM case guide](../agent/src/sr2fpga_agent/tasks/README.md) documents current
fixed controls. `reports/conformance.json` remains the historical PC 2.0
70-test report and supplies no current PC2.1 or LLM benchmark result.

`pc/2.0/` keeps the never-adopted PC 2.0 candidate schemas, deliberately
unregistered.

<a id="system-his-layer"></a>
## Project Contract Layer

- `system-his/system-his-v1.2.schema.json`
- `system-his/system-his-backend-capabilities-v1.json`
- `system-his/system-his-well-formedness-v1.json` — the machine-readable
  W1-W10 stage and applicability matrix
- `system-his/system-his-compatibility-v1.json` — the canonical,
  legacy-quarantine, method-inapplicable, and unknown-representation policy

System-HIS v1.2 is the **superseded** Project Contract serialization.
[PC 2.1](pc/2.1/) replaced it on 2026-09-15 and shares no fields or conversion
path with the schemas below. These remain registered so existing artifacts stay
readable; new runtime paths must not use them.

Project Contract uses three deliberately separate layers:

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
  deny decision retain generic guidance. For a two-stage Project Contract request,
  the complete selection decision is evaluator-side sample/preflight/freeze
  metadata and does not enter the REQ2HIS prompt, Project Contract, or HIS2PROJECT
  input; only an `applied` decision contributes the recipe body to the REQ2HIS
  prompt. Direct-project and deterministic-reference methods do not record this
  decision. This describes the legacy generation path. The catalog retains its
  deny set as `legacy_candidate_primary_family_heldout`, with status
  `historical_development_only`; it is not the new research split. PC2.1 core
  family recipes are disabled. See the [catalog migration](task-catalog/README.md).

## Requirement Audit / OASA (A_req)

> **Optional extension, disabled by default under v2.1 section 12.1.** The core
> keeps only the public fact provenance and the `ready` /
> `needs_clarification` / `capability_gap` stop boundary before method
> dispatch; the full audit — natural requirement clusters, gold dispositions,
> allowed defaults, clarification answers, and its own sample size and
> statistics — is a separate frozen study. Enabling it does not change the
> M0-M5 denominator, and its outcomes can neither grant project pass credit nor
> remove an official instance. These schemas stay registered so the extension
> can be switched on without rebuilding the format layer.

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
  three-node Direct/PC/complete-project checkpoint DAG for a complete excluded
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
registration, or this paired-block path alone does not accept G3 or authorize an
outcome-producing campaign.

Registry key `development_shared_checkpoint_manifest` resolves
`development-shared-checkpoint-manifest-v1`. It is written by the Agent block-
preparation coordinator. The `block_preparation` verified reader, Runner resume
path, and cost reducer start from the independently supplied fingerprint-verified
preparation policy, then re-read the manifest and recompute paired identity,
planned keys, graph, consumers, artifact contents, event chain/partition, close
totals, and false-authority invariants. Runner then injects verified
`SharedArtifactRefs`; method adapters consume those downstream artifact
references and do not read the manifest directly. A valid shape does not by
itself prove that preparation succeeded or accept G3.

`project-package-v1` is the canonical schema for the candidate package's
`manifest.json`. It declares role-based top/source/interface/build intent and
any package-relative conditional or advisory artifacts. A valid package need
not contain a candidate testbench, predicted QoR report, Project Contract, or timing
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
  PC artifacts, exact eight-event pre-candidate prefix, correction parent/input
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
than trusting stored totals. Count axes are integer-valued, duration axes are
numeric, and unavailable inputs retain a reason instead of becoming zero.
Ordinary failed or `not_run` methods retain valid trajectory/event/cost lineage
in an incomplete companion. A method blocked by a shared checkpoint instead has
a null trajectory, no method events, and closed measured-zero exclusive cost;
its standalone-to-stop view still retains applicable prerequisite cost. A
schema-valid companion is development accounting data, not functional proof,
G3 acceptance, or an official outcome.

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
actual block cost, is never assigned to a method or execution ordinal, and is
not divided among checkpoint consumers. A valid event does not grant pass
credit or G3 authority.

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
