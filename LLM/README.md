# LLM Cloud Deployment and Fine-Tuning

Use this directory for cloud-server model deployment and later fine-tuning. The local machine prepares code and pushes it to GitHub; the cloud server clones the repository, installs dependencies, and serves the model. On Windows cloud servers, run the deployment inside WSL2/Ubuntu.

Downloaded models:

- `google/gemma-4-12B-it`
- `Qwen/Qwen2.5-Coder-7B-Instruct`

Recommended vLLM service model: `Qwen/Qwen2.5-Coder-7B-Instruct`.

Deployment status: Qwen2.5-Coder-7B-Instruct has been successfully served with
vLLM on an RTX 4090 24GB under Windows WSL2, and the OpenAI-compatible chat API
has returned valid Verilog output.

Primary deployment guide: `LLM/DEPLOY.md`.

Current deployment decision:

- Deploy first, fine-tune later.
- Use Windows + WSL2/Ubuntu on the cloud server.
- WSL itself stays in the Windows-managed location on `C:` because `E:` may
  not be suitable for WSL registration.
- Keep durable assets under `E:\Aowen`: the project checkout, Python venv,
  model files, datasets, caches, training outputs, merged models, logs, and
  WSL export backups.
- The default project path is `/mnt/e/Aowen/repos/cuc-ai-fpga`.
- The default venv path is `/mnt/e/Aowen/venvs/cuc-ai-fpga`.
- Run the current Gemma compatibility test in float16 without 4-bit quantization.
- Use ModelScope as the current model download route if Hugging Face fails inside WSL.
- Treat Gemma 4 12B vLLM serving as an experimental compatibility path.
- Use Qwen2.5-Coder-7B-Instruct as the preferred vLLM path for RTL/Verilog generation.

## Gemma 4 vLLM Compatibility Status

The ModelScope download completed successfully and the local model is expected at:

```text
/mnt/c/Users/Administrator/models/gemma-4-12B-it
```

vLLM can load approximately 22.56 GiB of weights, but the current
vLLM/Transformers combination may fail while starting EngineCore:

```text
RuntimeError: mat1 and mat2 shapes cannot be multiplied
(1024x4096 and 8192x3840)
```

The failure occurs in Gemma4 Unified attention `o_proj` during profiling or a
dummy run. It is not a model-path error, malformed JSON, or a simple CUDA OOM.

Use these routes:

- `LLM/scripts/serve_vllm.sh`: Gemma 4 vLLM compatibility testing only.
- `python test_gemma_transformers.py`: Gemma 4 Transformers chat-template test.
- `LLM/scripts/serve_qwen_vllm.sh`: recommended stable vLLM service.

## Layout

- `configs/` - LoRA training and vLLM serving configuration templates.
- `data/` - cloud-local training data. JSONL data files are ignored by Git.
- `scripts/` - cloud setup, training, merge, and serving scripts.
- `src/` - Python entrypoints for dataset preparation, training, and adapter merge.
- `tests/` - lightweight tests for repository-side utilities.

## SR2FPGA Data Generation Agent

The `LLM/src/sr2fpga_agent/` package contains the first lightweight data
generation agent for SR2FPGA RTL project samples. It is a tool-calling dataset
factory, not the final no-tool generation model.

V1 generates a small Verilog project package with:

- `system_his.json`
- `manifest.json`
- one or more RTL files under `rtl/`, always including `rtl/top.v`
- `constraints/timing.sdc`
- `sim/tb_top.v`
- `reports/predicted_qor.json`

`system_his.json` uses the current `system-his-v1.1` shape with explicit
`project`, `clocks`, `resets`, `modules`, `connections`, `top_ports`, and
`qor_intent` records. The L0 checker validates those records against
`manifest.json` and the emitted RTL before HDL tools run. Module records also
include clock/reset domain names, one-line intent strings, spec-style `params`,
and top-level instance parameter overrides when a submodule is instantiated with
`#(...)`. The `verification` record includes the expected L0-L3 checks and
`test_pass_means` acceptance text for the self-checking testbench.
L0 also checks that System-HIS port directions and widths match RTL module
declarations, `top_ports` matches the manifest top module, the testbench
instantiates the manifest top module, verification acceptance fields are
present, `clocks`/`resets`/`qor_intent.resources` are structurally valid, and
connection `protocol`/`width`/`cdc` fields and timing constraints reference real
top-level ports. Connection widths may be positive integers or non-empty
parameterized width expressions.

