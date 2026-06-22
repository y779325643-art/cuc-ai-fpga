# SR2FPGA LLM Generation Entry Design

## Decision

This document records the next SR2FPGA data-agent step: connect an actual LLM
project generator to the existing open-source tool verification pipeline.

The approved first step is intentionally narrow:

```text
natural-language requirement
-> DeepSeek project generation
-> Verilator / Icarus / Yosys verification
-> dataset attempt, logs, labels, trajectory
```

This step proves that the data factory can use an LLM as the code-writing
agent. Multi-round LLM repair is left for the next implementation step so that
format stability, tool verification, and dataset recording can be debugged
separately from repair policy quality.

## Scope

Included:

- Use `--provider deepseek` as a real LLM generation path.
- Pass the CLI `--requirement` text into `ProjectRequest.description`.
- Ask the model to generate the required SR2FPGA project files:
  - `system_his.json`
  - `manifest.json`
  - `rtl/top.v`
  - `constraints/timing.sdc`
  - `sim/tb_top.v`
  - `reports/predicted_qor.json`
- Validate that required files exist before tool execution.
- Run the existing tool pipeline unchanged:
  - Verilator lint
  - Icarus Verilog compile and simulation
  - Yosys synthesis and resource parsing
- Record failed LLM outputs as attempts when the generated package is complete
  enough to write to disk and run tools.
- Keep API keys environment-only.

Excluded:

- Multi-round repair.
- Automatic patch generation.
- Vendor IP, HLS, bitstream, or board programming.
- Required Vivado / Quartus execution.
- Committing generated dataset samples.

## Architecture

The implementation should reuse the current boundaries:

- `cli.py` selects the generator provider and constructs `ProjectRequest`.
- `deepseek.py` handles chat completion calls and response parsing.
- `DataGenerationAgent` remains the orchestration layer for generate, write,
  verify, and record.
- `ProjectGenerator` remains the deterministic baseline and fallback.

The DeepSeek generator should satisfy the same interface as the deterministic
generator:

```python
generate(request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject
```

This keeps the agent independent from model provider details and allows later
providers to be added without changing the tool pipeline or recorder.

## Data Flow

1. User runs the CLI with `--provider deepseek`.
2. CLI reads the API key from `DEEPSEEK_API_KEY` or the configured env name.
3. CLI builds `ProjectRequest` with the user-provided natural-language
   requirement as `description`.
4. `DeepSeekProjectGenerator` sends a constrained JSON-only prompt.
5. `parse_project_files` parses and validates the returned package.
6. `DataGenerationAgent` writes the files under `attempts/attempt_000/`.
7. The existing tool runner executes lint, simulation, and synthesis.
8. The recorder saves logs, labels, measured QoR, and trajectory data.

## Error Handling

Response parsing failures should fail clearly before tool execution:

- Invalid JSON: raise a parse error that explains the output was not JSON.
- Missing required file: raise a validation error listing missing paths.
- Missing API key: exit with a concise env-var message.

Tool failures should continue to use the existing attempt/eval structure:

- The generated files are saved.
- The failing tool log is saved.
- The final label reflects the highest passed level.
- The trajectory records the stage, command, exit code, and failure type.

## Testing

The implementation should follow test-first changes.

Required tests:

- CLI passes `--requirement` into `ProjectRequest.description`.
- `DataGenerationAgent` can use an injected fake LLM generator and records that
  generated output instead of deterministic templates.
- DeepSeek parser continues accepting both mapping and list file formats.
- Missing required files still fail with a clear validation message.

Verification commands:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
python3 -m unittest discover -s LLM/tests -q
```

Manual smoke test after implementation:

```bash
export DEEPSEEK_API_KEY="..."
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_llm_000001 \
  --provider deepseek \
  --task-type counter \
  --width 8 \
  --project-name llm_counter_8bit \
  --requirement "Design an 8-bit synchronous counter with enable, active-low reset, testbench, and predicted QoR."
```

The smoke test is successful if the sample is written and the pass level is
recorded. It does not have to pass L3 on the first real LLM attempt; failures
are useful dataset evidence as long as they are recorded.

## Follow-Up

After this entry point works, the next research-aligned step is repair-data
collection:

```text
LLM-generated project
-> tool failure
-> structured diagnosis
-> LLM repair
-> rerun tools
-> record patch trajectory
```

That follow-up should produce `LOG2DIAG` and `FAILURE2PATCH` training views.
