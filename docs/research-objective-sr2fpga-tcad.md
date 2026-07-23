# SR2FPGA TCAD Research Objective

> **Positioning note (2026-06-23):** This document is a concise project-level
> objective summary. The primary research framing is the approved reframe spec:
> `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`.
> Where this summary and the reframe spec differ, the reframe spec governs.
> Keep this file aligned with that spec rather than treating it as a competing
> source of truth.

## Purpose

This document records the project-level research objective for HNAI-FPGA / SR2FPGA. Future development, dataset construction, model training, and manuscript writing should align with this direction.

The project should be treated as a TCAD-oriented EDA method research project, not as a general platform demo and not as a single-file LLM-to-Verilog showcase.

## One-Sentence Direction

**SR2FPGA studies tool-verified learning for system-requirement-to-FPGA RTL project generation.**

Chinese formulation:

**本课题研究基于 System-HIS 与工具验证轨迹的 FPGA RTL 工程生成方法，使模型能够从系统需求出发，生成、诊断、修复并预测多文件 FPGA RTL 工程的质量。**

## Recommended Paper Positioning

Recommended English titles:

- **SR2FPGA: Learning FPGA RTL Project Generation from Tool-Verified Agent Trajectories**
- **Tool-Verified Agentic Learning for System-Requirement-to-FPGA RTL Project Generation**
- **Learning FPGA Project Generation from Tool-Verified Evolutionary Design Trajectories**

Recommended Chinese title:

**基于工具验证轨迹学习的系统需求到 FPGA RTL 工程生成方法研究**

## Core Problem

The research problem is not simply:

```text
natural language -> Verilog code
```

The real problem is:

```text
system requirement
-> System-HIS
-> multi-file Verilog RTL project
-> constraints / testbench / predicted QoR
-> lint / simulation / synthesis / implementation labels
-> diagnosis / patch / repair trajectory
-> trainable dataset and model
```

The central question is:

**How can AI learn to generate FPGA RTL project packages that satisfy functional, interface, constraint, synthesis, and quality requirements, using EDA tool feedback as objective supervision?**

## What This Project Must Solve

### 1. Requirement-To-Hardware Intent

Natural-language requirements must be converted into structured hardware intent:

- Function
- Ports
- Bit widths
- Clock and reset
- State machines
- Datapaths
- Storage structures
- Interface protocols
- Verification goals
- Resource and timing expectations

`system_his.json` is the intermediate supervision format for this step.

### 2. Project-Level Generation

The generated object is not a single Verilog file. It is a multi-file RTL project package:

```text
generated_project/
  system_his.json
  manifest.json
  rtl/top.v
  constraints/timing.sdc
  sim/tb_top.v
  reports/predicted_qor.json
```

The generated files must be internally consistent:

- `manifest.json` top module matches RTL.
- Testbench instantiates the correct top module and ports.
- Constraints reference real design ports.
- `System-HIS` reset polarity and interface match RTL.
- `predicted_qor.json` is generated before tool execution and does not leak measured results.

### 3. Tool-Verified Dataset Construction

The data generation agent may call tools. It is a dataset factory, not the final no-tool generation model.

The agent should generate projects, run tools, record failures, repair projects, and save objective labels:

```text
Verilator -> lint labels
Icarus Verilog -> simulation labels
Yosys -> synthesis and measured QoR labels
Vivado / Quartus -> later implementation, timing, and power labels
board tests -> sparse representative L5 labels
```

Each dataset sample should preserve:

```text
requirement
system_his
generated_project
attempts
tool logs
diagnosis.json
patch.diff
labels.json
measured_qor.json
trajectory.json
```

### 4. Failure Diagnosis And Repair Learning

The project should not keep only final successful code. Failed attempts are research assets.

The primary failure source should be **natural LLM-generated RTL project
failures**, not hand-injected toy bugs. The preferred trajectory is:

```text
hard system requirement
-> LLM-generated multi-file RTL project
-> real tool failure from Verilator / Icarus / Yosys / later implementation
-> structured diagnosis
-> LLM or agent repair
-> rerun tools
-> recorded repair trajectory
```

The repair trajectory must preserve:

```text
failed project
-> tool command and log
-> structured diagnosis
-> patch.diff
-> repaired project
-> next tool result
```

This supports training:

- `LOG2DIAG`
- `FAILURE2PATCH`
- `PROJECT_CRITIC`

Synthetic failure injection is still useful, but only as a secondary control
mechanism:

- pipeline and exporter smoke tests;
- controlled repair ablations;
- failure-taxonomy coverage checks;
- small balanced evaluation slices.

Synthetic injected failures must be labeled separately from natural LLM
failures. They should not become the main training or paper narrative.

Recommended failure-origin labels:

```text
natural_llm
synthetic_injected
mutation
tool_or_environment
```

### 5. QoR Prediction

The model should learn hardware quality intuition:

- LUT / logic cell count
- FF count
- BRAM / memory usage
- DSP / multiplier usage
- Fmax or timing risk
- resource bottleneck
- synthesis pass probability

