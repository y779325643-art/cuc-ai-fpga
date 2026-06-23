# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

This is **SR2FPGA**: a TCAD-oriented EDA research project on *tool-verified learning for
system-requirement-to-FPGA RTL project generation*. The research objective in
`docs/research-objective-sr2fpga-tcad.md` is the north star — read it before any
engineering or writing work, and update it if the objective changes.

The framing matters and shapes design decisions:
- The problem is **NOT** `natural language -> Verilog`. It is
  `requirement -> System-HIS -> multi-file RTL project -> tool labels -> diagnosis/patch -> trainable dataset`.
- The generated artifact is a **multi-file project package**, never a single `.v` file.
- EDA tool feedback (Verilator/Icarus/Yosys, later Vivado/Quartus) is the objective supervision signal.
- Do not reframe this as a "LLM writes Verilog" demo, a prompt-engineering platform, or an
  acceleration-speedup paper. See the "What To Avoid" section of the objective doc.

The repo has two distinct halves:
1. `LLM/src/sr2fpga_agent/` — the **data generation agent** (a tool-calling dataset factory).
2. `LLM/` (configs/scripts/src) — **model deployment & fine-tuning** infra (vLLM serving + LoRA).
   The fine-tuned model is the eventual no-tool generation model; fine-tuning is a means, not the goal.

`app/`, `outputs/`, `reports/`, `references/` are demo UI, generated deliverables, and manuscripts —
peripheral to the core research code.

## Data Generation Agent Architecture (`LLM/src/sr2fpga_agent/`)

Pipeline, in dependency order:

- **`models.py`** — frozen dataclasses shared everywhere: `ProjectRequest`, `PlatformProfile`,
  `GeneratedProject` (files keyed by POSIX relative path), `ToolResult`.
- **`project_generator.py`** — *deterministic* V1 generator. Produces the full project package for
  task families `counter`, `fifo`, `simple_fsm`, `ram_read_write`. This is the trusted baseline.
- **`deepseek.py`** — *LLM* alternative generator (`DeepSeekProjectGenerator`) via an
  OpenAI-compatible DeepSeek API. Strictly validates the returned JSON: all `REQUIRED_PROJECT_FILES`
  must be present and `manifest.json` must be internally consistent (top module, sources, testbench
  all resolve). Retries on bad JSON. Will also host the repair provider (see below).
- **`agent.py`** — `DataGenerationAgent.run_one()` is the orchestrator: generate project → write
  attempt → run tool pipeline → diagnose first failure → (optional repair) → record. Owns the
  L0–L3 labeling, measured-QoR extraction, and trajectory assembly.
- **`tool_runner.py`** — `CommandRunner.run()` shells out to one tool, returns a `ToolResult`.
  Missing executables become `status="missing_tool"` (not a crash) — so the dataset structure can be
  exercised without the EDA toolchain installed.
- **`log_parser.py`** — `classify_failure()` maps raw logs to the V1 failure taxonomy;
  `parse_yosys_stats()` extracts resource counts (lut/ff/bram/dsp/cells) from Yosys `stat` output.
- **`recorder.py`** — `DatasetRecorder` persists each sample (`attempts/`, `final/`, `eval/`) and
  `export_training_views()` emits the per-task JSONL files.
- **`cli.py`** — argparse entry point; `build_project_generator()` selects deterministic vs deepseek.

### Tool pipeline & pass levels

`agent._run_pipeline()` runs stages in order, short-circuiting on first non-pass:
`lint` (Verilator) → `sim_compile` (iverilog) → `sim_run` (vvp) → `synth` (Yosys + stat).
Labels: **L0** = contract/cross-file consistency, **L1** = lint, **L2** = sim, **L3** = synth.
V1 targets L0–L3 with open-source tools only; L4 (Vivado/Quartus) and L5 (board) are future work.

### Invariants to preserve

- **`predicted_qor.json` is model-generated *before* tool execution; `measured_qor.json` is parsed
  *from* tool output.** Never let measured/tool results leak into predicted QoR. This separation is
  a core research claim — do not blur it.
