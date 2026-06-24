# SR2FPGA System-HIS v1.2 Top-Down Design

## Status

Prototype design (2026-06-24), now under smoke-test implementation. This is a
focused trial of a more engineer-like System-HIS shape before migrating the
main clean training split.

## Motivation

The current `system-his-v1.1` schema proved useful for L0 package checking, but
it mixes several concepts:

- module definition and module instance;
- structural role and semantic kind;
- top-level interface and internal ports;
- data movement and control rules;
- architectural state and incidental RTL temporaries.

This causes exactly the failures seen around T3/T4. For example, a dual-stream
join has two `skid_buffer` instances, but v1.1 can make it unclear whether a
connection endpoint should name the reusable module definition or the concrete
instance. A senior FPGA engineer would not start there. The natural design
process is top-down:

```text
top interface
-> clock/reset and parameters
-> architectural state
-> submodule boundaries
-> data flow
-> control flow
-> verification and implementation constraints
```

System-HIS v1.2 should encode that process.

## Position Among IRs

System-HIS is a requirement-level architecture contract IR. It is not a
replacement for FIRRTL, CIRCT, MLIR hardware dialects, Calyx, or RTL ASTs.

```text
simple user prompt
-> System-HIS v1.2 top-down architecture contract
-> Verilog RTL project
-> optional lowering / checking against lower hardware IRs
-> lint / sim / synth / P&R / board
```

Design borrowings:

- From FIRRTL/CIRCT: modules, ports, parameters, hierarchy, and possible
  lowering boundaries.
- From Calyx: separate datapath movement from control sequencing.
- From IP-XACT-like practice: components, instances, interfaces, parameters,
  and file artifacts are first-class.
- From FPGA architecture practice: clock/reset, protocols, CDC, timing, QoR,
  and testbench acceptance are first-class.

## Scope For This Trial

Included:

- Define `system-his-v1.2-topdown` as a prototype schema.
- Cover T1-T4 component topologies, with T4 as the pressure test.
- Keep the IR architecture-level, not RTL-level.
- Add one hand-written T4 example.

Excluded for now:

- Replacing all v1.1 generation paths in the runner.
- Migrating old dataset samples.
- Replacing the project-level v1.1 L0 checker for legacy/v1.1 samples.
- Full behavioral semantics or formal properties.

Current implementation note:

- `LLM/src/sr2fpga_agent/system_his_v12_checker.py` implements a standalone
  v1.2 structural checker for REQ2HIS output.
- `LLM/src/sr2fpga_agent/deepseek.py` includes `DeepSeekSystemHisGenerator`,
  which asks DeepSeek for only the v1.2 architecture contract and validates it
  before returning it.
- `DeepSeekHisProjectGenerator` then accepts a checked v1.2 contract and asks
  DeepSeek for the complete project package while requiring the returned
  `system_his.json` to remain valid v1.2.
- CLI/runner provider construction exposes the two-stage path as
  `deepseek-his-v12`.
- `LLM/src/sr2fpga_agent/system_his_checker.py` dispatches
  `schema_version: system-his-v1.2-topdown` projects to the v1.2 checker before
  basic artifact-contract checks, while preserving v1.1 checks for existing
  paths.
- `LLM/src/sr2fpga_agent/rtl_identifier_checker.py` runs after L0 and before
  Verilator lint to catch target-language lexical failures such as Verilog
  reserved keywords used as generated RTL identifiers.
- Two-stage generation emits `generation_stage_started`,
  `generation_stage_finished`, and `generation_stage_failed` events for
  `req2his` and `his2project`, including sample metadata and stage latency in
  runner `events.jsonl`.
- `configs/sr2fpga_his_v12_smoke.example.yaml` is the current narrow smoke path
  for `simple_prompt -> System-HIS v1.2 -> project -> local tools`.

## Core Shape

```json
{
  "schema_version": "system-his-v1.2-topdown",
  "intent": {},
  "top": {},
  "state": {},
  "components": [],
  "instances": [],
  "data_flow": [],
  "control_flow": [],
  "timing": {},
  "resources": {},
  "verification": {},
  "artifacts": {}
}
```

The schema is intentionally ordered the way an FPGA architect would reason
about the design.

## Field Design

### intent

Purpose: preserve the user-level request separately from the expanded
engineering contract.

Required fields:

- `user_prompt`: short natural-language prompt.
- `design_goal`: expanded one-sentence black-box goal.
- `assumptions`: explicit assumptions added by the system.

### top

Purpose: define the design boundary before any submodule decisions.

Required fields:

- `name`: top module name.
- `parameters`: top-level parameters.
- `clocks`: clock ports and target frequencies.
- `resets`: reset ports, polarity, and sync/async kind.
- `ports`: full top-level port list.
- `interfaces`: protocol-grouped top-level ports.

