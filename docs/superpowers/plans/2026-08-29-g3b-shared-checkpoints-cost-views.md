# G3b Shared Checkpoints And Three-View Cost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement development-only eager shared checkpoints and artifact-derived actual, standalone-attributed, and checkpoint-specific incremental cost views for one complete excluded M0-M5 paired block.

**Architecture:** A method-neutral block-preparation phase runs after measurement freeze and before randomized method execution. It emits a closed raw cost-event chain and a verified three-node checkpoint manifest; the method phase consumes those immutable artifacts with exclusive budgets, and a companion reducer reconstructs all three 13-axis cost views from raw preparation events plus the existing six method trajectories and full-pack-v2 artifact.

**Tech Stack:** Python 3.11+ frozen dataclasses and Protocols, JSON Schema Draft 2020-12, ArtifactStore, ModelCallBudget, existing attempt/cost/trajectory readers, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-29-g3b-shared-checkpoints-cost-views-design.md`

## Global Constraints

- `paper1-freeze-v1.7` remains the research authority; this plan changes implementation only.
- All new artifacts use `evaluation_scope=excluded_development_conformance_only`.
- Every new official/pass-credit/RQ1/RQ2/G3/G4b authority field is the literal `false`.
- Do not modify `paired-block-v1`, episode-pack-v1, trajectory-v2, attempt-event-v1, cost-summary-v1, or full-pack-runner-v2 semantics.
- Complete paired blocks use eager preparation; partial and `development_derived` paths retain existing lazy behavior and mint no G3b artifact.
- Shared content, identities, schedule/order, checkpoint state, sibling results, and cost views remain model- and repair-invisible.
- M4/M5 share the complete behavior-filled initial project, not only the trusted deterministic skeleton.
- No real API, paid model call, training, official evaluator, dataset promotion, or evidence promotion is authorized.
- M5 H0-H3 correction scenario closure, repair-policy probes, two-axis hidden missingness, and positive `g3-acceptance-v1` remain G3c/G3d work.
- Set `PYTHONPATH` to this worktree's `agent/src` for every focused test command.
- Each task ends with focused tests, changed-file Ruff, `git diff --check`, independent review, and one atomic commit.

---

### Task 1: Register Method-Neutral Preparation Events And Implement The Raw Ledger

**Files:**
- Create: `contracts/accounting/development-block-preparation-event-v1.schema.json`
- Create: `contracts/tests/test_development_block_preparation_event_schema.py`
- Create: `agent/src/sr2fpga_agent/block_cost_accounting.py`
- Create: `agent/tests/test_sr2fpga_agent_block_cost_accounting.py`
- Modify: `contracts/manifest.json`
- Modify: `contracts/tests/test_contract_manifest.py`
- Modify: `agent/src/sr2fpga_agent/model_budget.py`

**Interfaces:**
- Consumes: existing `ArtifactRef`, `ArtifactStore`, `ContractRegistry`, and the 13-axis constants from `cost_accounting.py`.
- Produces:

```python
CHECKPOINT_IDS = (
    "direct_initial_project",
    "shared_system_his",
    "skeleton_initial_project",
)

@runtime_checkable
class ModelCostLedger(Protocol):
    def reserve(self, axis: str, amount: int | float, *, stage: str,
                visibility_class: str, limit: int | float,
                used_after: int | float, started_at: float | None = None) -> ArtifactRef: ...
    def record_budget_exhausted(self, axis: str, amount: int | float, *,
                stage: str, visibility_class: str, limit: int | float,
                used_after: int | float, started_at: float | None = None) -> ArtifactRef: ...
    def record_cost(self, *, stage: str, visibility_class: str,
                cost_delta: Mapping[str, int | float | None],
                status: str = "completed", duration_seconds: float | None = None,
                input_artifact_hashes: Iterable[str] = (),
                output_artifact_hashes: Iterable[str] = (),
                unavailable_axes: Mapping[str, str] | None = None,
                started_at: float | None = None) -> ArtifactRef: ...

class BlockPreparationCostLedger:
    def __init__(self, store: ArtifactStore, *, paired_block_ref: ArtifactRef,
                 failure_origin: str | None) -> None: ...
    @property
    def event_refs(self) -> tuple[ArtifactRef, ...]: ...
    def activate_checkpoint(self, checkpoint_id: str) -> None: ...
    def record_checkpoint(self, *, checkpoint_id: str, event_kind: str,
                          status: str, input_refs: Iterable[ArtifactRef] = (),
                          output_refs: Iterable[ArtifactRef] = (),
                          reason: str | None = None) -> ArtifactRef: ...
    def close(self, *, zero_axes: Iterable[str] = (),
              unavailable_axes: Mapping[str, str] | None = None) -> ArtifactRef: ...

@dataclass(frozen=True)
class ReplayedBlockPreparation:
    paired_block_ref: ArtifactRef
    event_refs: tuple[ArtifactRef, ...]
    events: tuple[dict[str, Any], ...]
    checkpoint_axes: dict[str, dict[str, Any]]
    actual_axes: dict[str, Any]
    source_events_sha256: str

def replay_development_block_preparation(
    store: ArtifactStore,
    event_refs: Iterable[ArtifactRef],
    *,
    registry: ContractRegistry | None = None,
) -> ReplayedBlockPreparation: ...
```

- `ModelCallBudget.attempt_cost_ledger` and its provider are typed against `ModelCostLedger`; runtime behavior for `AttemptCostLedger` remains unchanged.

- [ ] **Step 1: Write failing closed-schema tests**

Add a canonical fixture with no `method_condition`, an ordered parent chain, one checkpoint materialization event, a block-level accounting close, all 13 axes, and all authority flags false. Add independent negative tests for a method owner, unknown checkpoint, invalid parent, missing axis, unavailable without reason, authority escalation, wrong version, and unknown field.

```python
def test_block_preparation_event_is_method_neutral() -> None:
    payload = _event()
    assert "method_condition" not in payload
    _validator().validate(payload)


def test_block_preparation_event_rejects_method_owner() -> None:
    payload = _event()
    payload["method_condition"] = "M4"
    with pytest.raises(ValidationError):
        _validator().validate(payload)