- Project files must be cross-consistent: `manifest.json` top module ↔ RTL, testbench instantiates
  the real top + ports, constraints reference real ports, System-HIS reset polarity ↔ RTL.
- Failed attempts are research assets, not noise. Preserve the full repair trajectory
  (failed project → tool log → diagnosis → patch.diff → repaired project → next result).

### Training views (exported JSONL)

`export_training_views()` produces, under `datasets/sr2fpga_rtl_v1_exports/`:
`requirement_to_his`, `his_to_project`, `requirement_to_project`, `failure_to_diagnosis`,
`failure_to_patch`, `project_to_predicted_qor`, `project_to_measured_qor`. These map to the planned
training tasks (REQ2HIS, HIS2FILES, REQ2PROJECT, LOG2DIAG, FAILURE2PATCH, PROJECT_CRITIC, QOR_PRED).

## Commands

All Python is run **from the repo root** — there is no installed package and no `__init__.py` under
`LLM/`. Modules use absolute imports like `from LLM.src.sr2fpga_agent...`, which only resolve when
the repo root is on `sys.path` (i.e. cwd = repo root).

```bash
# Run all data-agent tests (unittest; pytest also works from repo root)
python3 -m unittest discover -s LLM/tests -q

# Run a single test module / case
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder.RecorderTest.<method> -q

# Generate one dataset sample with the deterministic generator
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_000001 \
  --task-type counter --width 8 --project-name counter_8bit
# task-type in {counter, fifo, simple_fsm, ram_read_write}

# Generate with DeepSeek (key read only from env, never written to repo/samples)
export DEEPSEEK_API_KEY="your-key"
python3 -m LLM.src.sr2fpga_agent.cli --provider deepseek --model deepseek-v4-flash \
  --dataset-root datasets/sr2fpga_rtl_v1 --sample-id sample_llm_000001 \
  --task-type counter --width 8 --project-name counter_8bit
```

EDA tools (`verilator`, `iverilog`/`vvp`, `yosys`) must be installed separately for real labels;
without them the agent records `missing_tool` results and still exercises the dataset schema.

Model serving / fine-tuning (cloud, runs inside WSL2 on the deploy box — see `LLM/README.md` and
`LLM/DEPLOY.md`): `bash LLM/scripts/serve_qwen_vllm.sh` (recommended stable vLLM path),
`bash LLM/scripts/train_lora.sh <config>`, `python -m LLM.src.prepare_dataset --input ... --output ...`.
The serving model is Qwen2.5-Coder-7B-Instruct (Gemma 4 12B is an experimental, currently-failing path).

## Spec / Plan Workflow

This repo uses the superpowers brainstorming→spec→plan workflow. Design decisions are recorded as
markdown before code:
- `docs/superpowers/specs/` — approved designs (one per feature, dated).
- `docs/superpowers/plans/` — implementation plans.

When picking up in-progress work, check the newest dated spec/plan. The active thread on branch
`codex/sr2fpga-data-agent` is the **DeepSeek repair loop**
(`docs/superpowers/specs/2026-06-22-sr2fpga-deepseek-repair-loop-design.md`): a `DeepSeekRepairer`
that takes a failed project + diagnosis, returns a complete repaired `GeneratedProject`, with
`patch.diff` computed locally (not trusted from the model). It plugs into the existing
`DataGenerationAgent(repairer=..., max_attempts=...)` hook.

## Conventions

- Cross-platform line endings are enforced via `.gitattributes` (`*.sh/.py/.yaml/.env` = LF) because
  scripts execute inside WSL/Linux — never introduce CRLF into these.
- Git hygiene: commit source, scripts, configs, small docs. Do **not** commit model weights, raw
  datasets, LoRA adapters/merged models, venvs, or `serve_vllm.env`. Generated `datasets/` samples
  are working artifacts, not committed deliverables.
- Near-term priorities (from the objective doc): expand task families (valid-ready pipeline, vector
  add, small AI kernels), deliberately collect failure/repair trajectories, then train first models
  on REQ2HIS / LOG2DIAG / FAILURE2PATCH.