`interfaces` should group ports into engineering concepts such as
`valid_ready`, `register`, `axi_stream`, or `axi_lite`. This avoids treating
ports as unrelated strings.

### state

Purpose: record architectural state, not every RTL temporary variable.

Required groups:

- `registers`: persistent architectural registers.
- `counters`: counters with update conditions.
- `fsms`: named FSMs and state sets.
- `buffers`: FIFOs, skid buffers, queues, or occupancy state.
- `memories`: RAMs/register files if present.

This field should answer: what state must exist for the architecture to work?

### components

Purpose: define reusable module definitions.

Required fields per component:

- `name`: RTL module definition name.
- `semantic_kind`: engineer-level role such as `stream_buffer`,
  `stream_join`, `accumulator`, `output_stage`, or `counter_core`.
- `source`: expected RTL file.
- `parameters`: declared parameter names and defaults.
- `ports`: component port contract.
- `intent`: one-line component responsibility.

`semantic_kind` replaces the old overloaded `role` concept.

### instances

Purpose: define concrete instantiated blocks.

Required fields per instance:

- `name`: instance name in the integration wrapper.
- `component`: referenced component definition.
- `parameter_values`: concrete parameter overrides.
- `clock`: clock domain.
- `reset`: reset domain.
- `owns_state`: state entries owned by this instance.

Connections and flows must reference instances, not component definitions.

### data_flow

Purpose: describe payload movement at architecture level.

Required fields per flow:

- `name`: flow name.
- `path`: ordered endpoint list such as `top.in0_data`,
  `in0_buffer.out_data`, `join_core.in0_data`.
- `payload`: width and meaning.
- `protocol`: protocol carried by the flow.
- `latency`: optional min/max latency.

This is not a netlist. It is a readable architecture trace of where data moves.

### control_flow

Purpose: describe when state updates and when data is allowed to move.

Allowed rule kinds for the first prototype:

- `reset_rule`
- `handshake_rule`
- `enable_rule`
- `stall_rule`
- `counter_update`
- `fsm_transition`
- `buffer_occupancy`

Required fields per rule:

- `name`
- `kind`
- `condition`
- `effects`
- `related_state`
- `related_flows`

Control rules should be template-like and checkable enough to guide generation,
but not so detailed that System-HIS becomes another HDL.

### timing

Purpose: capture FPGA timing intent and constraint artifacts.

Required fields:

- `primary_clock`
- `target_fmax_mhz`
- `constraints`

### resources

Purpose: capture coarse resource intent and optimization target.

Required fields:

- `optimization_goal`: e.g. `area_first`, `speed_first`, `balanced`.
- `expected`: coarse LUT/FF/BRAM/DSP expectations.

### verification

Purpose: describe acceptance scenarios without writing the full testbench.

Required fields:

- `testbench`
- `scenarios`
- `pass_condition`

Scenarios should be concrete enough for testbench generation:

- stimulus;
- expected result;
- relevant flow/control rule.

### artifacts

Purpose: align System-HIS with the generated project package.

Required fields:

- `top_module`
- `rtl_sources`
- `testbench`
- `constraints`
- `manifest`
- `predicted_qor`

## Checker Strategy

The v1.2 checker should stay mostly structural:

1. `schema_version` equals `system-his-v1.2-topdown`.
2. Every instance references an existing component.
3. Instance names must be legal target-language identifiers; reserved keywords
   such as `fork`, `join`, and `buf` are rejected early.
4. Every `data_flow.path` endpoint names either `top.<port>` or
   `<instance>.<port>`.
5. Every `control_flow.related_state` entry exists in `state`.
6. Artifacts declare the expected top module, RTL source files, testbench,
   constraints, manifest, and predicted QoR report.
7. Project-level L0 then checks basic artifact presence and leaves deeper RTL
   lexical/lint/sim/synth validation to later pipeline stages.

Later checks can validate protocol-specific shapes, latency claims, and simple
reset/hold behavior, but v1.2 should not begin with a full semantic checker.

## Compatibility Plan

Keep existing dataset files, but label them explicitly:

- missing `schema_version`: `legacy`.
- current checked format: `system-his-v1.1`.
- new clean split: `system-his-v1.2-topdown`.

Do not mix legacy/v1.1/v1.2 as the same REQ-to-HIS training target. A migration
view may map old data into v1.2 for diagnostics, but the migrated view should be
marked as derived.

## Success Criteria For The Trial

The trial is promising if:

- T4 dual-stream join can be expressed without ambiguous module-vs-instance
  endpoints.
- The state list is compact and architecture-level.
- Data flow and control flow make the design easier to review than v1.1
  `modules + connections`.
- A minimal checker could validate structure without solving full behavior.

The trial should be rejected or revised if:

- The example becomes as verbose as RTL.
- Control rules require arbitrary HDL-like expressions everywhere.
- The schema cannot represent repeated component instances cleanly.
- It loses the ability to map back to files, testbench, manifest, and tools.
