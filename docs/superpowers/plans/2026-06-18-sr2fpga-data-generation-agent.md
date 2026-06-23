# SR2FPGA Data Generation Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a first working SR2FPGA data generation agent that can create a Verilog RTL project package, run command-line checks, record attempts, parse Yosys-style resource stats, and export training views.

**Architecture:** Add a focused Python package under `LLM/src/sr2fpga_agent/`. V1 separates deterministic project scaffolding, command execution, log parsing, dataset recording, and orchestration so later LLM calls can replace the deterministic generator without changing the recorder or tool runner.

**Tech Stack:** Python standard library, `unittest`, subprocess-based command execution, JSON/JSONL files, Verilog/Yosys-compatible text artifacts.

---

## File Structure

- Create `LLM/src/sr2fpga_agent/__init__.py`: public package exports.
- Create `LLM/src/sr2fpga_agent/models.py`: dataclasses for requirements, tool results, labels, QoR, and attempts.
- Create `LLM/src/sr2fpga_agent/project_generator.py`: deterministic V1 generator for small RTL tasks, starting with counter.
- Create `LLM/src/sr2fpga_agent/tool_runner.py`: command runner and optional Verilator/Icarus/Yosys pipeline.
- Create `LLM/src/sr2fpga_agent/log_parser.py`: parse common failure types and Yosys `stat` output.
- Create `LLM/src/sr2fpga_agent/recorder.py`: create dataset sample directories, write attempts/final/eval files, export JSONL views.
- Create `LLM/src/sr2fpga_agent/agent.py`: high-level orchestration for generate -> run tools -> record sample.
- Create `LLM/src/sr2fpga_agent/cli.py`: command-line entry point for one sample.
- Create `LLM/tests/test_sr2fpga_agent_project_generator.py`: tests generated project content and manifest consistency.
- Create `LLM/tests/test_sr2fpga_agent_tooling.py`: tests command execution, missing tools, and log parsing.
- Create `LLM/tests/test_sr2fpga_agent_recorder.py`: tests dataset structure, trajectory, labels, measured QoR, and JSONL export.

## Task 1: Project Generator

**Files:**
- Create: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Create: `LLM/src/sr2fpga_agent/__init__.py`
- Create: `LLM/src/sr2fpga_agent/models.py`
- Create: `LLM/src/sr2fpga_agent/project_generator.py`

- [x] **Step 1: Write failing tests for a counter project package**

Create `LLM/tests/test_sr2fpga_agent_project_generator.py` with tests that instantiate `ProjectGenerator`, generate an 8-bit counter project, and assert:

- `system_his.json`, `manifest.json`, `rtl/top.v`, `constraints/timing.sdc`, `sim/tb_top.v`, and `reports/predicted_qor.json` exist in the returned in-memory package.
- `manifest.json` top module matches the Verilog module name.
- The testbench instantiates the top module.
- `predicted_qor.json` contains predicted LUT, FF, BRAM, DSP, Fmax, confidence, and assumptions fields.

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator -q
```

Expected: fail with `ModuleNotFoundError` for `LLM.src.sr2fpga_agent`.

- [x] **Step 2: Implement minimal project generator**

Create the package and implement:

```python
ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
ProjectGenerator.generate(request, platform) -> GeneratedProject
```

`GeneratedProject.files` should be a dictionary from relative path to text content. The generated Verilog must define `module top(...)` with `clk`, `rst_n`, `en`, and `count` ports.

- [x] **Step 3: Run generator tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator -q
```

Expected: pass.

## Task 2: Tool Runner And Log Parser

**Files:**
- Create: `LLM/tests/test_sr2fpga_agent_tooling.py`
- Create: `LLM/src/sr2fpga_agent/tool_runner.py`
- Create: `LLM/src/sr2fpga_agent/log_parser.py`

- [x] **Step 1: Write failing tests for command execution and parsing**

Create tests that assert:

- `CommandRunner.run(["python3", "-c", "print('ok')"])` returns exit code `0` and stdout containing `ok`.
- A missing executable returns a `ToolResult` with `status == "missing_tool"` and does not raise.
- `classify_failure("Unknown module type: foo")` returns `module_not_found`.
- `parse_yosys_stats()` extracts LUT/FF-like cell counts from a small synthetic Yosys `stat` log.

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_tooling -q
```

Expected: fail with missing modules/functions.

- [x] **Step 2: Implement command runner and parser**

Implement `ToolResult`, `CommandRunner`, `classify_failure`, and `parse_yosys_stats`.

`CommandRunner.run()` should accept command list, cwd, timeout seconds, and stage name. It should capture stdout/stderr, return duration, and report missing tools without throwing.

- [x] **Step 3: Run tooling tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_tooling -q
```

Expected: pass.

## Task 3: Recorder

**Files:**
- Create: `LLM/tests/test_sr2fpga_agent_recorder.py`
- Create: `LLM/src/sr2fpga_agent/recorder.py`

- [x] **Step 1: Write failing tests for dataset recording**

Create tests using `tempfile.TemporaryDirectory()` that:

- Save `sample_000001/requirement.txt` and `platform_profile.json`.
- Save `attempts/attempt_000/generated_project/...`.
- Save `attempts/attempt_000/eval/lint.log`.
- Save `attempts/attempt_000/diagnosis.json` and `patch.diff` for a failed attempt.
- Save `final/generated_project/...`.
- Save `eval/labels.json`, `eval/measured_qor.json`, `eval/tool_versions.json`, and `eval/trajectory.json`.
- Export `requirement_to_his.jsonl` and `failure_to_patch.jsonl`.

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected: fail with missing recorder module.

- [x] **Step 2: Implement dataset recorder**

Implement `DatasetRecorder` with methods:

- `start_sample(sample_id, requirement, platform_profile)`
- `write_attempt(sample_id, attempt)`
- `write_final(sample_id, generated_project, labels, measured_qor, tool_versions, trajectory)`
- `export_training_views(dataset_root, output_dir)`

Write JSON with `ensure_ascii=False` and stable indentation.

- [x] **Step 3: Run recorder tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected: pass.

## Task 4: Agent Orchestration And CLI

**Files:**
- Create: `LLM/src/sr2fpga_agent/agent.py`
- Create: `LLM/src/sr2fpga_agent/cli.py`
- Modify: `LLM/README.md`
- Test: `LLM/tests/test_sr2fpga_agent_recorder.py`

- [x] **Step 1: Write failing orchestration test**

Extend recorder tests to instantiate `DataGenerationAgent` with a fake runner that returns successful lint, simulation, and synthesis results. Assert that `run_one()` creates a sample with pass level `L3`, `trajectory.json`, and `measured_qor.json`.

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected: fail because `DataGenerationAgent` is missing.

- [x] **Step 2: Implement orchestration**

Implement `DataGenerationAgent.run_one()` to:

1. Generate project files.
2. Run lint, simulation, and synthesis stages through the runner.
3. Parse measured QoR from synthesis stdout.
4. Build L0-L3 labels.
5. Record attempt and final sample.

Use a maximum of one attempt for V1 scaffolding. Repair-loop implementation can be added after the runner/recorder shape is stable.

- [x] **Step 3: Implement CLI**

Create a CLI that supports:

```bash
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_000001 \
  --task-type counter \
  --width 8 \
  --project-name counter_8bit
```

The CLI should print the sample directory and pass level.

- [x] **Step 4: Document V1 usage**

Add a short section to `LLM/README.md` explaining the lightweight data generation agent and noting that Verilator/Icarus/Yosys must be installed for real tool execution.

- [x] **Step 5: Run orchestration tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected: pass.

## Task 5: Verification

**Files:**
- No new files.

- [x] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator \
  LLM.tests.test_sr2fpga_agent_tooling \
  LLM.tests.test_sr2fpga_agent_recorder \
  -q
```

Expected: pass.

- [x] **Step 2: Run existing lightweight dataset tests that do not require PyYAML**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_prepare_dataset \
  LLM.tests.test_serving_entrypoints \
  -q
```

Expected: pass.

- [x] **Step 3: Run full unittest discovery and record known environment issue**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Expected in the current local environment: fail only if `yaml` is unavailable for `test_training_smoke_assets`.

- [x] **Step 4: Inspect git diff**

Run:

```bash
git diff --stat
git status --short
```

Expected: only planned agent files and docs changed, plus pre-existing untracked files left untouched.