Separate:

- `predicted_qor.json`: model-generated before tool execution.
- `measured_qor.json`: parsed from external EDA tool outputs.

### 6. Unified Multi-Task Model

Fine-tuning is a means, not the research goal.

The model should learn multiple tasks from the tool-verified dataset:

```text
REQ2HIS
HIS2FILES
REQ2PROJECT
LOG2DIAG
FAILURE2PATCH
PROJECT_CRITIC
QOR_PRED
```

The long-term goal is a no-tool inference model that can generate higher-quality project packages before external evaluation.

## Evaluation Levels

Use project-level metrics, not only compile pass rate:

```text
L0: project contract and cross-file consistency pass
L1: lint pass
L2: functional simulation pass
L3: synthesis pass and measured QoR parsed
L4: implementation / timing pass
L5: representative board execution pass
```

Current V1 target:

```text
L0-L3 with Verilator, Icarus Verilog, and Yosys
```

Later TCAD-grade target:

```text
L4 with Vivado / Quartus implementation
L5 with sparse representative board validation
```

## TCAD-Oriented Contributions

The paper should emphasize EDA method contributions:

1. **System-HIS intermediate supervision** for system-requirement-to-RTL-project generation.
2. **Tool-verified agent trajectory dataset** containing natural LLM failures,
   projects, logs, diagnoses, patches, pass levels, and measured QoR.
3. **Unified SR2FPGA model** for generation, diagnosis, repair, critique, and QoR prediction.
4. **Project-level evaluation** using L0-L5 rather than single-file compile pass.
5. **Failure taxonomy and repair learning** for hardware generation errors.
6. **Optional evolutionary architecture search** in Architecture IR / System-HIS parameter space, using EDA tools as fitness evaluators.

## Role Of Evolutionary Search

Evolutionary search is useful but should not replace the main research thread.

Correct positioning:

```text
LLM proposes candidate structures
-> GA optimizes Architecture IR / System-HIS parameters
-> Agent generates RTL projects
-> EDA tools evaluate fitness
-> trajectories become training data
```

GA should optimize architecture parameters, not raw Verilog tokens.

Examples of searchable parameters:

- Parallel lanes
- Pipeline depth
- Memory banks
- Accumulator width
- Stream width
- Buffer mode
- Target clock

The main topic remains:

**system-requirement-to-FPGA RTL project generation from tool-verified trajectories.**

## What To Avoid

Do not frame the project as:

- A generic "LLM writes Verilog" demo.
- A prompt-engineering platform.
- A natural-language UI for FPGA design only.
- A paper whose main claim is application speedup.
- A paper that reports bitstream or measured QoR as model-generated output.

Avoid overclaiming:

- "complete deployable FPGA project" without enough L4/L5 evidence.
- large acceleration numbers as the main contribution.
- unfair comparisons against Vitis AI, hls4ml, or FINN for non-DNN GA/RL tasks.
- RL-PONG full results unless the model size and parameter counts are revalidated.

## Immediate Work Alignment

Near-term work should follow this order:

1. Keep the deterministic generator as a trusted reference and smoke-test
   source, not the main source of repair-learning failures.
2. Use frontier or local LLMs to generate harder multi-file RTL projects so
   failures arise naturally from model limitations.
3. Preserve every natural failure, tool log, diagnosis, patch, and rerun result
   with explicit metadata for `failure_origin`, `generator`, `repair_provider`,
   and task difficulty.
4. Use synthetic failure injectors only for pipeline tests, controlled ablation,
   and coverage balancing; never mix them silently with natural failures.
5. Export stable JSONL views for `REQ2HIS`, `HIS2FILES`, `REQ2PROJECT`,
   `LOG2DIAG`, `FAILURE2PATCH`, `PROJECT_CRITIC`, and `QOR_PRED`.
6. Train or fine-tune first models after natural-failure volume is sufficient to
   support diagnosis and repair learning.
7. Add OpenXC7 / Vivado L4 and representative board L5 only after the open-source
   L0-L3 flow and trajectory schema are stable.

## Current Repository Mapping

Current implementation assets:

- Data generation agent: `agent/src/sr2fpga_agent/`
- Agent CLI: `python -m sr2fpga_agent.cli`
- Autonomous runner: `python -m sr2fpga_agent.runner`
- Maintained runner configs: `agent/configs/current/`
- Versioned dataset releases: `datasets/`
- Training exports: `datasets/sr2fpga_rtl_v1_exports/`
- Current status: `docs/current-status.md`
- Documentation index: `docs/README.md`
- Generation boundary spec: `docs/superpowers/specs/2026-06-18-sr2fpga-generation-boundary-design.md`
- Data generation agent spec: `docs/superpowers/specs/2026-06-18-sr2fpga-data-generation-agent-design.md`
- Autonomous runner spec: `docs/superpowers/specs/2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`

Future changes should update this document if the research objective changes.