Current deterministic V1 task types are `counter`, `fifo`, `simple_fsm`,
`ram_read_write`, `uart_tx`, `spi_master`, `pwm_controller`, `fir_filter`,
`streaming_valid_ready`, `matrix_vector_mac`, `composed_event_counter`, and
`composed_stream_accumulator`, `composed_stream_fork`, and
`composed_dual_stream_join`. The multi-module families generate `rtl/top.v`
plus task-specific submodule `.v` files. The
`composed_*` task family is the first deterministic component-topology benchmark
set and records its component-library topology in System-HIS.

It can then run a command-line pipeline:

- Verilator for lint
- Icarus Verilog for simulation
- Yosys for synthesis and resource statistics

Install those tools separately before running real checks. Without them, the
agent still records missing-tool results, which is useful for testing the
dataset structure.

Generate one sample:

```bash
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_000001 \
  --task-type counter \
  --width 8 \
  --project-name counter_8bit
```

Replace `--task-type`, `--width`, and `--project-name` to generate another
supported task family, for example `fifo`, `spi_master`, or `fir_filter`.

Use DeepSeek as the project generator:

```bash
export DEEPSEEK_API_KEY="your-key"

python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_000006 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --task-type counter \
  --width 8 \
  --project-name counter_8bit
```

For multi-module task types, the DeepSeek prompt requires the LLM to generate a
true multi-file RTL package. For example, `spi_master` is expected to return
`rtl/top.v`, `rtl/clock_divider.v`, and `rtl/spi_master_core.v`, and
`manifest.json.sources` must list every RTL file. The agent rejects a single
`rtl/top.v` response for these multi-module task families and asks DeepSeek to
retry.

```bash
export DEEPSEEK_API_KEY="your-key"

python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_llm_spi_master_000001 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --task-type spi_master \
  --width 8 \
  --project-name llm_spi_master_8bit \
  --requirement "Design an 8-bit SPI master as a true multi-file Verilog RTL project. Keep rtl/top.v as the integration wrapper, place protocol and clocking logic in separate submodule .v files, include a self-checking testbench, timing constraint, manifest, system_his, and predicted QoR."
```

The API key is read only from the environment. Do not write it into repository
files or generated samples.

Use DeepSeek for generation and one repair attempt:

```bash
export DEEPSEEK_API_KEY="your-key"

python3 -m LLM.src.sr2fpga_agent.cli \
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

### Autonomous Batch Runner

Use the runner when generating more than one sample. The runner reads a config,
creates sample IDs, runs the existing `DataGenerationAgent`, records a resumable
run state, refreshes training exports, and prints a compact summary.
Each task can declare its data source, difficulty tier, failure origin, and
measurement point; these fields are persisted as sample metadata and copied into
exported JSONL rows.
Supported measurement points are `a_first_attempt_no_tools`,
`b_tool_in_loop_repair`, and `c_finetuned_first_attempt_no_tools`, matching the
reframe spec's (a)/(b)/(c) comparison structure.
For compositional deterministic samples, use `task_type: component_topology`
with `topology_ids` such as `t1_event_counter`, `t2_stream_accumulator`, and
`t3_stream_fork`, and `t4_dual_stream_join`; the runner expands them into the
corresponding `composed_*` task packages and records the selected topology ID in
sample metadata.
The run summary also reports metadata breakdowns, pass-level breakdowns, and a
calibration matrix with per-group L3 pass rates, L0 contract-failure counts, and
cross-file consistency error rates for natural LLM failure collection. It also
reports global contract metrics, including the cross-file consistency error
rate derived from L0 System-HIS/manifest failures.

```bash
set -a
source .env
set +a

