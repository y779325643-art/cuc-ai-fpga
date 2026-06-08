# LLM Cloud Deployment and Fine-Tuning

Use this directory for cloud-server model deployment and later fine-tuning. The local machine prepares code and pushes it to GitHub; the cloud server clones the repository, installs dependencies, and serves the model.

Default base model: `google/gemma-4-12B-it`.

## Layout

- `configs/` - LoRA training and vLLM serving configuration templates.
- `data/` - cloud-local training data. JSONL data files are ignored by Git.
- `scripts/` - cloud setup, training, merge, and serving scripts.
- `src/` - Python entrypoints for dataset preparation, training, and adapter merge.
- `tests/` - lightweight tests for repository-side utilities.

## Recommended Workflow: Deploy First

On the cloud server:

```bash
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga
bash LLM/scripts/setup_server.sh
huggingface-cli login
```

Use a Hugging Face account that has accepted the `google/gemma-4-12B-it` model license/access terms.

Serve with vLLM:

```bash
cp LLM/configs/serve_vllm.env.example LLM/configs/serve_vllm.env
bash LLM/scripts/serve_vllm.sh
```

Test the OpenAI-compatible API:

```bash
BASE_URL=http://127.0.0.1:8000/v1 bash LLM/scripts/test_api.sh
```

The server exposes an OpenAI-compatible API at `http://<server-ip>:8000/v1`.

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
