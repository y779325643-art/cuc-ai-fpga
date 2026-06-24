# HNAI-FPGA / SR2FPGA

HNAI-FPGA is being developed as **SR2FPGA: tool-verified learning for
system-requirement-to-FPGA RTL project generation**.

The repository contains research documents, dataset-generation tools, generated
SR2FPGA samples, local/cloud LLM deployment utilities, and a small Spec-to-RTL
demo interface. The central research direction is not plain
`natural language -> Verilog`; it is project-level generation with tool-derived
supervision:

```text
system requirement
-> System-HIS
-> multi-file Verilog RTL project
-> constraints / testbench / predicted QoR
-> lint / simulation / synthesis / later implementation labels
-> diagnosis / patch / repair trajectory
-> trainable dataset and model
```

The current engineering priority is the dataset factory and benchmark pipeline.
The long-term paper target is TCAD, with TRETS as a fallback if the eventual
method novelty or physical-evaluation depth is better suited there.

## Research Position

The project studies how a model can learn to generate complete FPGA RTL project
packages from system requirements by internalizing feedback from EDA tools.

Core ideas:

- **System-HIS**: an intermediate hardware-intent representation above RTL.
- **Project-level generation**: output is a coherent project package, not a
  single code snippet.
- **Tool-verified trajectories**: failed attempts, logs, diagnoses, patches,
  pass levels, and measured QoR are preserved as training data.
- **L0-L5 evaluation**: progress from project consistency through lint,
  simulation, synthesis, implementation/timing, and representative board runs.
- **Tool distillation, not LLM distillation**: tools are the objective teacher;
  DeepSeek/frontier models are candidate generators and baselines.

Important project documents:

- `docs/README.md` - documentation map and recommended reading order.
- `docs/current-status.md` - living current engineering status.
- `docs/research-objective-sr2fpga-tcad.md` - project-level research objective.
- `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md` -
  TCAD/TRETS research reframe and paper program.
- `docs/superpowers/specs/2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`
  - autonomous trajectory runner design.
- `docs/superpowers/decisions/2026-06-22-sr2fpga-reframe-decision-log.md` -
  decision log and reasoning trail.

## Current Capability

The current SR2FPGA agent can generate Verilog RTL project samples, run a
lightweight open-source EDA pipeline, record labels, and export trainable JSONL
views.

Generated project package:

```text
generated_project/
  system_his.json
  manifest.json
  rtl/top.v
  rtl/*.v
  constraints/timing.sdc
  sim/tb_top.v
  reports/predicted_qor.json
```

Current verification levels:

- `L1`: Verilator lint pass.
- `L2`: Icarus Verilog compile/run with `TEST_PASS`.
- `L3`: Yosys synthesis pass with measured resource statistics.

Planned later levels:

- `L4`: implementation and timing closure through OpenXC7/Vivado.
- `L5`: sparse representative board validation, initially targeting the
  AC820-ZYNQ / XC7Z020 line of work described in the research specs.

Current task families include single-module and multi-module RTL projects:

- `counter`
- `fifo`
- `simple_fsm`
- `ram_read_write`
- `uart_tx`
- `spi_master`
- `pwm_controller`
- `fir_filter`
- `streaming_valid_ready`
- `matrix_vector_mac`
- `composed_event_counter`
- `composed_stream_accumulator`
- `composed_stream_fork`
- `composed_dual_stream_join`

The multi-module families are expected to emit `rtl/top.v` plus task-specific
submodule `.v` files. The DeepSeek path rejects single-file responses for these
families.

## Quick Start

Run the test suite:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Generate one deterministic sample:

```bash
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_local_counter_000001 \
  --task-type counter \
  --width 8 \
  --project-name local_counter_8bit
```

Run baseline (a), first attempt with no tool-loop repair, across the current
T1-T4 component-topology tasks:

```bash
python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_baseline_a.example.yaml \
  --run-id deepseek-baseline-a \
  --preflight

python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_baseline_a.example.yaml \
  --run-id deepseek-baseline-a
```

The preflight command prints JSON with tool readiness, API-key readiness, run
directory status, and a planned sample preview for the T1-T4 topology set. Each
preview includes the exact requirement text that will be sent to the generator,
including topology nodes, edges, difficulty tier, and expected behavior.
Baseline (a) uses the `natural_component` requirement style: a deterministic
surface rewrite that makes component-topology prompts read like engineering
requirements while preserving the same audited contracts.

Run the autonomous batch runner with the tool-loop example config:

```bash
python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_agent.example.yaml \
  --run-id deepseek-tool-loop-smoke
```

The example runner config uses DeepSeek by default. Set the API key through the
environment or the ignored local `.env` file, never in tracked files. The
baseline (a) config declares `env_file: .env`, so the runner will load it
automatically when present:

```bash
cp .env.example .env
# edit .env locally
```

On macOS/Python.org installs, if HTTPS verification fails with
`CERTIFICATE_VERIFY_FAILED`, set `SSL_CERT_FILE=/etc/ssl/cert.pem` in the local
ignored `.env` file.

