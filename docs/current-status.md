# SR2FPGA Current Status - 2026-06-24

## Current Branch

`codex/sr2fpga-data-agent`

## Current Focus

Build and harden the SR2FPGA tool-verified dataset factory:

```text
requirement
-> System-HIS
-> multi-file Verilog RTL project
-> open-source EDA labels
-> diagnosis / patch trajectories
-> trainable JSONL views
```

The current engineering slice is autonomous runner hardening for natural LLM
failure collection. Synthetic failure injection exists as a pipeline test and
controlled-ablation aid, not as the main repair-learning data source.

## Current Code State

Implemented and under active review:

- Autonomous batch runner in `LLM/src/sr2fpga_agent/runner.py`.
- Runner task config supports per-task `source`, `difficulty_tier`,
  `failure_origin`, `measurement_point`, `requirement_style`, and
  `failure_injectors`.
- Runner accepts the current measurement points:
  `a_first_attempt_no_tools`, `b_tool_in_loop_repair`, and
  `c_finetuned_first_attempt_no_tools`.
- Runner now dispatches each sample through its configured source instead of
  only the global provider.
- `run_state.json` records a config fingerprint; resume rejects attempts to
  reuse the same run ID with a different config, which keeps baseline
  calibration runs reproducible.
- Runner supports `task_type: component_topology` with `topology_ids`, expanding
  topology selections into concrete `composed_*` tasks while preserving
  `topology_id` in sample metadata.
- `configs/sr2fpga_baseline_a.example.yaml` is the first-attempt/no-repair
  baseline (a) entry point for DeepSeek over the current T1-T4 component
  topologies. It uses `requirement_style: natural_component`, a deterministic
  surface rewrite that preserves topology contracts while making prompts read
  more like engineering requirements. It also declares `env_file: .env`, letting
  the runner load an ignored local DeepSeek key file automatically when present.
  `configs/sr2fpga_agent.example.yaml` remains the tool-loop repair smoke path.
- A real baseline (a) run completed against DeepSeek with the local ignored
  `.env` key. `--preflight --validate-provider` confirmed provider auth before
  spending generation calls. The run ID is `deepseek-baseline-a`.
- Baseline (a) generated four natural-component DeepSeek samples over T1-T4.
  All four were recorded as `repair_trajectory` with pass level `L0` because
  DeepSeek generated incomplete/non-v1.1 `system_his.json` and manifest
  structures. This is a valid natural project-generation failure family for
  SR2FPGA repair, not merely noise: the model produced an incomplete FPGA
  project package even when some RTL files were present.
- `configs/sr2fpga_baseline_b.example.yaml` is the tool-in-loop repair
  baseline (b) entry point for the same T1-T4 natural-component tasks. It uses
  `repair_provider: deepseek`, `max_attempts: 4`, measurement point
  `b_tool_in_loop_repair`, and `sample_id_prefix: baseline_b` so baseline (a)
  and (b) can coexist in one dataset root without sample ID collisions.
- A real baseline (b) run completed against DeepSeek with run ID
  `deepseek-baseline-b`. It completed four samples, each with four L0 attempts:
  `failure_types.l0_contract_violation = 16`, `success_l3 = 0`,
  `repair_trajectory = 4`, `rejected = 0`. This proves the tool-in-loop repair
  path is wired and repair patches are recorded, but the first repair prompt was
  still not precise enough to pass the strict System-HIS/manifest L0 checker.
- Post-run diagnosis showed DeepSeek repair moved in the right direction:
  it expanded tiny/legacy `system_his.json` files into large v1.1-like
  structures and changed manifest constraints toward the checker shape. The
  remaining L0 errors were schema-detail mismatches: `role` must be exactly
  `top`/`submodule`, modules need `clock` not `clock_domain`, `parameters` and
  `params` must both exist and match exactly, QoR resource values must be
  non-negative integers, verification needs `checks` and `test_pass_means`,
  connection protocol must be one of the checker-approved values, and
  `manifest.constraints.timing` must be present. The repair prompt has now been
  tightened to include those checker-level details.
- `configs/sr2fpga_baseline_b_smoke.example.yaml` is the tightened-prompt
  baseline (b) smoke run for T1/T2 only. It uses `sample_id_prefix:
  baseline_b_smoke` to keep smoke data separate from full baseline runs.
