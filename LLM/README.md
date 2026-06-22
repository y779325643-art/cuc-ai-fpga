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
- `rtl/top.v`
- `constraints/timing.sdc`
- `sim/tb_top.v`
- `reports/predicted_qor.json`

Current deterministic V1 task types are `counter`, `fifo`, `simple_fsm`, and
`ram_read_write`. These are intentionally small building blocks for validating
the data schema, tool pipeline, and training views before moving to larger RTL
design families.

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
supported task family, for example `fifo`, `simple_fsm`, or `ram_read_write`.

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

The API key is read only from the environment. Do not write it into repository
files or generated samples.

Each sample records generated project files under `attempts/` and `final/`,
plus labels and measured QoR under `eval/`.

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

Do commit source code, scripts, configs, and small documentation. Do not commit model weights, raw datasets, trained adapters, merged models, virtual environments, or server-specific `.env` files.
