# SR2FPGA Runner Configs

- `current/` holds the active smoke, evaluation, and latest checkpoint configs.
- `legacy/` holds older baseline/demo configs that remain useful for comparison.
- `archive/` holds historical experiment snapshots superseded by later configs.
- `local/` holds ignored machine-local configs such as private provider runs.

Use `python -m LLM.src.sr2fpga_agent.runner --config <path>` with the full path
to the YAML file in one of these subdirectories.

`current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml` is the opt-in
Line-A physical-reference config. It runs the catalog-selected OpenXC7 subset
and the Vivado commercial-reference subset after L3. Vivado remains disabled in
normal Line-B configs. Set the machine-local launcher without committing an
installation path, for example:

```powershell
$env:SR2FPGA_VIVADO_COMMAND='D:\Xilinx\Vivado\2024.2\bin\vivado.bat'
python -m LLM.src.sr2fpga_agent.runner `
  --config configs/current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml `
  --run-id line-a-l4-dual-tool-reference
```