- A real tightened-prompt smoke run completed with run ID
  `deepseek-baseline-b-smoke`: `total_completed = 2`, `success_l3 = 2`,
  `repair_trajectory = 0`, `rejected = 0`. Both samples began from natural
  DeepSeek failures and were repaired to L3 under the tool loop:
  - T1 `event_counter`: L0 -> L0 -> L3.
  - T2 `stream_accumulator`: L0 -> L1/lint failure -> L3.
  This proves the baseline (b) repair path can repair project-package failures
  across L0 and continue into RTL/tool repair when the prompt is aligned with
  the checker.
- `configs/sr2fpga_baseline_b_tightened.example.yaml` is the full T1-T4
  tightened-prompt baseline (b) rerun. It uses `sample_id_prefix:
  baseline_b_tightened` to preserve the earlier failed full baseline (b) run.
- A real full tightened baseline (b) run completed with run ID
  `deepseek-baseline-b-tightened`: `total_completed = 4`, `success_l3 = 2`,
  `repair_trajectory = 2`, `rejected = 0`. T1 and T2 repaired to L3; T3 and T4
  remained repair trajectories. The observed repair knee is T3:
  - T1 `event_counter`: repaired to L3 after two L0 failures.
  - T2 `stream_accumulator`: repaired to L3 after two L0 failures.
  - T3 `stream_fork`: crossed L0 but final attempt failed Verilator lint because
    `rtl/top.v` used the Verilog reserved keyword `fork` as an instance name.
  - T4 `dual_stream_join`: remained at L0; final System-HIS still used
    instance aliases such as `sb0`, `join`, `acc`, and `stg` as connection
    endpoint module names, and simplified parameterized widths instead of the
    exact parsed RTL ranges such as `[DATA_WIDTH-1:0]`.
- The repair prompt has been tightened again after the full run to explicitly
  forbid Verilog reserved keywords as instance names, require System-HIS
  connection endpoints to use declared module names rather than instance
  aliases, and require width strings to match parsed RTL ranges exactly.
- `configs/sr2fpga_baseline_b_t3_t4_smoke.example.yaml` is the narrow repair-knee
  smoke run for T3/T4 only. It uses `sample_id_prefix:
  baseline_b_t3_t4_smoke`.
- A real T3/T4 narrow smoke run completed with run ID
  `deepseek-baseline-b-t3-t4-smoke`: `total_completed = 2`, `success_l3 = 0`,
  `repair_trajectory = 2`, `rejected = 0`. The newest prompt changes moved T4
  forward from L0 to L1 but did not reach L3:
  - T3 `stream_fork`: remained at L0; final errors were equivalent width
    notation mismatches such as `[7:0]` versus `8` and top-port mismatch.
  - T4 `dual_stream_join`: crossed L0 and lint, then failed simulation with
    `TEST_FAIL: out_data=xx`.
- L0 checker width normalization now treats numeric ranges like `[7:0]` as
  equivalent to integer width `8`. This addresses the T3 narrow-smoke residual
  failure without loosening parameterized ranges such as `[DATA_WIDTH-1:0]`.
- Manual side evaluation of the generated RTL, used only as deeper diagnostic
  labeling, showed additional failure signals inside the same generated
  projects:
  - T1 `event_counter`: compiles and testbench prints `TEST_PASS`.
  - T2 `stream_accumulator`: compiles but testbench prints `TEST_FAIL`.
  - T3 `stream_fork`: compiles but testbench reports many data mismatches and
    prints `TEST_FAIL`.
  - T4 `dual_stream_join`: fails Verilog compilation in `stream_stage.v`.
  This means the current DeepSeek baseline is already valuable as natural
  project-level repair data. The measurement pipeline should keep L0
  artifact/schema failures as first-class labels while optionally adding
  deeper L1/L2/L3 side labels for the RTL files that were generated.
- Runner supports `--preflight` to check planned sample count, DeepSeek API-key
  environment readiness, HDL tool availability, and existing run-directory state
  before spending API calls on baseline (a). The preflight JSON also includes a
  planned sample preview with source, task type, requirement style, requirement
  text, difficulty tier, topology ID, failure origin, and measurement point for
  each sample. It reports the `DEEPSEEK_API_KEY` source and a short non-secret
  fingerprint so local `.env` key updates can be confirmed before a DeepSeek
  run. With `--validate-provider`, preflight makes a minimal DeepSeek
  authentication request, catching invalid keys before any RTL sample is
  attempted. The component-topology requirements expose nodes, required edges,
  and expected behavior for prompt audit.