python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_baseline_a.example.yaml \
  --run-id deepseek-baseline-a \
  --preflight

python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_baseline_a.example.yaml \
  --run-id deepseek-baseline-a
```

Use `configs/sr2fpga_baseline_a.example.yaml` for measurement point (a): a
frontier-model first attempt with `repair_provider: none`, `max_attempts: 1`,
synthetic failure injection disabled, and `env_file: .env` so the runner can
load the local ignored DeepSeek key file automatically. Use
`configs/sr2fpga_agent.example.yaml` for the tool-loop repair smoke path,
measurement point (b). The preflight output includes a planned sample preview
with `sample_id`, source, task type, requirement style, requirement text,
difficulty tier, topology ID, failure origin, and measurement point. Baseline
(a) sets `requirement_style: natural_component`, which deterministically
surface-rewrites component-topology prompts into more natural engineering
language while preserving the same topology contracts for prompt audit before
API calls. It also reports the `DEEPSEEK_API_KEY` source and a short non-secret
fingerprint so local `.env` key updates are visible without printing the key.
Use `--preflight --validate-provider` to make a minimal DeepSeek authentication
request before launching generation; this catches invalid keys before any RTL
sample is attempted.

Run state, `summary.json`, and the automatically generated
`baseline_report.md` live under `tmp/sr2fpga_runs/<run-id>/`. The report also
groups source, failure origin, requirement style, difficulty tier, topology ID,
and measurement point, then flags the first difficulty tier whose L3 pass rate
drops below the knee threshold, defaulting to 80%. Keep those logs local by
default. Commit only milestone dataset snapshots or compact summaries when they
are useful for research traceability.
`run_state.json` records a config fingerprint, and resume rejects a run when
the same run ID is reused with a different config.

Regenerate the compact baseline table manually if you edit or copy a
`summary.json`:

```bash
python3 -m LLM.src.sr2fpga_agent.baseline_report \
  --summary tmp/sr2fpga_runs/deepseek-baseline-a/summary.json \
  --knee-threshold 0.8 \
  --output tmp/sr2fpga_runs/deepseek-baseline-a/baseline_report.md
```

To intentionally collect repair trajectories, add task-level
`failure_injectors`. Supported injectors are `rename_reset_port`,
`missing_manifest_source`, `wrong_top_module`, `width_mismatch`,
`testbench_expected_value_mismatch`, `constraint_missing_clock`, and
`multimodule_connection_mismatch`; omit the field or use an empty list for
normal generation.

Each sample records generated project files under `attempts/` and `final/`,
plus metadata, labels, and measured QoR. Before Verilator/Icarus/Yosys run, the
agent performs an L0 System-HIS/manifest consistency check so packaging and
cross-file contract errors are recorded as first-class failures.

## Quick Workflow: Deploy First

In Ubuntu/WSL on the cloud server:

```bash
mkdir -p /mnt/e/Aowen/repos
cd /mnt/e/Aowen/repos
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga

bash LLM/scripts/setup_server.sh
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
```

Download or prepare Gemma 4. Current working route:

```bash
python -m pip install -U modelscope
modelscope download \
  --model google/gemma-4-12B-it \
  --local_dir /mnt/e/Aowen/models/gemma-4-12B-it
```

### Gemma Transformers Test

```bash
python test_gemma_transformers.py
```

The test uses `tokenizer.apply_chat_template`, deterministic decoding, an EOS
token, a padding token, and eager attention.

### Gemma vLLM Compatibility Test

```bash
cp LLM/configs/serve_vllm.env.example LLM/configs/serve_vllm.env
bash LLM/scripts/serve_vllm.sh
```

The Gemma script deliberately omits `--limit-mm-per-prompt`, so the previous
extra-closing-brace JSON error cannot recur.

### Recommended Qwen vLLM Service

Recommended Qwen model directory:

```text
E:\Aowen\models\Qwen2.5-Coder-7B-Instruct
```

Its WSL path is:

```text
/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

