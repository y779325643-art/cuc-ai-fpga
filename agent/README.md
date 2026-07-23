# SR2FPGA Agent

This project owns FPGA project generation, validation, repair, L0-L4 tool
orchestration, and trajectory recording.

Training and model fine-tuning are owned by the separate `training/` project.
The Agent runtime intentionally has no PyTorch, Transformers, PEFT, or TRL
dependency.

## Installation

From the repository root:

```powershell
python -m pip install -e "agent[dev]"
```

Canonical Python imports use the standalone package:

```python
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.runner import load_runner_config
```

The old `LLM.src.sr2fpga_agent` namespace is transitional compatibility only.
It emits a `DeprecationWarning`; new code must import `sr2fpga_agent`.

## Commands

Editable installation provides:

```text
sr2fpga-agent
sr2fpga-runner
sr2fpga-baseline-report
sr2fpga-req2file-eval
sr2fpga-task-evidence
```

The equivalent module entry points remain available, for example:

```powershell
python -m sr2fpga_agent.runner --help
```

## Configuration

- `agent/configs/current/`: maintained runnable configurations.
- `agent/configs/archive/`: historical evidence; not run by default.
- `agent/configs/legacy/`: compatibility-only configurations.
- `agent/configs/local/`: ignored machine-local overrides when needed.

Active configurations write run output beneath ignored
`artifacts/agent/runs/` and generated candidate datasets beneath ignored
`artifacts/agent/candidates/`. Existing releases under `datasets/` are
immutable inputs. Promoting a candidate into `datasets/` is a separate,
explicit release operation.

## External Tools

L1-L3 execution requires:

- Verilator for lint.
- Icarus Verilog and `vvp` for simulation.
- Yosys for synthesis.

OpenXC7/nextpnr is optional for L4-open physical implementation. Vivado is an
optional commercial-reference flow. Tool discovery and missing-tool outcomes
are recorded separately from model failures.

Executable discovery checks `PATH` first. Additional machine-local tool bins
may be supplied through the platform path-list variable
`SR2FPGA_TOOL_FALLBACK_DIRS`; an OSS CAD Suite root may be supplied through
`SR2FPGA_OSS_CAD_SUITE_ROOT`. No machine-specific tool path is committed in
source.

## Tests

```powershell
python -m pytest agent/tests -q
python -m pytest contracts/tests agent/tests -q
```