- Runner summaries now include `metadata_breakdown`, `pass_level_breakdown`,
  `failure_family_breakdown`, and `calibration_matrix` for source, failure
  family, failure origin, requirement style, difficulty tier, topology ID,
  measurement point, pass-level counts, L3 pass-rate calibration, L0
  contract-failure counts, and grouped cross-file consistency error rates.
  `l0_contract_violation` is reported as the first-class project-generation
  family `artifact_contract_failure`. Stage-aware family mapping now classifies
  unknown `lint` and `sim_compile` failures as `rtl_compile_failure`, `sim_run`
  failures as `rtl_sim_failure`, and `synth` failures as `synth_failure`, while
  preserving the raw fine-grained `failure_type`.
- Runner summaries also include `contract_metrics`, including total labeled
  samples, L0 contract failures, and cross-file consistency error rate.
- `LLM/src/sr2fpga_agent/baseline_report.py` renders runner `summary.json`
  into a compact Markdown table for baseline (a), grouped by source, failure
  origin, requirement style, difficulty tier, topology ID, and measurement
  point. Runner now writes this table automatically as `baseline_report.md` in
  each run directory and flags the first difficulty tier below the default 80%
  L3 pass-rate knee threshold.
- Sample metadata is written to `metadata.json` and copied into all exported
  JSONL training views.
- L0 is now a real System-HIS/manifest consistency check before HDL tools run:
  `LLM/src/sr2fpga_agent/system_his_checker.py`.
- System-HIS v1.1 now includes explicit `project`, `clocks`, `resets`,
  `modules`, port-level `connections`, `top_ports`, and `qor_intent` records.
  L0 checks module names, roles, sources, parameters, port-list shape, RTL
  declaration coverage, top-port coverage, port direction and width agreement,
  connection endpoint modules, connection endpoint ports, connection protocol,
  connection width, CDC flags, testbench top-module instantiation,
  verification acceptance fields, clock/reset/QoR intent structure, and SDC
  `get_ports` references.
  Connection widths may be concrete integers or parameterized expressions.
- System-HIS module records now capture top-level instance parameter overrides,
  clock/reset domain names, spec-style `params`, and one-line intent strings;
  L0 rejects missing module intent and parameters that are not declared by the
  RTL module. L0 also normalizes numeric range widths like `[7:0]` to `8` when
  comparing System-HIS against parsed RTL port widths.
- System-HIS v1.2 freeze Task 1 is implemented: shared RTL-introspection helpers
  now live in `LLM/src/sr2fpga_agent/rtl_introspect.py`, and the v1.1
  project-level L0 checker imports them instead of carrying private duplicate
  parsing logic. This keeps the existing v1.1 checker behavior intact while
  giving the upcoming canonical v1.2 cross-check a shared parser foundation.
- A standalone System-HIS v1.2 structural checker now exists for the
  REQ2HIS stage: `LLM/src/sr2fpga_agent/system_his_v12_checker.py`. It validates
  the canonical `system-his-v1.2` JSON shape independently of RTL files,
  including required sections, component-to-instance references, instance-owned
  state, data-flow endpoints, control-flow state/flow references, and artifact
  fields. It also rejects Verilog reserved keywords such as `fork` and `join`
  as concrete instance names, because those IR identifiers become illegal RTL
  identifiers during lowering.
- System-HIS v1.2 freeze Task 2 is implemented: the canonical schema string is
  now exactly `system-his-v1.2`; the retired `system-his-v1.2-topdown` suffix is
  rejected by the v1.2 checker and should be treated as historical prototype
  data.
- System-HIS v1.2 freeze Task 3 is implemented: `data_flow[*].timing` remains
  optional, but when present the checker now requires `latency_cycles` to be a
  non-negative integer, `initiation_interval` to be a positive integer, and
  optional `throughput` to be a non-empty string.