Start the verified service:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
sed -i 's/\r$//' LLM/scripts/*.sh
bash LLM/scripts/serve_qwen_vllm.sh
```

The script disables the FlashInfer sampler by default because the current WSL
environment has the NVIDIA runtime but no CUDA Toolkit or `nvcc`. vLLM falls
back to its PyTorch sampler while continuing to run the model on the GPU.

If the model is still in the old C-drive location, use this temporarily:

```bash
QWEN_MODEL_PATH=/mnt/c/Users/Administrator/models/Qwen2.5-Coder-7B-Instruct \
  bash LLM/scripts/serve_qwen_vllm.sh
```

Test the OpenAI-compatible API:

```bash
BASE_URL=http://127.0.0.1:8000/v1 bash LLM/scripts/test_api.sh
```

From Windows PowerShell, use `Invoke-RestMethod` so JSON and Chinese text are
encoded correctly:

```powershell
$body = @{
    model = "cuc-ai-fpga"
    messages = @(
        @{
            role = "user"
            content = "请写一个可综合的 Verilog 8位同步计数器，包含 clk、rst_n、en、count 端口，只输出代码。"
        }
    )
    temperature = 0.2
    max_tokens = 512
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body ([Text.Encoding]::UTF8.GetBytes($body))

$response.choices[0].message.content
```

The server exposes an OpenAI-compatible API at `http://127.0.0.1:8000/v1` inside WSL. Use SSH port forwarding rather than exposing port `8000` publicly.

For detailed deployment steps, see `LLM/DEPLOY.md`.

## Optional Workflow: Fine-Tune Later

### First Smoke Training Run

Use the tiny built-in Verilog dataset first. This is only for validating the
training pipeline, not for model quality:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate

python -m LLM.src.prepare_dataset \
  --input LLM/data/examples/smoke_verilog_raw.jsonl \
  --output LLM/data/train.jsonl

mkdir -p /mnt/e/Aowen/runs
bash LLM/scripts/train_lora.sh LLM/configs/train_qwen_smoke.yaml
```

The smoke config uses the verified local Qwen path:

```text
/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

It runs only `10` optimizer steps with QLoRA and writes the adapter to the
persistent E drive:

```text
/mnt/e/Aowen/runs/qwen2_5_coder_7b_smoke_lora
```

If this run finishes, the environment, tokenizer, dataset conversion, LoRA
setup, and adapter saving path are all working.

### SR2FPGA Export Dry-Run

Before training on SR2FPGA trajectory exports, run a no-model dry-run over the
converted chat JSONL. This validates the `messages` structure consumed by
`train_lora.py` and reports estimated sequence lengths:

```bash
python -m LLM.src.training_dry_run \
  --input tmp/t0_t4_requirement_to_project.chat.jsonl \
  --max-seq-length 65536 \
  --fail-on-truncation
```

The current deterministic T0-T4 `requirement_to_project` samples contain full
project files on the assistant side, even though the canonical T0-T4
requirements use short `simple_prompt` user intent. They do not fit short smoke
settings such as `2048` estimated tokens; use long-context training or split the
project-generation task before a real run.

For a first short-context SR2FPGA SFT smoke, train the file-level `REQ2FILE`
view and exclude `system_his.json` rows:

```bash
python -m LLM.src.prepare_dataset \
  --input datasets/sr2fpga_rtl_v1_exports/requirement_to_file.jsonl \
  --output LLM/data/t0_t4_req2file_short.chat.jsonl \
  --sample-id-prefix sample_t0_t4_deterministic_smoke_ \
  --exclude-file-path system_his.json

python -m LLM.src.training_dry_run \
  --config LLM/configs/train_qwen_req2file_short.yaml \
  --fail-on-truncation

bash LLM/scripts/train_lora.sh LLM/configs/train_qwen_req2file_short.yaml
```

Build the matching eval prompt set before serving the trained adapter:

```bash
python -m LLM.src.req2file_eval build \
  --input datasets/sr2fpga_rtl_v1_exports/requirement_to_file.jsonl \
  --output tmp/req2file_eval/t0_t4_req2file_eval.jsonl \
  --sample-id-prefix sample_t0_t4_deterministic_smoke_ \
  --exclude-file-path system_his.json
```

Run inference through the local OpenAI-compatible vLLM endpoint. The `infer`
command does not request JSON-only output because `REQ2FILE` must generate
Verilog, SDC, and JSON file contents:

```bash
python -m LLM.src.req2file_eval infer \
  --input tmp/req2file_eval/t0_t4_req2file_eval.jsonl \
  --output tmp/req2file_eval/t0_t4_req2file_predictions.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --api-key EMPTY \
  --model Qwen2.5-Coder-7B-Instruct \
  --max-tokens 4096

python -m LLM.src.req2file_eval score \
  --input tmp/req2file_eval/t0_t4_req2file_predictions.jsonl \
  --output tmp/req2file_eval/t0_t4_req2file_score.json

python -m LLM.src.req2file_eval assemble \
  --input tmp/req2file_eval/t0_t4_req2file_predictions.jsonl \
  --output-root tmp/req2file_eval/assembled \
  --reference-dataset-root datasets/sr2fpga_rtl_v1 \
  --backfill-reference-path system_his.json

python -m LLM.src.req2file_eval verify-static \
  --project-root tmp/req2file_eval/assembled \
  --output tmp/req2file_eval/t0_t4_req2file_static_report.json

python -m LLM.src.req2file_eval verify-tools \
  --project-root tmp/req2file_eval/assembled \
  --output tmp/req2file_eval/t0_t4_req2file_tools_report.json

python -m LLM.src.req2file_eval verify-synth \
  --project-root tmp/req2file_eval/assembled \
  --output tmp/req2file_eval/t0_t4_req2file_synth_report.json
```

`system_his.json` is backfilled from the reference dataset only for this
project-consistency check; it is not part of the short-context `REQ2FILE`
training target. `verify-tools` runs Verilator lint plus Icarus compile/run, and
`verify-synth` runs Yosys synthesis and records parsed QoR cell counts when
those tools are installed.

### Custom Training Data

Prepare training data:

```bash
cp /path/to/raw.jsonl LLM/data/raw.jsonl
python -m LLM.src.prepare_dataset --input LLM/data/raw.jsonl --output LLM/data/train.jsonl
```

Edit `LLM/configs/train_lora.yaml`, then train:

```bash
bash LLM/scripts/train_lora.sh
```

Merge the LoRA adapter for serving:

```bash
BASE_MODEL=google/gemma-4-12B-it \
ADAPTER_PATH=LLM/runs/gemma4_12b_lora \
OUTPUT_PATH=LLM/merged/gemma4_12b_fpga \
bash LLM/scripts/merge_lora.sh
```

After merging, edit `LLM/configs/serve_vllm.env`:

```bash
MODEL_PATH=LLM/merged/gemma4_12b_fpga
```

For a 24GB RTX 4090, start with QLoRA, `per_device_train_batch_size: 1`, and gradient accumulation. If training hits CUDA out-of-memory, reduce `max_seq_length` from `2048` to `1024` before changing the model.

## Data Format

`prepare_dataset.py` accepts these JSONL row formats:

```jsonl
{"instruction":"Write Verilog for a 2-input AND gate.","input":"Use module name and2.","output":"module and2(...); endmodule"}
{"prompt":"Explain FPGA timing closure.","completion":"Timing closure means ..."}
{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```

## Git Hygiene

Do commit source code, scripts, configs, and small documentation. Do not commit
model weights, raw datasets, trained adapters, merged models, virtual
environments, server-specific `.env` files, or real API keys. Keep the real
`DEEPSEEK_API_KEY` only in a local ignored `.env` file or in the current shell;
tracked docs and configs should mention only the variable name.
