# SR2FPGA Official Eval Gap Closure

This checkpoint freezes the pre-OpenXC7 eval scaffold for the paper-facing task set.

## Scope

- T1-T12 component topologies remain the primary complexity ladder.
- `alu_control_unit` and `crc_stream_checker` cover common official benchmark families not represented by the RL-oriented topologies.
- The new config runs 14 deterministic reference samples and 14 `deepseek-his-v12` samples.
- This stage targets local open-source L0-L3 labels only. OpenXC7/Vivado validation is a Windows follow-up.

## Local Command

```bash
python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_official_eval_gap_closure.example.yaml \
  --run-id official-eval-gap-closure-20260629 \
  --preflight
```

After preflight passes and `DEEPSEEK_API_KEY` is available:

```bash
python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_official_eval_gap_closure.example.yaml \
  --run-id official-eval-gap-closure-20260629 \
  --no-resume
```

## Windows Boundary

Stop after local generated projects, `summary.json`, `baseline_report.md`, and exports are produced. The next environment-dependent step is OpenXC7/Vivado on Windows, using the generated `final/generated_project` directories as inputs.
