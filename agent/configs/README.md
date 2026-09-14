# SR2FPGA Runner Configs

- `current/` contains maintained smoke and evaluation examples.
- `archive/` is historical evidence and is not executed by default.
- `legacy/` is compatibility-only and is not executed by default.
- `local/` contains ignored machine-local overrides such as private provider runs.

Here `current/` means maintained configuration, not signed G4b authority or an
official Paper-1 campaign. Research and gate semantics come from the active
[`paper1-freeze-v1.7`](../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md).

Use `python -m sr2fpga_agent.runner --config <path>` with the full path
to the YAML file in one of these subdirectories.

`current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml` is the opt-in
Line-A physical-reference config. It runs the catalog-selected OpenXC7 subset
and the Vivado commercial-reference subset after L3. Vivado remains disabled in
normal Line-B configs. Set the machine-local launcher without committing an
installation path, for example:

```powershell
$env:SR2FPGA_VIVADO_COMMAND='D:\Xilinx\Vivado\2024.2\bin\vivado.bat'
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml `
  --run-id line-a-l4-dual-tool-reference
```