The runner preflight reports whether `DEEPSEEK_API_KEY` is present, where it
was loaded from (`environment` or `.env`), and a short non-secret fingerprint so
you can confirm that a local key update took effect before launching a run.
Add `--validate-provider` to make a minimal DeepSeek authentication request
before generation:

```bash
python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_baseline_a.example.yaml \
  --run-id deepseek-baseline-a \
  --preflight \
  --validate-provider
```

For a no-network deterministic smoke run, create a temporary JSON config with
`provider: deterministic` and `repair_provider: none`, or use the unit tests in
`LLM/tests/test_sr2fpga_agent_runner.py`.

## Autonomous Runner

The runner is the preferred control entry for producing more than one sample:

```bash
python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_baseline_a.example.yaml \
  --run-id <run-id>
```

It provides:

- config-driven task planning;
- resumable `run_state.json` with a config fingerprint; resume rejects runs
  when the same run ID is reused with a different config;
- `events.jsonl` for compact run events;
- `summary.json` with bucket counts and failure histograms;
- `baseline_report.md` with source, failure-origin, requirement-style,
  difficulty-tier, topology, and measurement-point calibration rows plus the
  first pass-rate knee under the default 80% L3 threshold;
- `success_l3`, `repair_trajectory`, and `rejected` sample buckets;
- automatic refresh of training exports.

The runner writes `baseline_report.md` automatically. Regenerate it manually if
you edit or copy a `summary.json`:

```bash
python3 -m LLM.src.sr2fpga_agent.baseline_report \
  --summary tmp/sr2fpga_runs/<run-id>/summary.json \
  --knee-threshold 0.8 \
  --output tmp/sr2fpga_runs/<run-id>/baseline_report.md
```

Full run logs live under `tmp/sr2fpga_runs/<run-id>/` and should remain local
by default. Commit compact summaries only when they are useful for research
traceability.

## Dataset And Exports

The repository currently includes a milestone SR2FPGA RTL dataset snapshot under
`datasets/sr2fpga_rtl_v1/` and exported JSONL views under
`datasets/sr2fpga_rtl_v1_exports/`.

Each sample may contain:

```text
requirement.txt
platform_profile.json
attempts/attempt_*/generated_project/
attempts/attempt_*/eval/
attempts/attempt_*/diagnosis.json
attempts/attempt_*/patch.diff
final/generated_project/
eval/labels.json
eval/measured_qor.json
eval/tool_versions.json
eval/trajectory.json
```

Training views include:

- `requirement_to_his.jsonl`
- `his_to_project.jsonl`
- `requirement_to_project.jsonl`
- `failure_to_diagnosis.jsonl`
- `failure_to_patch.jsonl`
- `project_to_predicted_qor.jsonl`
- `project_to_measured_qor.jsonl`

## Repository Layout

- `LLM/` - local/cloud LLM deployment, fine-tuning utilities, and SR2FPGA agent
  code.
- `LLM/src/sr2fpga_agent/` - generation, tool running, recording, DeepSeek
  integration, and autonomous runner modules.
- `LLM/tests/` - unit and smoke tests for dataset preparation, serving scripts,
  and SR2FPGA agent behavior.
- `configs/` - repository-level runner configs, including the safe example
  config.
- `datasets/` - committed SR2FPGA milestone dataset snapshot and exported JSONL
  views.
- `docs/` - research objectives, specs, decisions, handoff notes, and plans.
- `app/` - browser-based Spec-to-RTL demo interface.
- `assets/` - images and visual references.
- `reports/` - manuscripts, rendered PDFs, and report outputs.
- `outputs/` - generated presentation/report deliverables.
- `references/` - background reading and reference notes.
- `tmp/` - ignored local run logs and temporary artifacts.

## LLM Deployment

The `LLM/` workspace also contains cloud deployment and fine-tuning scripts.
The verified preferred serving path is currently Qwen2.5-Coder-7B-Instruct via
vLLM on an OpenAI-compatible local API. Gemma 4 compatibility work is recorded
but not the preferred serving route.

See:

- `LLM/README.md`
- `LLM/DEPLOY.md`
- `LLM/scripts/serve_qwen_vllm.sh`
- `LLM/scripts/setup_server.sh`

## Application Interface

Open `app/index.html` in a browser to use the Spec-to-RTL demo interface. It can
call a local OpenAI-compatible vLLM endpoint at `http://127.0.0.1:8000/v1` when
the model service is running, and falls back to demo Verilog output when the
service is unavailable.

## Tooling Requirements

For real L0-L3 sample validation, install:

- Verilator
- Icarus Verilog (`iverilog` and `vvp`)
- Yosys

If the tools are missing, the agent can still record missing-tool failures,
which is useful for validating dataset structure but not for producing passing
L3 samples.

## Secrets And Git Hygiene

- Do not commit real API keys, including in README, specs, handoff notes,
  configs, shell history snippets, or run summaries.
- `.env` is ignored and should stay local; put the real
  `DEEPSEEK_API_KEY` there or export it only in the current shell.
- `.env.example` documents the expected environment variable names.
- Large model weights, LoRA outputs, server-local caches, and temporary run logs
  should remain outside Git or under ignored directories.
- Commit source code, tests, configs, research docs, reproducible scripts, and
  intentional milestone dataset snapshots.
