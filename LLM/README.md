# LLM Cloud Deployment and Fine-Tuning

Use this directory for cloud-server model deployment and later fine-tuning. The local machine prepares code and pushes it to GitHub; the cloud server clones the repository, installs dependencies, and serves the model. On Windows cloud servers, run the deployment inside WSL2/Ubuntu.

Current downloaded model: `google/gemma-4-12B-it`.

Recommended vLLM service model: `Qwen/Qwen2.5-Coder-7B-Instruct`.

Primary deployment guide: `LLM/DEPLOY.md`.

Current deployment decision:

- Deploy first, fine-tune later.
- Use Windows + WSL2/Ubuntu on the cloud server.
- Move the WSL distribution, project files, model files, caches, and experiment outputs under `E:\Aowen`; the current cloud setup may still be under `C:` temporarily.
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

## Quick Workflow: Deploy First

In Ubuntu/WSL on the cloud server:

```bash
# Recommended final project location after moving WSL itself to E drive:
mkdir -p /mnt/e/Aowen/repos
cd /mnt/e/Aowen/repos
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga

# If you have not moved to E drive yet, use your current project path instead:
# cd /mnt/c/WSL/cuc-ai-fpga

bash LLM/scripts/setup_server.sh
source LLM/.venv/bin/activate
```

Download or prepare Gemma 4. Current working route:

```bash
python -m pip install -U modelscope
modelscope download \
  --model google/gemma-4-12B-it \
  --local_dir /mnt/c/Users/Administrator/models/gemma-4-12B-it
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

Download Qwen to the persistent `E:` drive through ModelScope:

```bash
mkdir -p /mnt/e/Aowen/models
modelscope download \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --local_dir /mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

Then start the service:

```bash
bash LLM/scripts/serve_qwen_vllm.sh
```

The script defaults to
`/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct`. Override it only when the
model is stored elsewhere:

```bash
QWEN_MODEL_PATH=/path/to/Qwen2.5-Coder-7B-Instruct \
  bash LLM/scripts/serve_qwen_vllm.sh
```

Test the OpenAI-compatible API:

```bash
BASE_URL=http://127.0.0.1:8000/v1 bash LLM/scripts/test_api.sh
```

The server exposes an OpenAI-compatible API at `http://127.0.0.1:8000/v1` inside WSL. Use SSH port forwarding rather than exposing port `8000` publicly.

For detailed deployment steps, see `LLM/DEPLOY.md`.

## Optional Workflow: Fine-Tune Later

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