- System-HIS v1.2 freeze Task 4 is implemented for structured control rules:
  `state.fsms` now validates declared states plus `initial`/`reset_state`, and
  structured `fsm_transition`/`enable_rule` entries validate guard operators,
  declared guard signals, effect targets, and guard nesting depth <= 2. The
  canonical T4 fixture now includes a structured FSM/guard example.
- System-HIS v1.2 freeze Task 5 is implemented: the v1.2 checker now exposes
  `check_system_his_v12_against_rtl(payload, project)`, which runs IR checks and
  then cross-checks RTL module declarations, top/component port name, direction,
  semantic width equivalence, top-level instance presence, data-flow endpoints,
  manifest/source alignment, testbench top instantiation, SDC `get_ports`, and
  FSM state-name presence where FSMs are declared.
- System-HIS v1.2 freeze Task 6 is implemented: project-level
  `check_project_l0(project)` now routes canonical `system-his-v1.2` projects
  through the v1.2 HIS↔RTL cross-check instead of only the standalone IR checker.
  This makes v1.2 L0 labels sensitive to cross-file consistency before Verilator
  or simulation runs.
- System-HIS v1.2 freeze Tasks 7a/7b are implemented: deterministic
  `ProjectGenerator` now emits canonical `system-his-v1.2` for all supported
  single-module, multi-module, and composed topology families. Deterministic
  v1.2 output carries the required aspect sections and passes project-level L0.
  Streaming/composed streaming families include `data_flow.timing` plus
  `handshake_rule`/`stall_rule` control entries.
- System-HIS v1.2 freeze Task 8 is implemented: the DeepSeek REQ2HIS prompt now
  asks for canonical v1.2, optional `data_flow.timing`, structured
  `control_flow` `when/effect` rules, guard grammar, and guard depth <= 2.
- System-HIS v1.2 freeze Task 9 is implemented: runner metadata derives
  `training_split` from `system_his_schema_version`; v1.2 samples are `clean`,
  and legacy/v1.1 samples are `quarantine`. Recorder exports backfill this field
  for older metadata at export time.
- The first DeepSeek REQ2HIS entry point now exists in
  `LLM/src/sr2fpga_agent/deepseek.py`: `DeepSeekSystemHisGenerator`,
  `parse_system_his_v12`, and `_system_his_v12_messages`. This stage asks
  DeepSeek to produce only a `system-his-v1.2` architecture contract
  from a short user prompt, validates it with the standalone checker before
  returning it, and feeds checker errors back to DeepSeek for bounded retry.
- The matching DeepSeek HIS2PROJECT entry point also now exists:
  `DeepSeekHisProjectGenerator` and `_his_project_messages`. This stage takes a
  checked `system-his-v1.2` contract, asks DeepSeek for a complete
  project package, validates the generated project files with the existing
  project parser, and additionally requires the returned `system_his.json` to
  remain valid v1.2.
- CLI/runner provider construction now exposes the two-stage chain as
  `deepseek-his-v12`, implemented by `DeepSeekTwoStageProjectGenerator`.
  Runner preflight treats this provider as a DeepSeek-backed source for API-key
  and auth diagnostics. A narrow T4 smoke config is available at
  `configs/sr2fpga_his_v12_smoke.example.yaml`.
- The project-level L0 checker now dispatches
  `schema_version: system-his-v1.2` files to the v1.2 checker and then
  verifies the basic project artifact contract. This lets the two-stage path
  reach RTL lint instead of being rejected by the older v1.1 schema checker.
- Runner task requirements now support `requirement_style: simple_prompt`. This
  gives the v1.2 two-stage path a true short user-intent input instead of the
  long benchmark-contract prompt used by `natural_component`.
- The first v1.2 smoke run that reached project L0 was `his-v12-smoke-6`.
  It completed one T4 `simple_prompt` sample with `pass_level_breakdown.L0 = 1`,
  `contract_metrics.l0_contract_failures = 0`, and
  `failure_family_breakdown.rtl_compile_failure = 1`. The failure was no longer
  a System-HIS/package-contract issue: Verilator rejected `rtl/top.v` because
  the model used the reserved keyword `join` as an instance name. The canonical
  T4 v1.2 example and REQ2HIS prompt now use `join_core` instead.