```

- [ ] **Step 2: Run the schema tests to verify RED**

```powershell
python -m pytest contracts/tests/test_development_block_preparation_event_schema.py -q -p no:cacheprovider
```

Expected: fail because the schema and registry key do not exist.

- [ ] **Step 3: Add the schema and registry entry**

Register key `development_block_preparation_event`, version `development-block-preparation-event-v1`. Define checkpoint IDs, stages, event kinds, status/reason cross-field rules, ArtifactRef shape, 13-axis deltas, unavailable reasons, and false authority constants exactly as frozen in the design.

```json
{
  "development_block_preparation_event": {
    "version": "development-block-preparation-event-v1",
    "path": "contracts/accounting/development-block-preparation-event-v1.schema.json"
  }
}
```

- [ ] **Step 4: Write failing ledger/replay tests**

Cover an event chain containing one budget reservation, one provider-cost event, one checkpoint-materialized lineage event, and one close event. Assert the model call is counted once, lineage cost is zero, close totals are not double-counted, wall time comes from disjoint cost events, and every event ref is content-verified.

```python
def test_replay_counts_shared_call_once_and_excludes_close_delta(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    ledger = BlockPreparationCostLedger(
        store, paired_block_ref=_paired_ref(store), failure_origin="natural_llm"
    )
    ledger.activate_checkpoint("direct_initial_project")
    ledger.reserve("logical_model_calls", 1, stage="block_direct_initial",
                   visibility_class="accounting", limit=3, used_after=1)
    ledger.record_cost(
        stage="block_direct_initial",
        visibility_class="accounting",
        cost_delta=_provider_cost(transport=1, wall_time=0.25),
    )
    ledger.record_checkpoint(
        checkpoint_id="direct_initial_project",
        event_kind="checkpoint_materialized",
        status="completed",
        output_refs=(_project_ref(store),),
    )
    ledger.close(zero_axes=_remaining_zero_axes())

    replay = replay_development_block_preparation(store, ledger.event_refs)
    assert replay.actual_axes["logical_model_calls"]["value"] == 1
    assert replay.actual_axes["wall_time"]["value"] == 0.25
```

- [ ] **Step 5: Implement the ledger, replay, and ledger Protocol**

Use ArtifactStore write-once keys:

```python
key = (
    f"block-preparation-events/{paired_block_sha256}/"
    f"{sequence:06d}-{event_id}"
)
```

The replay function must reload every blob, recompute event IDs, validate parent/sequence identity, require exactly one final close event, partition events by checkpoint, propagate unavailable axes, and compare close totals with replayed totals.

- [ ] **Step 6: Run focused GREEN validation**

```powershell
python -m pytest `
  contracts/tests/test_development_block_preparation_event_schema.py `
  contracts/tests/test_contract_manifest.py `
  agent/tests/test_sr2fpga_agent_block_cost_accounting.py `
  agent/tests/test_sr2fpga_agent_cost_accounting.py `
  agent/tests/test_sr2fpga_agent_model_gateway_provenance.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/block_cost_accounting.py agent/src/sr2fpga_agent/model_budget.py agent/tests/test_sr2fpga_agent_block_cost_accounting.py contracts/tests/test_development_block_preparation_event_schema.py
git diff --check
```

- [ ] **Step 7: Commit Task 1**

```powershell
git add -- contracts/accounting/development-block-preparation-event-v1.schema.json contracts/manifest.json contracts/tests/test_contract_manifest.py contracts/tests/test_development_block_preparation_event_schema.py agent/src/sr2fpga_agent/block_cost_accounting.py agent/src/sr2fpga_agent/model_budget.py agent/tests/test_sr2fpga_agent_block_cost_accounting.py
git commit -m "feat: add method-neutral block cost ledger"
```

---

### Task 2: Register The Shared-Checkpoint DAG And Add Explicit Coordinator Keys

**Files:**
- Create: `contracts/episode-pack/development-shared-checkpoint-manifest-v1.schema.json`
- Create: `contracts/tests/test_development_shared_checkpoint_manifest_schema.py`
- Create: `agent/src/sr2fpga_agent/block_preparation.py`
- Create: `agent/tests/test_sr2fpga_agent_block_preparation.py`
- Modify: `contracts/manifest.json`
- Modify: `contracts/tests/test_contract_manifest.py`
- Modify: `agent/src/sr2fpga_agent/method_adapters.py`
- Modify: `agent/tests/test_sr2fpga_agent_method_adapters.py`

**Interfaces:**
- Consumes: Task 1 block event refs and replay, G3a `PairingKey`, `ArtifactStore`, project/planning emission types.
- Produces:

```python
class CheckpointId(str, Enum):
    DIRECT_INITIAL_PROJECT = "direct_initial_project"
    SHARED_SYSTEM_HIS = "shared_system_his"
    SKELETON_INITIAL_PROJECT = "skeleton_initial_project"

@dataclass(frozen=True)
class CheckpointNode:
    checkpoint_id: CheckpointId
    status: str
    reason: str | None
    artifact_ref: ArtifactRef | None
    content_sha256: str | None
    project_package_sha256: str | None
    trusted_skeleton_ref: ArtifactRef | None
    parent_checkpoint_ids: tuple[CheckpointId, ...]
    consumer_methods: tuple[str, ...]
    source_event_refs: tuple[ArtifactRef, ...]
    source_events_sha256: str

@dataclass(frozen=True)
class PreparedBlockArtifacts:
    paired_block_ref: ArtifactRef
    manifest_ref: ArtifactRef
    direct_initial_project: ProjectCandidateEmission | None
    system_his: PlanningArtifactEmission | None
    skeleton_initial_project: ProjectCandidateEmission | None
    trusted_skeleton: ProjectCandidateEmission | None
    event_refs: tuple[ArtifactRef, ...]

def write_development_shared_checkpoint_manifest(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    preparation_policy_sha256: str,
    nodes: Iterable[CheckpointNode],
    block_event_refs: Iterable[ArtifactRef],
) -> ArtifactRef: ...

def read_development_shared_checkpoint_manifest(
    store: ArtifactStore, reference: ArtifactRef
) -> dict[str, Any]: ...
```

- `PairedArtifactCoordinator` gains:

```python
def materialize_project_checkpoint(
    self, pairing: PairingKey, checkpoint_id: CheckpointId,
    factory: Callable[[], GeneratedProject]
) -> ProjectCandidateEmission: ...

def materialize_system_his_checkpoint(
    self, pairing: PairingKey,
    factory: Callable[[], Mapping[str, Any]]
) -> PlanningArtifactEmission: ...
```

Existing `materialize_initial_project()` and `materialize_system_his()` remain wrappers for compatibility.

- [ ] **Step 1: Write failing manifest Schema tests**

Assert exactly three nodes, exact parents/consumers, completed-node refs, failed/not-run null refs, false authority, and rejection of cycles, wrong consumer sets, skeleton without HIS parent, trusted skeleton substituted for complete project, missing event refs, and unknown fields.

```python
def test_manifest_requires_exact_checkpoint_graph() -> None:
    _validator().validate(_complete_manifest())

    wrong = copy.deepcopy(_complete_manifest())
    wrong["nodes"][2]["parent_checkpoint_ids"] = []
    with pytest.raises(ValidationError):
        _validator().validate(wrong)
```

- [ ] **Step 2: Run RED Schema tests**

```powershell
python -m pytest contracts/tests/test_development_shared_checkpoint_manifest_schema.py -q -p no:cacheprovider
```

- [ ] **Step 3: Add the manifest Schema and registry entry**

Register key `development_shared_checkpoint_manifest`. Use closed node records and conditional requirements for completed versus failed/not-run nodes. Keep graph-shape validation in the verified writer/reader as well as the Schema.

- [ ] **Step 4: Write failing explicit-key and verified-reader tests**

```python
def test_direct_and_skeleton_projects_use_distinct_checkpoint_keys(tmp_path) -> None:
    coordinator = PairedArtifactCoordinator(ArtifactStore(tmp_path / "store"))
    direct = coordinator.materialize_project_checkpoint(
        _pairing(), CheckpointId.DIRECT_INITIAL_PROJECT, _direct_project
    )
    skeleton = coordinator.materialize_project_checkpoint(
        _pairing(), CheckpointId.SKELETON_INITIAL_PROJECT, _skeleton_project
    )
    assert direct.artifact_ref.key.endswith("/direct-initial-project")
    assert skeleton.artifact_ref.key.endswith("/skeleton-initial-project")
    assert direct.artifact_ref != skeleton.artifact_ref
```

Add manifest round-trip, content tamper, cross-block ref, wrong DAG, event-set hash, and authority-escalation tests.

- [ ] **Step 5: Implement explicit keys and manifest writer/reader**

Map checkpoint IDs to immutable keys:

```python
_CHECKPOINT_SUFFIX = {
    CheckpointId.DIRECT_INITIAL_PROJECT: "direct-initial-project",
    CheckpointId.SHARED_SYSTEM_HIS: "system-his",
    CheckpointId.SKELETON_INITIAL_PROJECT: "skeleton-initial-project",
}
```

The reader reloads the paired block, replays Task 1 events, verifies the exact graph, reads every completed artifact, recomputes project/HIS/skeleton digests, and checks that each node's source-event set is the corresponding replay partition.

- [ ] **Step 6: Run focused GREEN validation**

```powershell
python -m pytest `
  contracts/tests/test_development_shared_checkpoint_manifest_schema.py `
  contracts/tests/test_contract_manifest.py `
  agent/tests/test_sr2fpga_agent_block_preparation.py `
  agent/tests/test_sr2fpga_agent_method_adapters.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/block_preparation.py agent/src/sr2fpga_agent/method_adapters.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_method_adapters.py contracts/tests/test_development_shared_checkpoint_manifest_schema.py
git diff --check
```

- [ ] **Step 7: Commit Task 2**

```powershell
git add -- contracts/episode-pack/development-shared-checkpoint-manifest-v1.schema.json contracts/manifest.json contracts/tests/test_contract_manifest.py contracts/tests/test_development_shared_checkpoint_manifest_schema.py agent/src/sr2fpga_agent/block_preparation.py agent/src/sr2fpga_agent/method_adapters.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_method_adapters.py
git commit -m "feat: register shared checkpoint manifests"
```

---

### Task 3: Register And Implement The Pure Three-View Cost Reducer

**Files:**
- Create: `contracts/evaluation/development-paired-block-cost-reconciliation-v1.schema.json`
- Create: `contracts/tests/test_development_paired_block_cost_reconciliation_schema.py`
- Create: `agent/src/sr2fpga_agent/paired_cost_views.py`
- Create: `agent/tests/test_sr2fpga_agent_paired_cost_views.py`
- Modify: `contracts/manifest.json`
- Modify: `contracts/tests/test_contract_manifest.py`

**Interfaces:**
- Consumes: paired block, Task 2 checkpoint manifest, Task 1 replay, existing `trajectory-v2` and `cost-summary-v1` artifacts.
- Produces:

```python
@dataclass(frozen=True)
class MethodCostSource:
    method_condition: str
    terminal_status: str
    trajectory_ref: ArtifactRef | None
    blocked_checkpoint_id: str | None = None

def reconcile_development_paired_block_costs(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    checkpoint_manifest_ref: ArtifactRef,
    block_event_refs: Iterable[ArtifactRef],
    methods: Iterable[MethodCostSource],
    source_full_pack_runner_ref: ArtifactRef | None,
    reducer_policy_sha256: str,
) -> tuple[dict[str, Any], ArtifactRef]: ...

def read_development_paired_block_cost_reconciliation(
    store: ArtifactStore, reference: ArtifactRef
) -> dict[str, Any]: ...
```

- [ ] **Step 1: Write failing Schema tests for complete and incomplete shapes**

The complete fixture has exact M0-M5 method records, three contrast records, 13-axis actual/standalone/arms/signed deltas, a non-null full-pack-v2 ref, source partition hashes, and all false authority flags. The incomplete fixture has a blocked method, null trajectory/full-pack ref, unavailable affected contrasts, and preserves pre-failure costs.

```python
def test_signed_delta_allows_negative_measured_value() -> None:
    payload = _complete_reconciliation()
    payload["incremental_contrasts"][0]["signed_delta_axes"]["wall_time"] = {
        "status": "measured", "value": -0.5, "reason": None
    }
    _validator().validate(payload)
```

Reject missing methods/contrasts/axes, negative non-delta values, unavailable-as-zero, missing reason, partial authority group, false flag escalation, and unknown fields.

- [ ] **Step 2: Run RED Schema tests**

```powershell
python -m pytest contracts/tests/test_development_paired_block_cost_reconciliation_schema.py -q -p no:cacheprovider
```

- [ ] **Step 3: Add the reconciliation Schema and registry entry**

Define separate non-negative `axis_result` and signed `signed_axis_result`. Use conditional rules so a complete record requires six trajectories and full-pack-v2, while an incomplete record requires at least one named blocked/unavailable reason.

- [ ] **Step 4: Write failing reducer algebra tests**

Build synthetic verified block events and method trajectories with scalar axis values. Assert:

```python
assert result["actual_block_axes"]["logical_model_calls"]["value"] == 6
assert _standalone(result, "M0", "logical_model_calls") == 1
assert _standalone(result, "M1", "logical_model_calls") == 1
assert _standalone(result, "M2", "logical_model_calls") == 2
assert _standalone(result, "M3", "logical_model_calls") == 2
assert _standalone(result, "M4", "logical_model_calls") == 2
assert _standalone(result, "M5", "logical_model_calls") == 2
assert _contrast_arm(result, "M4-M3", "M4", "logical_model_calls") == 1
assert _contrast_arm(result, "M4-M3", "M3", "logical_model_calls") == 1
```

Also assert unavailable propagation, negative signed deltas, exact event partition, blocked-to-stop attribution, and order invariance under permuted method records.

- [ ] **Step 5: Implement verified source loading and reducer formulas**

Freeze the prerequisite map and contrast map as module constants:

```python
_METHOD_PREREQUISITES = {
    "M0": ("direct_initial_project",),
    "M1": ("direct_initial_project",),
    "M2": (),
    "M3": ("shared_system_his",),
    "M4": ("shared_system_his", "skeleton_initial_project"),
    "M5": ("shared_system_his", "skeleton_initial_project"),
}

_CONTRASTS = {
    "M1-M0": ("direct_initial_project", "M1", "M0"),
    "M4-M3": ("shared_system_his", "M4", "M3"),
    "M5-M4": ("skeleton_initial_project", "M5", "M4"),
}
```

Reload and re-reconcile every attempt summary from raw events. Reject any overlap between block event IDs and method event IDs, duplicates across method partitions, checkpoint refs absent from trajectory inputs, or full-pack lineage disagreement.

- [ ] **Step 6: Run focused GREEN validation**

```powershell
python -m pytest `
  contracts/tests/test_development_paired_block_cost_reconciliation_schema.py `
  contracts/tests/test_contract_manifest.py `
  agent/tests/test_sr2fpga_agent_paired_cost_views.py `
  agent/tests/test_sr2fpga_agent_cost_accounting.py `
  agent/tests/test_sr2fpga_agent_full_pack_smoke.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/paired_cost_views.py agent/tests/test_sr2fpga_agent_paired_cost_views.py contracts/tests/test_development_paired_block_cost_reconciliation_schema.py
git diff --check
```

- [ ] **Step 7: Commit Task 3**

```powershell
git add -- contracts/evaluation/development-paired-block-cost-reconciliation-v1.schema.json contracts/manifest.json contracts/tests/test_contract_manifest.py contracts/tests/test_development_paired_block_cost_reconciliation_schema.py agent/src/sr2fpga_agent/paired_cost_views.py agent/tests/test_sr2fpga_agent_paired_cost_views.py
git commit -m "feat: reconcile paired-block cost views"
```

---

### Task 4: Implement Eager Dependency-Aware Block Preparation

**Files:**
- Modify: `agent/src/sr2fpga_agent/block_preparation.py`
- Modify: `agent/src/sr2fpga_agent/generation/context_his.py`
- Modify: `agent/src/sr2fpga_agent/method_adapters.py`
- Modify: `agent/tests/test_sr2fpga_agent_block_preparation.py`
- Modify: `agent/tests/test_sr2fpga_agent_context_his.py`
- Modify: `agent/tests/test_sr2fpga_agent_method_adapters.py`

**Interfaces:**
- Consumes: Task 1 ledger, Task 2 manifest/coordinator, frozen requirement context, Direct and HIS facades, H validator, and a method-neutral `ModelCallBudget(max_calls=3)`.
- Produces:

```python
@dataclass(frozen=True)
class BlockPreparationFacades:
    direct: FrozenContextDirectProjectFacade
    system_his: FrozenContextSystemHisFacade
    his_validation: FrozenContextSystemHisValidationFacade

def prepare_development_paired_block(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    pairing: PairingKey,
    context: FrozenRequirementContext,
    platform: PlatformProfile,
    facades: BlockPreparationFacades,
    model_budget: ModelCallBudget,
    preparation_policy_sha256: str,
) -> PreparedBlockArtifacts: ...
```

- `FrozenContextHisGeneratorBridge` gains optional `prepared_shared_artifacts: SharedArtifactRefs | None` and `prepared_trusted_skeleton: ProjectCandidateEmission | None`. When present, it never invokes coordinator factories for the supplied checkpoints.

- [ ] **Step 1: Write failing gold-ready preparation test**

Use counting fake Direct/REQ2HIS/HIS2PROJECT clients. Assert exactly one call per checkpoint, complete manifest, valid H0-H3 before `S_P`, distinct Direct/project checkpoint keys, and a complete shared M4/M5 project.

```python
result = prepare_development_paired_block(
    store,
    paired_block_ref=paired_ref,
    pairing=pairing,
    context=context,
    platform=platform,
    facades=BlockPreparationFacades(
        direct=direct_facade,
        system_his=his_facade,
        his_validation=validation_facade,
    ),
    model_budget=ModelCallBudget(max_calls=3, attempt_cost_ledger=ledger),
    preparation_policy_sha256="a" * 64,
)
assert direct_client.calls == 1
assert req2his_client.calls == 1
assert behavior_client.calls == 1
assert result.direct_initial_project is not None
assert result.system_his is not None
assert result.skeleton_initial_project is not None
assert result.manifest_ref.media_type == "application/json"
```

- [ ] **Step 2: Run the gold-ready test to verify RED**

```powershell
python -m pytest agent/tests/test_sr2fpga_agent_block_preparation.py::test_gold_ready_preparation_materializes_three_checkpoints_once -q -p no:cacheprovider
```

- [ ] **Step 3: Implement the serial preparation executor**

Run `S_D`, `S_H`, then `S_P`. `S_D` is independent of the HIS branch. Validate `S_H` through the complete H-stage facade before `S_P`. Record checkpoint materialization/failure/not-run events, close all 13 axes, write the manifest, then immediately read it back.

```python
try:
    direct = coordinator.materialize_project_checkpoint(
        pairing, CheckpointId.DIRECT_INITIAL_PROJECT,
        lambda: facades.direct.emit_project(context),
    )
except Exception as exc:
    direct = None
    ledger.record_checkpoint(
        checkpoint_id=CheckpointId.DIRECT_INITIAL_PROJECT.value,
        event_kind="checkpoint_failed", status="failed",
        reason=_preparation_failure_reason(exc),
    )
```

Apply the analogous dependency-aware path to `S_H` and `S_P`; never regenerate locally after failure.

- [ ] **Step 4: Write and pass prepared-adapter consumption tests**

Assert M0/M1 consume one Direct ref, M3 consumes shared HIS then performs one free project call, and M4/M5 consume one shared complete project without a behavior-fill call. Assert M4/M5 candidate snapshots remain method-specific even though their initial project bytes match.

- [ ] **Step 5: Run focused GREEN validation**

```powershell
python -m pytest `
  agent/tests/test_sr2fpga_agent_block_preparation.py `
  agent/tests/test_sr2fpga_agent_context_his.py `
  agent/tests/test_sr2fpga_agent_method_adapters.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/block_preparation.py agent/src/sr2fpga_agent/generation/context_his.py agent/src/sr2fpga_agent/method_adapters.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_context_his.py agent/tests/test_sr2fpga_agent_method_adapters.py
git diff --check
```

- [ ] **Step 6: Commit Task 4**

```powershell
git add -- agent/src/sr2fpga_agent/block_preparation.py agent/src/sr2fpga_agent/generation/context_his.py agent/src/sr2fpga_agent/method_adapters.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_context_his.py agent/tests/test_sr2fpga_agent_method_adapters.py
git commit -m "feat: eagerly prepare shared block checkpoints"
```

---

### Task 5: Integrate Preparation, Exclusive Budgets, And Checkpoint Injection Into Runner

**Files:**
- Modify: `agent/src/sr2fpga_agent/runner.py`
- Modify: `agent/src/sr2fpga_agent/model_budget.py`
- Modify: `agent/src/sr2fpga_agent/generation/context_his.py`
- Modify: `agent/tests/test_sr2fpga_agent_runner_method_dispatch.py`
- Modify: `agent/tests/test_sr2fpga_agent_runner.py`
- Modify: `agent/tests/test_sr2fpga_agent_full_pack_smoke.py`

**Interfaces:**
- Consumes: complete G3a `_PlannedPairedBlock`, Task 4 preparation result, and the existing per-sample method order.
- Produces:

```python
@dataclass(frozen=True)
class PreparedBlockRuntime:
    prepared: PreparedBlockArtifacts
    member_sample_ids: tuple[str, ...]
    exclusive_model_call_ceilings: dict[str, int]

def _plan_block_preparation_policy(
    config: RunnerConfig, samples: list[PlannedSample],
    paired_blocks: Mapping[str, _PlannedPairedBlock]
) -> dict[str, dict[str, Any]]: ...

def _exclusive_model_call_ceiling(
    config: RunnerConfig, sample: PlannedSample, method_condition: str
) -> int: ...
```

- [ ] **Step 1: Write failing preflight/freeze tests**

Assert preflight and runtime compute the same preparation-policy hash, expected checkpoint graph, block physical ceiling `3`, and per-method exclusive ceilings. Assert these fields remain audit-only and source/model mismatch stops before run-directory creation.

```python
assert policy["physical_initial_model_call_ceiling"] == 3
assert policy["exclusive_model_call_ceilings"] == {
    "M0": 0, "M1": 0, "M2": 2, "M3": 1, "M4": 0, "M5": 0
}
```

- [ ] **Step 2: Run RED Runner tests**

```powershell
python -m pytest agent/tests/test_sr2fpga_agent_runner_method_dispatch.py -k "preparation or exclusive" -q -p no:cacheprovider
```

- [ ] **Step 3: Add the preparation phase after freeze and before method loop**

For each complete planned block:

```python
freeze_manifest = _measurement_freeze_manifest(
    config,
    run_id,
    config_fingerprint,
    samples,
    tool_versions=tool_versions,
    tool_environment_ref=tool_environment_ref.to_dict(),
    l4_tool_environment_ref=l4_tool_environment_ref.to_dict(),
    paired_block_refs=paired_block_refs_by_sample,
    paired_execution_ordinals=paired_execution_ordinals,
)
freeze_fingerprint = write_or_validate_freeze(
    run_dir / "measurement_freeze.json",
    freeze_manifest,
    resume=resume and existing_run,
)
prepared_blocks = _prepare_complete_blocks(
    config=config,
    samples=samples,
    paired_block_plans=paired_block_plans,
    paired_block_refs=paired_block_refs,
    store=method_artifact_store,
    freeze_fingerprint=freeze_fingerprint,
)
```

Build preparation clients from the M0 Direct source and M4 two-stage source only after the freeze is written. Verify their effective identity matches the G3a block identity. Persist checkpoint manifest/event refs in run config projection, summary, generation/completion events, and attempt input hashes without exposing them to prompts.

- [ ] **Step 4: Inject prepared artifacts and enforce exclusive budgets**

Complete-block M0/M1/M4/M5 must short-circuit provider construction when no exclusive repair client is needed. M3 receives shared HIS plus its own project client. M2 is unchanged. M1/M5 construct only their permitted repair/correction client when their exclusive ceiling is nonzero.

```python
_SHARED_INITIAL_CALL_CEILING = {
    "M0": 1,
    "M1": 1,
    "M2": 0,
    "M3": 1,
    "M4": 2,
    "M5": 2,
}


def _exclusive_model_call_ceiling(config, sample, method):
    standalone = _sample_model_call_ceiling(sample, config, method)
    shared = _SHARED_INITIAL_CALL_CEILING[method]
    if standalone < shared:
        raise SystemExit(
            f"{method} standalone model-call ceiling {standalone} is below "
            f"its shared prerequisite ceiling {shared}"
        )
    return standalone - shared
```

The standalone ceiling remains available in metadata for analysis; the runtime
`ModelCallBudget` uses the exclusive ceiling on complete G3b blocks. This formula
also preserves an explicit `max_model_calls` override instead of silently replacing
it with method defaults.

- [ ] **Step 5: Add prompt-spy and no-first-method-charge tests**

Capture all M0-M5 prompts for a complete block and assert no checkpoint/cost/order/sibling field appears. Run a nontrivial row beginning with M1 or M3 and assert the first method's attempt summary has zero shared model-call cost.

- [ ] **Step 6: Run focused GREEN validation**

```powershell
python -m pytest `
  agent/tests/test_sr2fpga_agent_runner_method_dispatch.py `
  agent/tests/test_sr2fpga_agent_runner.py `
  agent/tests/test_sr2fpga_agent_full_pack_smoke.py `
  agent/tests/test_sr2fpga_agent_cost_accounting.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/runner.py agent/src/sr2fpga_agent/model_budget.py agent/src/sr2fpga_agent/generation/context_his.py agent/tests/test_sr2fpga_agent_runner_method_dispatch.py agent/tests/test_sr2fpga_agent_runner.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py
git diff --check
```

- [ ] **Step 7: Commit Task 5**

```powershell
git add -- agent/src/sr2fpga_agent/runner.py agent/src/sr2fpga_agent/model_budget.py agent/src/sr2fpga_agent/generation/context_his.py agent/tests/test_sr2fpga_agent_runner_method_dispatch.py agent/tests/test_sr2fpga_agent_runner.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py
git commit -m "feat: run eager paired-block preparation"
```

---

### Task 6: Assemble G3b Cost Companions And Prove Order Invariance

**Files:**
- Modify: `agent/src/sr2fpga_agent/full_pack_smoke.py`
- Modify: `agent/tests/test_sr2fpga_agent_full_pack_smoke.py`
- Modify: `agent/tests/test_sr2fpga_agent_paired_cost_views.py`

**Interfaces:**
- Consumes: existing `assemble_excluded_run_full_pack`, Task 5 completion events, Task 2 manifest, and Task 3 reducer.
- Produces:

```python
def assemble_excluded_run_full_pack_with_cost_views(
    store: ArtifactStore,
    *,
    events_path: Path,
    smoke_id: str,
    scenarios: Iterable[FullPackScenarioRecord],
    reducer_policy_sha256: str,
) -> tuple[
    dict[str, Any], ArtifactRef,
    dict[str, Any], ArtifactRef,
    dict[str, Any], ArtifactRef,
]: ...
```

The tuple is smoke report/ref, existing runner-v2 report/ref, and G3b cost reconciliation/ref.

- [ ] **Step 1: Write failing two-order integration test**

Run two fake-provider complete blocks with distinct nontrivial Williams rows and byte-equivalent fake responses. Count physical provider calls and compare method-keyed views.

```python
assert first.calls.initial_total == second.calls.initial_total == 6
assert _standalone_initial_calls(first.costs) == _standalone_initial_calls(second.costs) == {
    "M0": 1, "M1": 1, "M2": 2, "M3": 2, "M4": 2, "M5": 2
}
assert _method_keyed_views(first.costs) == _method_keyed_views(second.costs)
assert first.m4_initial_ref == first.m5_initial_ref
```

- [ ] **Step 2: Run the integration test to verify RED**

```powershell
python -m pytest agent/tests/test_sr2fpga_agent_full_pack_smoke.py -k "three_view or order_invariance" -q -p no:cacheprovider
```

- [ ] **Step 3: Implement the companion assembler**

Preserve completion-event file order for G3a verification, then build method records by method ID for order-independent cost reduction. Require one common checkpoint manifest ref and its block-event refs across six completions. Call existing v2 assembly first, then the G3b reducer.

- [ ] **Step 4: Add full lineage and call-count assertions**

Verify:

- checkpoint manifest was written before the first model-method event;
- all six trajectories bind the manifest/block event hashes;
- no preparation event appears in an attempt-event partition;
- physical call count remains six under both orders;
- M4/M5 complete initial ArtifactRefs match;
- all false authority fields survive projection.

- [ ] **Step 5: Run focused GREEN validation**

```powershell
python -m pytest `
  agent/tests/test_sr2fpga_agent_full_pack_smoke.py `
  agent/tests/test_sr2fpga_agent_paired_cost_views.py `
  agent/tests/test_sr2fpga_agent_block_preparation.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/full_pack_smoke.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py agent/tests/test_sr2fpga_agent_paired_cost_views.py
git diff --check
```

- [ ] **Step 6: Commit Task 6**

```powershell
git add -- agent/src/sr2fpga_agent/full_pack_smoke.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py agent/tests/test_sr2fpga_agent_paired_cost_views.py
git commit -m "feat: assemble G3b cost companions"
```

---

### Task 7: Close Preparation Failure, Unavailable-Axis, And Resume Semantics

**Files:**
- Modify: `agent/src/sr2fpga_agent/block_preparation.py`
- Modify: `agent/src/sr2fpga_agent/block_cost_accounting.py`
- Modify: `agent/src/sr2fpga_agent/paired_cost_views.py`
- Modify: `agent/src/sr2fpga_agent/runner.py`
- Modify: `agent/tests/test_sr2fpga_agent_block_preparation.py`
- Modify: `agent/tests/test_sr2fpga_agent_paired_cost_views.py`
- Modify: `agent/tests/test_sr2fpga_agent_full_pack_smoke.py`

**Interfaces:**
- Extends the existing Task 4/5/6 interfaces; introduces no new public contract.

- [ ] **Step 1: Write one-factor preparation-failure tests**

Parameterize failure at each checkpoint. Assert exact dependent-method blocking, unrelated-method continuation, no fallback calls, retained actual cost, standalone-to-stop attribution, and unavailable affected contrasts.

```python
@pytest.mark.parametrize(
    ("failed", "blocked"),
    (
        ("direct_initial_project", {"M0", "M1"}),
        ("shared_system_his", {"M3", "M4", "M5"}),
        ("skeleton_initial_project", {"M4", "M5"}),
    ),
)
def test_checkpoint_failure_blocks_only_dependents(failed, blocked):
    fixture = _checkpoint_failure_fixture(failed)
    prepared = fixture.prepare()
    assert prepared.blocked_methods == blocked
    assert fixture.fallback_call_count == 0
    assert prepared.manifest["manifest_status"] == "incomplete"
    assert prepared.costs["actual_block_axes"]["logical_model_calls"]["value"] >= 1
```

- [ ] **Step 2: Write unavailable-axis propagation tests**

For each of the 13 axes, make exactly one source checkpoint unavailable. Assert actual and dependent standalone/incremental arms are unavailable, unrelated methods remain measured, and signed delta is unavailable.

- [ ] **Step 3: Write resume idempotence tests**

Run preparation once, capture client call counts and refs, then resume with the exact plan. Assert no new calls/events/charges and identical manifest ref. Modify one ref, event, policy hash, or close total and assert resume fails closed before method execution. Assert partial preparation requires a new run ID.

- [ ] **Step 4: Implement dependency blocking and strict resume**

Use the manifest graph to derive blocked methods. Never reconstruct blocked methods by provider fallback. Reopen only verified complete manifests; incomplete/mismatched state raises `SharedCheckpointResumeError`.

```python
if existing_manifest is not None:
    verified = read_development_shared_checkpoint_manifest(store, existing_manifest)
    if verified["manifest_status"] != "complete":
        raise SharedCheckpointResumeError(
            "incomplete block preparation requires a new run ID"
        )
```

- [ ] **Step 5: Run focused GREEN validation**

```powershell
python -m pytest `
  agent/tests/test_sr2fpga_agent_block_preparation.py `
  agent/tests/test_sr2fpga_agent_paired_cost_views.py `
  agent/tests/test_sr2fpga_agent_full_pack_smoke.py -q -p no:cacheprovider
python -m ruff check agent/src/sr2fpga_agent/block_preparation.py agent/src/sr2fpga_agent/block_cost_accounting.py agent/src/sr2fpga_agent/paired_cost_views.py agent/src/sr2fpga_agent/runner.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_paired_cost_views.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py
git diff --check
```

- [ ] **Step 6: Commit Task 7**

```powershell
git add -- agent/src/sr2fpga_agent/block_preparation.py agent/src/sr2fpga_agent/block_cost_accounting.py agent/src/sr2fpga_agent/paired_cost_views.py agent/src/sr2fpga_agent/runner.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_paired_cost_views.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py
git commit -m "feat: close shared checkpoint failure semantics"
```

---

### Task 8: Add The Adversarial G3b Tamper And Visibility Matrix

**Files:**
- Modify: `agent/tests/test_sr2fpga_agent_block_cost_accounting.py`
- Modify: `agent/tests/test_sr2fpga_agent_block_preparation.py`
- Modify: `agent/tests/test_sr2fpga_agent_paired_cost_views.py`
- Modify: `agent/tests/test_sr2fpga_agent_runner_method_dispatch.py`
- Modify: `agent/tests/test_sr2fpga_agent_full_pack_smoke.py`
- Modify: `contracts/tests/test_development_block_preparation_event_schema.py`
- Modify: `contracts/tests/test_development_shared_checkpoint_manifest_schema.py`
- Modify: `contracts/tests/test_development_paired_block_cost_reconciliation_schema.py`

**Interfaces:**
- Exercises existing writers/readers/reducers only; adds no production interface.

- [ ] **Step 1: Add raw-event integrity tamper tests**

Independently alter event ID, parent, sequence, paired-block ref, checkpoint ID, source-event hash, close totals, missing close, duplicate event, and cost assignment to a method owner. Every mutation must fail replay.

- [ ] **Step 2: Add checkpoint-DAG and artifact tamper tests**

Independently alter consumer set, parent edge, cycle, completed/null mismatch, project/HIS/skeleton digest, cross-block artifact, trusted-skeleton substitution, and event partition. Every mutation must fail manifest read.

- [ ] **Step 3: Add cost-view algebra tamper tests**

Independently divide shared cost, omit shared cost from standalone, duplicate a raw event across partitions, insert pre-checkpoint cost into an incremental arm, merge M4's two views, delete/rename an axis, replace unavailable with zero, alter a signed delta, or swap a trajectory/full-pack ref. Every mutation must fail verified read or reconstruction equality.

- [ ] **Step 4: Add authority and visibility tests**

Set every false authority flag to true independently in each contract. Add an M0-M5 prompt spy whose requirement does not contain the canaries and assert none of the following appear:

```python
for forbidden in (
    paired_block_id,
    replicate_id,
    str(execution_schedule_seed),
    checkpoint_manifest_ref.sha256,
    "standalone_attributed",
    "actual_block_consumption",
    "sibling_method_status",
):
    assert forbidden not in serialized_model_messages
```

- [ ] **Step 5: Run the complete adversarial matrix**

```powershell
python -m pytest `
  contracts/tests/test_development_block_preparation_event_schema.py `
  contracts/tests/test_development_shared_checkpoint_manifest_schema.py `
  contracts/tests/test_development_paired_block_cost_reconciliation_schema.py `
  agent/tests/test_sr2fpga_agent_block_cost_accounting.py `
  agent/tests/test_sr2fpga_agent_block_preparation.py `
  agent/tests/test_sr2fpga_agent_paired_cost_views.py `
  agent/tests/test_sr2fpga_agent_runner_method_dispatch.py `
  agent/tests/test_sr2fpga_agent_full_pack_smoke.py -q -p no:cacheprovider
git diff --check
```

- [ ] **Step 6: Commit Task 8**

```powershell
git add -- contracts/tests/test_development_block_preparation_event_schema.py contracts/tests/test_development_shared_checkpoint_manifest_schema.py contracts/tests/test_development_paired_block_cost_reconciliation_schema.py agent/tests/test_sr2fpga_agent_block_cost_accounting.py agent/tests/test_sr2fpga_agent_block_preparation.py agent/tests/test_sr2fpga_agent_paired_cost_views.py agent/tests/test_sr2fpga_agent_runner_method_dispatch.py agent/tests/test_sr2fpga_agent_full_pack_smoke.py
git commit -m "test: add G3b adversarial matrix"
```

---

### Task 9: Synchronize v1.12 Status And Run Final Verification

**Files:**
- Modify: `README.md`
- Modify: `agent/README.md`
- Modify: `contracts/README.md`
- Modify: `docs/README.md`
- Modify: `docs/specs/README.md`
- Modify: `docs/current-status.md`
- Modify: `docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md`

**Interfaces:**
- Produces code-development status `sr2fpga-paper1-code-dev-v1.12` only if every G3b completion criterion in the approved design is verified.
- Leaves `paper1-freeze-v1.7`, `g3_accepted=false`, and G3c/G3d blockers unchanged.

- [ ] **Step 1: Update documentation with bounded status**

Record:

- eager three-checkpoint preparation implemented for complete excluded blocks;
- physical initial calls=6 and standalone-attributed initial calls=10 in fake fixtures;
- actual/standalone/incremental 13-axis reconciliation implemented;
- partial/legacy behavior retained without G3b authority;
- M5 H-stage scenario matrix, capability binding, hidden missingness, and positive G3 reducer remain open;
- no model, training, official, or paper outcome was produced.

- [ ] **Step 2: Run focused G3b tests**

```powershell
python -m pytest `
  contracts/tests/test_development_block_preparation_event_schema.py `
  contracts/tests/test_development_shared_checkpoint_manifest_schema.py `
  contracts/tests/test_development_paired_block_cost_reconciliation_schema.py `
  agent/tests/test_sr2fpga_agent_block_cost_accounting.py `
  agent/tests/test_sr2fpga_agent_block_preparation.py `
  agent/tests/test_sr2fpga_agent_paired_cost_views.py `
  agent/tests/test_sr2fpga_agent_runner_method_dispatch.py `
  agent/tests/test_sr2fpga_agent_full_pack_smoke.py -q -p no:cacheprovider
```

- [ ] **Step 3: Run the full repository test surface**

Use a repository-external basetemp so repository-discovery tests do not find the parent checkout:

```powershell
$env:PYTHONPATH='D:\Project\cuc-ai-fpga\artifacts\worktrees\codex-g3b-shared-checkpoints-cost-views\agent\src'
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q `
  --basetemp 'C:\Users\Aowen Yang\.codex\visualizations\2026\08\26\01a03c7b-544f-7750-bf9f-2efd17234550\pytest-basetemp-g3b-final' `
  -p no:cacheprovider
```

Update `docs/current-status.md` only with the actual observed count.

- [ ] **Step 4: Run quality, documentation, and sensitive-content checks**

```powershell
$base='e8ea7fa0fb268435a892275d9cfa4467775a7f01'
$pyFiles=@(git diff --name-only $base -- '*.py')
python -m ruff check $pyFiles
python -m pytest compatibility_tests/test_active_documentation_paths.py -q -p no:cacheprovider
git diff --check $base
```

Scan the branch diff for API keys, private endpoints, local absolute paths, hidden evaluator material, generated outputs, and untracked artifacts. Do not repair repository-wide Ruff debt outside changed files.

- [ ] **Step 5: Request independent code/protocol and documentation reviews**

The code/protocol reviewer verifies checkpoint identity, method-neutral cost ownership, 6/10 call algebra, order invariance, failure/resume, visibility, tamper behavior, compatibility, and false authority. The documentation reviewer verifies v1.12 labels, test counts, G3-open boundaries, and absence of result overclaim.

- [ ] **Step 6: Commit Task 9**

```powershell
git add -- README.md agent/README.md contracts/README.md docs/README.md docs/specs/README.md docs/current-status.md docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md
git commit -m "chore: finalize G3b development checkpoint"
```

## Plan Self-Review Checklist

- Every approved design section maps to Tasks 1-9.
- Three new contract versions and registry keys are named consistently.
- `BlockPreparationCostLedger`, `PreparedBlockArtifacts`, `MethodCostSource`, and reducer signatures are consistent across tasks.
- Raw block events remain method-neutral; no task modifies attempt-event-v1 semantics.
- M4/M5 complete-project sharing is distinct from deterministic-skeleton identity.
- All 13 axes, unavailable propagation, signed deltas, failures, resume, visibility, tamper, and order invariance have explicit tests.
- Partial/legacy paths and old contracts remain compatible but cannot gain G3b/G3 authority.
- The plan contains no real API, training, promotion, official-evaluation, or G3-acceptance action.

## Spec Coverage Mapping

| Approved design requirement | Plan task |
| --- | --- |
| Method-neutral raw event contract and 13-axis replay | Task 1 |
| Three-node immutable checkpoint DAG and distinct keys | Task 2 |
| Actual, standalone, and contrast-specific incremental formulas | Task 3 |
| Eager SD/SH/SP preparation and complete M4/M5 project sharing | Task 4 |
| Freeze-before-preparation Runner orchestration and exclusive budgets | Task 5 |
| Full-pack-v2 companion linkage and two-order 6/10 invariance | Task 6 |
| Dependency failures, unavailable propagation, and resume | Task 7 |
| Tamper, authority, and visibility matrix | Task 8 |
| Compatibility, v1.12 status, full validation, and independent review | Task 9 |

Self-review found no uncovered approved requirement. M5 H-stage scenario outcomes,
repair probes, hidden two-axis closure, and positive G3 acceptance remain explicit
non-goals assigned to G3c/G3d by the approved design.
