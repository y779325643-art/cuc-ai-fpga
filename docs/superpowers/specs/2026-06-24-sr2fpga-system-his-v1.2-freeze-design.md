# SR2FPGA System-HIS v1.2 Freeze Design

## Status

**Approved direction (2026-06-24); freeze ratified when the success criteria
pass.** This document commits `system-his-v1.2` as the single canonical
direction and stops the dual-schema (v1.1 + v1.2-topdown) drift — that decision
is in force now. The *freeze itself* (lock the fields and generate clean training
data at scale against them) is **ratified only after implementation validates the
schema**, because parts of it have not yet been run (see "Freeze ratification
gate"). Supersedes the prototype `system-his-v1.2-topdown`
(`docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md`)
and the inline `system-his-v1.1` schema in
`docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`. Where
they differ, this document governs.

> **Why not "frozen now":** the structural core (top/components/instances/
> data_flow/state/artifacts + cross-check) mirrors what v1.1 already runs, but the
> **new fields** — `data_flow.timing`, structured `control_flow`
> (`fsm_transition`/`enable_rule`), and the guard grammar — were designed in
> review and have **never been generated, checked, or exercised by any sample**.
> v1.1's flaws only surfaced when run (the T4 dual-instance failure); the same
> will hold here. So those fields are **provisional** until a real task exercises
> them. Freezing an unrun grammar is design-in-a-vacuum.

## Why freeze now

System-HIS is the **REQ2HIS training target** and the **L0 ground-truth
contract**. Once trajectories are generated at scale, schema churn invalidates or
forces migration of already-produced data. The repo currently runs **two schemas
in parallel** — the deterministic `ProjectGenerator` emits `system-his-v1.1`, the
DeepSeek two-stage path emits `system-his-v1.2-topdown` — which makes the REQ2HIS
target ambiguous. This document picks one canonical schema, defines what its
checker must enforce, and sets the migration/quarantine policy, so the next data
generation runs against a stable target.

## Decision summary

1. `system-his-v1.2` (dropping the `-topdown` prototype suffix) is the **single
   canonical schema**. The deterministic `ProjectGenerator` migrates to it.
2. The v1.2 checker **must gain HIS↔RTL cross-checks** (currently it does IR
   self-consistency only) to preserve the cross-file-consistency metric.
3. Cross-check strictness: **port existence + direction strict; width
   semantic-equivalence**.
4. `data_flow` carries an optional **timing contract** (latency / II /
   throughput) so pipeline depth and throughput are first-class.
5. `control_flow` is **load-bearing, verified at L2** (not advisory); FSMs are
   represented with structure in `state.fsms` and behavior in `control_flow`.
6. Guard expressions use a **shallow structured grammar (depth ≤ 2)**.
7. Legacy + v1.1 data is **quarantined** (labeled, kept for traceability, not
   mixed into the clean REQ2HIS training split).

## Freeze ratification gate

The freeze is staged, not declared all at once. Two tiers, each ratified by
evidence from implementation (the plan
`docs/superpowers/plans/2026-06-24-sr2fpga-system-his-v1.2-freeze.md`):

- **Tier 1 — structural core** (`schema_version`, `intent`, `top`, `components`,
  `instances`, `data_flow` path/endpoints, `state` (non-FSM), `timing`,
  `resources`, `verification`, `artifacts`) + the HIS↔RTL cross-check. This
  mirrors what the v1.1 checker already runs, so it is the low-risk part.
  **Ratified when:** the deterministic generator emits valid `system-his-v1.2`
  for **all** current task families and they pass the extended L0 checker
  (plan Task 7a/7b), and the cross-check reports a cross-file-consistency error
  rate (plan Task 5/6).

- **Tier 2 — provisional new fields** (`data_flow.timing` latency/II/throughput;
  structured `control_flow` `fsm_transition`/`enable_rule`; the guard grammar;
  `state.fsms`). These were designed in review and have never been generated or
  checked. They stay **provisional**: implemented and validated by the checker,
  but **not required in the REQ2HIS training target** until a real task exercises
  each one end-to-end. **Ratified when:** a pipelined task carries a
  `data_flow.timing` contract checkable at L2 (latency/II measured), and an
  FSM-bearing task (the RL agent FSM is the reference) round-trips through
  `state.fsms` + structured `control_flow` with auto-derived testbench
  liveness/stall scenarios. Until ratified, the guard grammar and FSM/timing
  shapes may still be revised based on what running them reveals — that is the
  point of keeping them provisional rather than frozen.

**Consequence for data collection:** the first clean training split may begin on
the **Tier-1 core** once Tier 1 is ratified, without waiting for Tier 2. REQ2HIS
targets do not depend on the provisional fields until Tier 2 ratifies, so
unvalidated grammar never pollutes the training target.

## Canonical schema and migration

- **Schema version string:** `system-his-v1.2`. Code, generators, and the
  checker emit/expect exactly this value. The `-topdown` suffix was the prototype
  marker and is retired.
- **Deterministic generator migration:** `ProjectGenerator` stops emitting
  `system-his-v1.1` and emits `system-his-v1.2`. This is the larger code change
  the freeze implies; it is in scope for the implementation plan, not optional.
  The deterministic generator is the trusted baseline, so its v1.2 output doubles
  as golden fixtures for the checker and as REQ2HIS supervision.
- **One checker, version-dispatched:** the project-level L0 checker keeps
  dispatching by `schema_version`. `system-his-v1.2` files go through the v1.2
  checker (now with cross-checks, below); `system-his-v1.1` / legacy files are
  accepted only for the quarantine/traceability path, never as clean training
  targets.

## Schema shape (canonical v1.2)

Organized as orthogonal architecture aspects (the way an FPGA architect reasons):

```json
{
  "schema_version": "system-his-v1.2",
  "intent":       {"user_prompt": "...", "design_goal": "...", "assumptions": []},
  "top":          {"name": "...", "parameters": [], "clocks": [], "resets": [],
                   "ports": [], "interfaces": []},
  "components":   [],
  "instances":    [],
  "data_flow":    [],
  "control_flow": [],
  "state":        {"registers": [], "counters": [], "fsms": [],
                   "buffers": [], "memories": []},
  "timing":       {"primary_clock": "...", "target_fmax_mhz": 0, "constraints": []},
  "resources":    {"optimization_goal": "balanced", "expected": {}},
  "verification": {"testbench": "...", "scenarios": [], "pass_condition": "..."},
  "artifacts":    {"top_module": "...", "rtl_sources": [], "testbench": "...",
                   "constraints": [], "manifest": "...", "predicted_qor": "..."}
}
```

Aspect roles: `top` = boundary; `components`/`instances` = composition (definition
vs concrete instance — the v1.2 split that resolves repeated-instance ambiguity);
`data_flow` = datapath + timing; `control_flow` = control logic; `state` =
architectural state; `timing`/`resources` = QoR/physical intent; `verification` =
acceptance; `artifacts` = mapping to the project package.

## L0 cross-check (v1.2 checker extension)

The v1.2 checker keeps its IR self-consistency checks and **adds HIS↔RTL
cross-checks** by parsing the generated RTL. This restores the metric the v1.1
checker provided and the prototype v1.2 checker dropped.

**Strict (hard failure on mismatch):**

- every `component` corresponds to an RTL module definition in its declared
  `source` file; every `instance` corresponds to an instantiation in `rtl/top.v`;
- **port existence and direction**: every port a component declares must exist in
  the RTL module with the same direction (`input`/`output`/`inout`); no extra,
  no missing;
- `data_flow.path` endpoints resolve to `top.<port>` or `<instance>.<port>` that
  actually exist;
- `artifacts` match `manifest.json`; the testbench instantiates the real top;
  `timing.constraints` reference only real top ports;
- (FSM cross-check) every `state.fsms[].states` set has a matching state
  enumeration in the RTL of its owner module (name-level match).

**Semantic-equivalence (not literal):**

- **port width**: `[7:0]`, `8`, and a parameterized form resolving to 8 are all
  equal. The checker compares resolved/normalized widths, never raw strings, so
  System-HIS stays an intent abstraction rather than an RTL mirror.

The principle: **structure (existence, direction, connectivity) is strict;
surface notation (width spelling) is normalized.**

## data_flow timing contract (pipeline / throughput)

Each `data_flow` path may carry an optional `timing` object:

```json
{
  "name": "main_stream",
  "path": ["top.in_data", "skid.out_data", "accum.sum", "top.sum"],
  "width": 8, "protocol": "valid_ready", "cdc": false,
  "timing": {"latency_cycles": 3, "initiation_interval": 1,
             "throughput": "1 sample/cycle"}
}
```

- `latency_cycles` = input→output latency (pipeline depth); `initiation_interval`
  (II) = cycles between accepted inputs (II=1 ⇒ fully pipelined); `throughput`
  derives from II.
- **Optional**: simple/unpipelined designs omit `timing`; pipelined designs
  include it. This keeps the REQ2HIS target stable for easy tasks.
- **Verification venue**: latency/II are measured at **L2** (simulation), Fmax at
  **L4** (P&R) — not vacuous.
- **Forward-compatible with Paper ②**: pipeline depth and II are exactly the QoR
  search variables, so first-classing them now avoids a later schema change.

Provenance: the rate/latency vocabulary is borrowed from dataflow models of
computation (SDF/KPN) as realized in HLS dataflow frameworks (TAPA, Stream-HLS,
HIDA, Calyx). The schema absorbs that vocabulary into `data_flow` without adopting
a pure dataflow MoC (see "Paradigm").

## control_flow (load-bearing, verified at L2)

`control_flow` is **not advisory**. Its correctness is verified at **L2** (the
testbench it drives), mirroring the v1.2 principle "L0 checks structure, L2 checks
function." data_flow is the structural aspect (L0-verifiable); control_flow is the
behavioral aspect (L2-verifiable).

### FSM representation (structure vs behavior split)

- **Structure** in `state.fsms`:

  ```json
  {"name": "agent_fsm", "owner": "agent_controller",
   "states": ["OBSERVE","INFER","SELECT","STEP","STORE","SAMPLE","UPDATE"],
   "initial": "OBSERVE", "reset_state": "OBSERVE"}
  ```

  L0 checks: states declared; `initial`/`reset_state` ∈ states; (cross-check) RTL
  contains a matching state enumeration.

- **Behavior** in `control_flow`:

  - `fsm_transition` — `{fsm, from, to, when, effect?}`. `from`/`to` must be
    declared states of `fsm`. Branches = multiple transitions from one state with
    different guards (e.g. ε-greedy explore vs exploit). Probabilistic sources
    (RNG) are modeled as components/state, not in the guard.
  - `enable_rule` ("conductor" pattern) — `when: fsm.state == X → assert
    datapath.start`. This explicitly links control to data_flow ("in INFER,
    start q_network") and is L2-checkable.

### Guard grammar (the intent/RTL boundary)

Guards use form **(b)**: structured, reference-checked, **nesting depth ≤ 2**.

```json
"when": {"all_of": [
  {"signal": "q_network.valid_out", "op": "==", "value": 1},
  {"signal": "agent_fsm.state",     "op": "==", "value": "INFER"}
]}
```

- Atoms: `{signal, op, value}` where `signal` references a declared port / state /
  flow (checked), `op` ∈ `{==, !=, <, >, &&, ||}`.
- Combinators: `all_of` / `any_of`, **at most 2 levels deep**.
- **Forbidden**: arbitrary nested boolean/arithmetic/bit expressions. The depth
  cap is the hard line that keeps System-HIS an intent abstraction, not Verilog.

### Why structured control_flow matters

A structured FSM + guards lets the testbench generator auto-derive **liveness**
scenarios (drive guards in sequence, assert the FSM walks the phases) and
**stall** scenarios (hold a guard low, assert the FSM stays). This makes the
failures of control-heavy designs measurable at L2, connecting control_flow to
the hardware-semantic failure taxonomy (backpressure / FSM-stall) in the reframe
spec. Free-text control_flow would make those failures un-generatable and
un-measurable.

## Paradigm: datapath+control backbone, dataflow timing absorbed

Three ways to organize a hardware-architecture IR were considered:

- **A — datapath + control** (Calyx-style): data_flow and control_flow as
  separate aspects. Checker- and testbench-implementable today.
- **B — dataflow actor/channel MoC** (SDF/KPN; TAPA/Stream-HLS/HIDA): actors with
  firing rules + production/consumption rates; throughput/pipeline native.
  Elegant for streaming, **awkward for control-heavy designs**.
- **C — orthogonal aspects**: organize the schema into independent aspects
  (boundary/composition/dataflow/control/state/timing/verification).

**Chosen: A as the primitive backbone + B's rate/latency vocabulary absorbed into
`data_flow.timing` + C's aspect organization.** Rationale: the benchmark body is
streaming valid-ready designs (B fits the datapath), but FSM/arbiter/controller
designs are coming (pure B cannot express them), so control_flow must stay an
independent first-class aspect.

### Stress test: RL accelerator (forward-compat, not specced now)

A reinforcement-learning accelerator (the T4/Stress flagship on the AC820-ZYNQ,
220 DSP + ARM) is the decisive case because it is **inherently hybrid**:

- streaming datapath (Q/policy-network inference = MAC array = the existing
  `matrix_vector_mac` task) → `data_flow.timing` (II / pipeline depth);
- control-heavy core (agent loop FSM: OBSERVE→INFER→SELECT→STEP→STORE→SAMPLE→
  UPDATE; ε-greedy branch; Bellman update; ARM/env handshake; replay-memory
  arbitration) → `control_flow` (irreducible to dataflow firing rules).

This confirms the hybrid choice: pure B is insufficient. The schema must be able
to **express** the RL accelerator (verified by mapping it onto v1.2 aspects), but
the freeze does **not** fully spec it. It also ties to existing assets
(`matrix_vector_mac`) and Paper ② (QoR search over the inference pipeline depth /
II / DSP allocation living in `data_flow.timing` + `resources`).

## Data migration / quarantine policy

- **Legacy** (no `schema_version`) and **`system-his-v1.1`** samples — including
  the committed baseline (a)/(b) snapshot — are **quarantined**: labeled by their
  schema, kept for traceability and as a comparison baseline, **never mixed into
  the clean REQ2HIS training split**.
- No migration tool is built (the v1.1 data volume is small; re-running under
  frozen v1.2 is cleaner than a lossy converter). Re-generation under v1.2 is the
  path to clean data.
- A derived/migrated view may be produced later for diagnostics only, explicitly
  marked as derived.

## Scope (freeze) vs out-of-scope (v1.3+)

**In the freeze:**

- `system-his-v1.2` schema (aspects above) + deterministic generator migration;
- v1.2 checker HIS↔RTL cross-checks (strict existence/direction, semantic width,
  FSM state-name cross-check);
- `data_flow.timing` (latency / II / throughput, optional);
- structured `control_flow` (fsm_transition / enable_rule) + guard grammar
  (depth ≤ 2);
- quarantine labeling for legacy/v1.1 data.

**Out of scope (later, v1.3+):**

- richer control_flow scheduling semantics beyond the rule kinds;
- behavioral (not structural) CDC verification;
- a v1.1→v1.2 migration tool;
- full RL-accelerator specification.

## Success criteria

- The deterministic generator emits valid `system-his-v1.2` for all current task
  families and passes the extended L0 checker.
- The v1.2 checker reports a cross-file-consistency error rate (the metric) on
  v1.2 samples.
- A pipelined task carries a `data_flow.timing` contract checkable at L2.
- An FSM-bearing task (RL agent FSM as the reference) is expressible with
  `state.fsms` + structured `control_flow`, and its testbench liveness/stall
  scenarios are auto-derivable.
- Legacy/v1.1 samples are schema-labeled and excluded from the clean training
  split.

## Relationship to existing documents

This freeze operationalizes the System-HIS portions of the reframe spec
(`2026-06-22-sr2fpga-research-reframe-design.md`) and supersedes the v1.2-topdown
prototype. The reframe spec's inline v1.1 schema block is now historical; the
hardware-semantic failure taxonomy it defines is realized through this schema
(data_flow.cdc, control_flow stall/handshake rules, state-based seq/comb).
