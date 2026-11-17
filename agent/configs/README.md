# SR2FPGA Runner Configs

- `current/` contains maintained **legacy development** smoke and evaluation examples; see its [scope note](current/README.md).
- `archive/` is historical evidence and is not executed by default.
- `legacy/` is compatibility-only and is not executed by default.
- `local/` contains ignored machine-local overrides such as private provider runs.

Here `current/` means maintained legacy configuration, not the PC2.1 runtime or an
official Paper-1 campaign. Research and work-package semantics come from the current
[`paper1-v2.2`](../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
research plan, which replaces the earlier G0-G9 gate sequence with seven work packages.

Use `python -m sr2fpga_agent.runner --config <path>` with the full path
to the YAML file in one of these subdirectories.

## `budget_policy`

Optional; defaults to `legacy-attempts-v1`.

| Value | Per-method model-call ceilings |
| --- | --- |
| `legacy-attempts-v1` (default) | The superseded v1.7/v1.8 formula, derived from `max_attempts`. It gives M5 one more call than M1 at every attempt count |
| `paper1-b4-v1` | The registered B4 allocation from `paper1-v2.2` section 10.1: M0 `1`, M1 `4`, M2/M3/M4 `2`, M5 `4`. `max_attempts` is ignored, and a `max_model_calls` override that contradicts the allocation is rejected |

The optional `paper1-b4-v1` setting aligns only logical call ceilings in the
legacy runtime. It does not migrate a configuration to PC2.1, the AI task
population, or equal total token/tool/time budgets. The allocations live in
`agent/src/sr2fpga_agent/budget_allocation.py`.

The B4 token, tool-subcall, runtime, and EDA ceilings are **not** set: the plan
defers them to development measurement and requires locking before the
exclusionary pilot. `BudgetAllocation.is_freeze_ready` stays `False` until they
are, so selecting `paper1-b4-v1` aligns the call axis only and does not make a
config official-run ready.

`current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml` is the opt-in
Line-A physical-reference config. It runs the catalog-selected OpenXC7 subset
and the Vivado commercial-reference subset after L3. Vivado remains disabled in
normal Line-B configs. Set the machine-local launcher without committing an
installation path, for example:

```powershell
$env:SR2FPGA_VIVADO_COMMAND = (Get-Command vivado.bat).Source
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml `
  --run-id line-a-l4-dual-tool-reference
```