- Follow-up v1.2 smoke runs confirm the issue moved down a layer:
  - `his-v12-smoke-7` used `join_core`, passed v1.2 L0, and failed Verilator
    lint because `-Wall` treated unused `clk`, `rst_n`, and `m_tready` signals
    as fatal warnings.
  - `his-v12-smoke-8` verified fixed metadata
    (`system_his_schema_version: system-his-v1.2-topdown`) and again passed
    v1.2 L0, then failed Verilator lint because `rtl/skid_buffer.v` used `buf`
    as an internal array name. `buf` is a Verilog primitive keyword, so this is
    now recorded as a target-language lexical lowering failure.
- A lightweight RTL identifier precheck now runs between L0 and Verilator lint.
  It records a `rtl_identifier_check` trajectory stage, rejects generated RTL
  identifiers that collide with Verilog reserved keywords, and classifies these
  as `rtl_reserved_identifier` under the `rtl_compile_failure` family.
- `his-v12-smoke-9` (`sample_id_prefix: his_v12_smoke_v5`) verifies the new
  precheck path: the sample passed `rtl_identifier_check`, then failed
  Verilator lint with `failure_type: lint_warning_as_error` because
  `rtl/top.v` declared an unused/undriven `out_ready_out` wire. This indicates
  the current v1.2 T4 frontier has moved from lexical legality to strict lint
  hygiene and dead-signal cleanup.
- Two-stage DeepSeek generation now emits stage-level events into runner
  `events.jsonl` for `req2his` and `his2project`, including start, finish,
  failure, sample metadata, and `duration_seconds`.
- `his-v12-smoke-10` (`sample_id_prefix: his_v12_smoke_v6`) verifies the event
  path on a real T4 run. `events.jsonl` recorded `req2his` as about 62.2
  seconds and `his2project` as about 70.7 seconds before the sample completed.
  The generated project again passed `rtl_identifier_check` and failed
  Verilator lint with `failure_type: lint_warning_as_error`, this time due to
  an unused/undriven `staged_ready` wire in `rtl/top.v`.
- Runner metadata now derives `system_his_schema_version` from the sample
  source/provider, so `deepseek-his-v12` samples are labeled
  `system-his-v1.2` instead of the older hard-coded v1.1 marker. Earlier
  `system-his-v1.2-topdown` smoke metadata is historical prototype data.
- Tool-log classification now includes `lint_warning_as_error` for Verilator
  warning-only lint exits, while reserved-keyword syntax failures remain
  `syntax_error`.
- First deterministic component-topology benchmark set:
  `composed_event_counter` (T1 event-gate-to-counter topology) and
  `composed_stream_accumulator` (T2 skid-buffer-to-accumulator topology), and
  `composed_stream_fork` (T3 skid-buffer-to-fork-to-dual-stage valid-ready
  topology), and `composed_dual_stream_join` (T4 dual-skid-buffer stream join
  into accumulator and output stage), all with explicit `architecture.topology`
  nodes/edges and port-level System-HIS connections.
- Deterministic System-HIS output now declares `schema_version:
  system-his-v1.2`.
- Synthetic failure injector module:
  - `LLM/src/sr2fpga_agent/failure_injector.py`
  - `LLM/tests/test_sr2fpga_agent_failure_injector.py`

Supported failure injectors:

- `rename_reset_port`
- `missing_manifest_source`
- `wrong_top_module`
- `width_mismatch`
- `testbench_expected_value_mismatch`
- `constraint_missing_clock`
- `multimodule_connection_mismatch`

## Latest Verification

Fresh verification from the latest implementation pass:

```bash
python3 -m unittest discover -s LLM/tests -q
# Ran 190 tests - OK

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_a.example.yaml --run-id deepseek-baseline-a --preflight --validate-provider
# ok: true; DEEPSEEK_API_KEY source: .env; provider_auth.deepseek.status: ok

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_a.example.yaml --run-id deepseek-baseline-a
# total_completed=4; success_l3=0; repair_trajectory=4; rejected=0

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b.example.yaml --run-id deepseek-baseline-b --preflight --validate-provider
# ok: true; planned_samples: 4; measurement_point: b_tool_in_loop_repair

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b.example.yaml --run-id deepseek-baseline-b
# total_completed=4; success_l3=0; repair_trajectory=4; rejected=0

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b_smoke.example.yaml --run-id deepseek-baseline-b-smoke --preflight --validate-provider
# ok: true; planned_samples: 2; measurement_point: b_tool_in_loop_repair

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b_smoke.example.yaml --run-id deepseek-baseline-b-smoke
# total_completed=2; success_l3=2; repair_trajectory=0; rejected=0

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b_tightened.example.yaml --run-id deepseek-baseline-b-tightened --preflight --validate-provider
# ok: true; planned_samples: 4; measurement_point: b_tool_in_loop_repair

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b_tightened.example.yaml --run-id deepseek-baseline-b-tightened
# total_completed=4; success_l3=2; repair_trajectory=2; rejected=0

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b_t3_t4_smoke.example.yaml --run-id deepseek-baseline-b-t3-t4-smoke --preflight --validate-provider
# ok: true; planned_samples: 2; measurement_point: b_tool_in_loop_repair

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_baseline_b_t3_t4_smoke.example.yaml --run-id deepseek-baseline-b-t3-t4-smoke
# total_completed=2; success_l3=0; repair_trajectory=2; rejected=0

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_his_v12_smoke.example.yaml --run-id his-v12-smoke-8 --preflight
# ok: true; planned_samples: 1; source: deepseek-his-v12; requirement_style: simple_prompt

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_his_v12_smoke.example.yaml --run-id his-v12-smoke-8 --no-resume
# total_completed=1; success_l3=0; repair_trajectory=1; rejected=0
# pass_level_breakdown: L0:1; l0_contract_failures=0; failure_types.syntax_error=1

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_his_v12_smoke.example.yaml --run-id his-v12-smoke-9 --preflight
# ok: true; planned_samples: 1; source: deepseek-his-v12; sample_id_prefix: his_v12_smoke_v5

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_his_v12_smoke.example.yaml --run-id his-v12-smoke-9 --no-resume
# total_completed=1; success_l3=0; repair_trajectory=1; rejected=0
# pass_level_breakdown: L0:1; l0_contract_failures=0; failure_types.lint_warning_as_error=1

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_his_v12_smoke.example.yaml --run-id his-v12-smoke-10 --preflight
# ok: true; planned_samples: 1; source: deepseek-his-v12; sample_id_prefix: his_v12_smoke_v6

python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_his_v12_smoke.example.yaml --run-id his-v12-smoke-10 --no-resume
# total_completed=1; success_l3=0; repair_trajectory=1; rejected=0
# events: req2his 62.2s; his2project 70.7s
# pass_level_breakdown: L0:1; l0_contract_failures=0; failure_types.lint_warning_as_error=1
```

Latest baseline report:

`tmp/sr2fpga_runs/deepseek-baseline-a/baseline_report.md`

Latest baseline (b) report:

`tmp/sr2fpga_runs/deepseek-baseline-b/baseline_report.md`

Latest baseline (b) tightened smoke report:

`tmp/sr2fpga_runs/deepseek-baseline-b-smoke/baseline_report.md`

Latest baseline (b) full tightened report:

`tmp/sr2fpga_runs/deepseek-baseline-b-tightened/baseline_report.md`

Latest baseline (b) T3/T4 narrow smoke report:

`tmp/sr2fpga_runs/deepseek-baseline-b-t3-t4-smoke/baseline_report.md`

Latest v1.2 two-stage smoke report:

`tmp/sr2fpga_runs/his-v12-smoke-8/baseline_report.md`

Latest v1.2 two-stage smoke report with RTL identifier precheck:

`tmp/sr2fpga_runs/his-v12-smoke-9/baseline_report.md`

Latest v1.2 two-stage smoke report with stage-level generation events:

`tmp/sr2fpga_runs/his-v12-smoke-10/baseline_report.md`

Key summary:

- Pass-rate knee: T1, because L3 pass rate is 0%.
- Primary failure family: `artifact_contract_failure` /
  `l0_contract_violation` for all four samples.
- Real report row: `failure_family | artifact_contract_failure | 4 | L0:4`.
- Interpretation: baseline (a) successfully collected natural project package
  failures from DeepSeek; these are in scope for failure repair, alongside RTL
  syntax, simulation, and synthesis failures.
