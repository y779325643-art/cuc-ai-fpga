# SR2FPGA DeepSeek Repair Loop Design

## Decision

This document records the next SR2FPGA data-agent step: add a first DeepSeek
repair loop for failed generated RTL projects.

The approved direction is approach A:

```text
LLM-generated project
-> open-source tool failure
-> DeepSeek repair prompt with project files and failure log
-> repaired complete project package
-> rerun tools
-> record diagnosis, patch.diff, trajectory, labels
```

The goal is not to guarantee every failed sample reaches L3. The goal is to
start collecting real repair trajectories for `LOG2DIAG` and `FAILURE2PATCH`
training views.

## Scope

Included:

- Add `DeepSeekRepairer`.
- Wire the CLI with:
  - `--repair-provider none|deepseek`
  - `--max-attempts`
- Keep generation provider and repair provider separate.
- Use the existing `DataGenerationAgent(repairer=..., max_attempts=...)`
  orchestration hook.
- Give the repairer:
  - original generated project files,
  - structured diagnosis,
  - failing stage,
  - failure log text,
  - enough guidance to preserve the SR2FPGA project package shape.
- Make the repairer return a complete repaired `GeneratedProject`.
- Generate `patch.diff` locally by comparing original and repaired project
  files.
- Record every attempt using the existing dataset recorder.

Excluded from this first repair loop:

- Separate diagnosis LLM agent.
- Local patch application.
- Multi-file semantic diff editing.
- More than one repair cycle as a default.
- Vendor tools, bitstream generation, or board execution.
- Committing generated datasets.

## Architecture

The implementation should keep the current boundaries:

- `agent.py` remains the orchestration layer.
- `deepseek.py` owns DeepSeek generation and repair provider logic.
- `cli.py` builds project generator and optional repairer.
- `recorder.py` keeps writing attempts, diagnoses, patches, final labels, and
  JSONL exports unchanged.

The repairer interface should match the existing agent hook:

```python
repair(project: GeneratedProject, diagnosis: dict[str, object]) -> RepairResult
```

For V1, the repairer may rely only on `project` and `diagnosis`, because the
diagnosis already contains the failing stage and raw tool log in `root_cause`.
If later experiments need richer context, the agent can pass requirement and
platform into a richer repair context in a separate change.

## Data Flow

1. CLI creates a project generator from `--provider`.
2. CLI creates a repairer from `--repair-provider`.
3. CLI passes `max_attempts` into `DataGenerationAgent`.
4. Attempt 0 runs as today.
5. If a stage fails and a repairer exists and another attempt is allowed:
   - agent calls `repairer.repair(project, diagnosis)`;
   - repairer asks DeepSeek for a complete repaired project package;
   - repairer validates the same required files and manifest schema as
     generation;
   - repairer returns `RepairResult(generated_project, patch_diff)`.
6. Agent records attempt 0 with diagnosis and patch path.
7. Attempt 1 writes the repaired project and reruns the tool pipeline.
8. Final labels reflect the final attempt level and total failure count.

## Repair Prompt Requirements

The repair prompt should ask DeepSeek to:

- preserve the same project package shape;
- return only valid JSON;
- return all required files under `files`;
- keep pure Verilog RTL;
- avoid vendor IP, HLS, bitstream, or real tool reports;
- focus on the failing tool log;
- make the smallest practical fix;
- keep `manifest.json` compatible with the agent pipeline:

```json
{
  "project_name": "<project_name>",
  "top_module": "top",
  "sources": ["rtl/top.v"],
  "constraints": ["constraints/timing.sdc"],
  "simulation": {"testbench": "sim/tb_top.v"},
  "reports": ["reports/predicted_qor.json"]
}
```

## Patch Diff

For V1, `patch.diff` should be generated locally from complete project files.
This avoids trusting the model to produce a correct unified diff.

Diff behavior:

- Compare every file path in the union of old and repaired projects.
- Use POSIX-style relative paths.
- Emit a unified diff with stable labels:
  - `a/<path>`
  - `b/<path>`
- Include changed, added, and deleted files.

This gives the training dataset a patch-like supervision target even though the
repairer returns full files.

## Error Handling

- If DeepSeek returns invalid JSON, retry using the same bounded retry behavior
  as generation.
- If required files are missing, fail repair with a clear exception.
- If the repaired manifest is invalid, fail repair with a clear exception.
- If repair fails before producing a project, the current V1 may let the sample
  fail fast. A later robustness pass can record repair-provider failures as a
  separate attempt type.
- If the repair succeeds but tools still fail, record the second failed attempt.

## Testing

Required tests:

- CLI builds no repairer by default.
- CLI builds `DeepSeekRepairer` from the same DeepSeek env/config when
  `--repair-provider deepseek`.
- `DeepSeekRepairer` sends project files and failure diagnosis to the client.
- `DeepSeekRepairer` returns a repaired `GeneratedProject`.
- Local project diff generation records a meaningful `patch.diff`.
- `DataGenerationAgent` with a fake repairer still records failed attempt,
  patch, repaired attempt, final labels, and exportable `failure_to_patch`
  rows.

Verification commands:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
python3 -m unittest discover -s LLM/tests -q
```

Manual smoke test:

```bash
DEEPSEEK_API_KEY="..." python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_llm_repair_000001 \
  --provider deepseek \
  --repair-provider deepseek \
  --max-attempts 2 \
  --task-type counter \
  --width 8 \
  --project-name llm_counter_repair_8bit \
  --requirement "Design an 8-bit synchronous counter with enable, active-low reset, self-checking Verilog testbench, timing constraint, manifest, system_his, and predicted QoR."
```

The smoke test is successful if a sample records at least attempt 0 and final
labels. It is stronger if a failed attempt produces `patch.diff` and a repaired
attempt reaches a higher pass level.

## Follow-Up

After V1 repair works, the next research-aligned step is to split the repair
trajectory into explicit training tasks:

- `LOG2DIAG`: tool log and project context to structured diagnosis.
- `FAILURE2PATCH`: failed project plus diagnosis to patch diff.
- `PATCH2VERIFY`: patch trajectory to final pass-level prediction.