- Metadata: `source=deepseek`, `failure_origin=natural_llm`,
  `requirement_style=natural_component`,
  `measurement_point=a_first_attempt_no_tools` for baseline (a) and
  `measurement_point=b_tool_in_loop_repair` for baseline (b).
- Tightened smoke result: no pass-rate knee observed above the 80% threshold;
  `failure_family | artifact_contract_failure | 2 | L3:2` and
  `failure_family | rtl_compile_failure | 1 | L3:1`.
- Full tightened result: pass-rate knee is T3; T1/T2 are L3, T3/T4 are L0.
  Overall `measurement_point | b_tool_in_loop_repair | 4 | L0:2, L3:2`.
- T3/T4 narrow smoke result: pass-rate knee remains T3; T3 is L0, T4 is L1.
  The T4 movement from L0 to L1 indicates the prompt changes improved project
  package repair, while the remaining frontier is RTL simulation semantics.
- v1.2 two-stage smoke result: the short prompt -> System-HIS v1.2 -> project
  path now clears the v1.2 project L0 contract for T4. The current frontier is
  RTL lint. The reserved-identifier precheck now catches lexical legality before
  Verilator; the newest observed failure is strict warning hygiene under
  Verilator `-Wall`.

## Dataset Policy

- The repo contains a milestone dataset snapshot under `datasets/`.
- Do not casually stage generated dataset additions, deletions, or run logs.
- Large future datasets should stay local by default.
- Commit compact summaries only when useful for research traceability.
- Never commit model weights, LoRA outputs, API keys, or local `.env` files.

## Next Recommended Work

0. **System-HIS v1.2 freeze (implemented; keep verifying before new data).** The freeze
   plan `docs/superpowers/plans/2026-06-24-sr2fpga-system-his-v1.2-freeze.md`
   (spec: `docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`).
   It makes `system-his-v1.2` canonical, migrates the deterministic generator off
   v1.1, gives the v1.2 checker HIS↔RTL cross-checks, adds `data_flow.timing` +
   structured `control_flow`, and quarantines legacy/v1.1 data. The code path is
   implemented and unit-verified; next work is to run a fresh deterministic and
   DeepSeek v1.2 smoke after this freeze before generating a larger clean split.
0b. **OpenXC7 L4 tool-stage spike (approved; run on the Windows+WSL2 box).**
   Plan `docs/superpowers/plans/2026-06-24-openxc7-l4-tool-stage-spike.md`
   (spec: `docs/superpowers/specs/2026-06-24-openxc7-l4-tool-stage-spike-design.md`).
   Adds OpenXC7 (Yosys synth_xilinx → nextpnr-xilinx → bitstream) as the L4 stage
   of the tool pipeline for batch, license-free post-P&R labels (real LUT/FF/BRAM/
   DSP + Fmax — closes the Finding-G vacuous-LUT issue). Independent of the v1.2
   freeze and the highest-value physical-implementation de-risk. Critical gate:
   XC7Z020 prjxray chipdb availability (Task 1). Batch L0–L4 runs on WSL2; L5 board
   load is a manual one-off via Vivado. Note: Task 3 edits `agent.py` `_run_pipeline`
   — coordinate with the v1.2 freeze's agent changes to avoid collision.
1. Treat L0 project-package failures as first-class repair targets: missing or
   malformed `system_his.json`, manifest structure drift, missing source lists,
   missing constraints, incomplete reports, and cross-file inconsistency all
   count as valid natural LLM failures.
2. Split reported failure families into at least `artifact_contract_failure`,
   `rtl_compile_failure`, `rtl_sim_failure`, and `synth_failure`, with L0 as
   the primary label when the raw project package is invalid.
3. Re-run a T3-only smoke after L0 numeric-width normalization to test whether
   `stream_fork` now crosses L0 and exposes the next real RTL failure stage.
4. Add attempt-level event logging so long DeepSeek repair runs expose progress
   after every attempt, not only after each sample completes.
5. Add an optional deep-diagnostic sidecar for baseline (a): preserve the raw
   L0 artifact failure label, but fill or normalize known metadata only in a
   separate diagnostic view so generated RTL can still receive L1/L2/L3 side
   labels when useful.
6. Run a larger DeepSeek baseline now that project-file failures are confirmed
   in scope, then expand variants around T1-T4 to estimate the natural failure
   distribution.
7. Keep synthetic failure injection disabled for main data collection and use
   it only for smoke tests, recorder/export validation, and controlled
   ablations.
8. Consider a deterministic L0 schema-normalizer repair as a separate tool-side
   baseline, then compare it against LLM-only repair.
9. Freeze a canonical System-HIS schema before the next clean training split.
10. Add stage-level event logging around REQ2HIS and HIS2PROJECT so long LLM
    calls expose progress, retry counts, and timeout/network failures. The
    basic start/finish/failure events are now implemented; retry-count
    aggregation remains to be added.
11. Extend the new Verilog identifier checker or add a sanitizer so it covers
    more generated RTL identifiers, including named blocks and generate labels.
12. Add strict-lint hygiene guidance or deterministic cleanup for unused and
    undriven signals such as the v5 `out_ready_out` failure.
13. Current data contains legacy/ad hoc `system_his.json` shapes as well as
    `system-his-v1.1`; keep legacy samples for traceability, but do not mix
    them with clean REQ-to-HIS training without migration labels.
14. **Fix training-data-quality issues before the first clean training split**
    (`docs/research-issues-training-data-quality-2026-06-24.md`). High priority:
    (F) `classify_failure` broad `reset`/`clock` single-word patterns produce
    noisy failure labels and make `synthesis_error`/`timing_risk` unreachable;
    (E) reconcile the failure-taxonomy names between the reframe spec and
    `log_parser.py` (spec should adopt existing `multiple_driver`/`latch_inferred`
    and add the missing seq/comb + CDC + backpressure classes). Medium:
    (G) L3 measured LUT is always 0 under the generic Yosys flow — use
    `synth_xilinx` or defer LUT to L4 before QOR_PRED; (C) add `pass_level` to
    QoR export rows so `project_to_measured_qor` can drop non-L3 partial rows.

## Important Pointers

- Primary research framing: `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
- Objective summary: `docs/research-objective-sr2fpga-tcad.md`
- Failure-repair research issue log: `docs/research-issues-failure-repair-2026-06-24.md`
- Training-data-quality issue log: `docs/research-issues-training-data-quality-2026-06-24.md`
- System-HIS v1.2 FREEZE spec (approved, canonical): `docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`
- System-HIS v1.2 FREEZE implementation plan (for codex): `docs/superpowers/plans/2026-06-24-sr2fpga-system-his-v1.2-freeze.md`
- OpenXC7 L4 tool-stage spike spec: `docs/superpowers/specs/2026-06-24-openxc7-l4-tool-stage-spike-design.md`
- OpenXC7 L4 tool-stage spike plan (run on Windows+WSL2): `docs/superpowers/plans/2026-06-24-openxc7-l4-tool-stage-spike.md`
- System-HIS v1.2 top-down prototype spec (superseded by the freeze): `docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md`
- System-HIS v1.2 T4 example: `docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json`
- Detailed handoff: `docs/sr2fpga-agent-handoff-2026-06-22.md`
- Runner design: `docs/superpowers/specs/2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`
- Baseline (a) runner config: `configs/sr2fpga_baseline_a.example.yaml`
- Baseline (b) runner config: `configs/sr2fpga_baseline_b.example.yaml`
- Baseline (b) smoke config: `configs/sr2fpga_baseline_b_smoke.example.yaml`
- Baseline (b) full tightened config: `configs/sr2fpga_baseline_b_tightened.example.yaml`
- Baseline (b) T3/T4 smoke config: `configs/sr2fpga_baseline_b_t3_t4_smoke.example.yaml`
- System-HIS v1.2 two-stage smoke config: `configs/sr2fpga_his_v12_smoke.example.yaml`
- Tool-loop runner config: `configs/sr2fpga_agent.example.yaml`
- Baseline report renderer: `LLM/src/sr2fpga_agent/baseline_report.py`
- Agent guidance: `CLAUDE.md`
- Multi-teacher source spec: `docs/superpowers/specs/2026-06-25-sr2fpga-multi-teacher-source-design.md`
- Multi-teacher source plan: `docs/superpowers/plans/2026-06-25-sr2fpga-multi-teacher-source.md`
- Multi-teacher runner config: `configs/sr2fpga_multi_teacher.example.yaml`
