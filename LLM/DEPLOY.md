# Deploy Gemma 4 12B on a Cloud Server

This guide deploys `google/gemma-4-12B-it` directly with vLLM. Fine-tuning is optional and can be added later.

## 1. Server Assumptions

- NVIDIA RTX 4090 24GB or similar CUDA GPU.
- Ubuntu/Linux cloud server with recent NVIDIA driver.
- Python 3.10 or newer.
- A Hugging Face account that has accepted access terms for `google/gemma-4-12B-it`.

Check GPU visibility:

```bash
nvidia-smi
```

## 2. Clone and Install

```bash
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga
bash LLM/scripts/setup_server.sh
source LLM/.venv/bin/activate
huggingface-cli login
```

## 3. Configure vLLM

```bash
cp LLM/configs/serve_vllm.env.example LLM/configs/serve_vllm.env
```

Default values:

```bash
MODEL_PATH=google/gemma-4-12B-it
HOST=0.0.0.0
PORT=8000
SERVED_MODEL_NAME=cuc-ai-fpga
GPU_MEMORY_UTILIZATION=0.92
MAX_MODEL_LEN=4096
DTYPE=auto
TRUST_REMOTE_CODE=false
```

If the server runs out of memory, reduce `MAX_MODEL_LEN` to `2048` first.

## 4. Start the API Server

```bash
bash LLM/scripts/serve_vllm.sh
```

The service exposes an OpenAI-compatible API:

```text
http://<server-ip>:8000/v1
```

## 5. Smoke Test

In a second terminal:

```bash
BASE_URL=http://127.0.0.1:8000/v1 bash LLM/scripts/test_api.sh
```

From your laptop, replace `127.0.0.1` with the cloud server IP after opening the cloud firewall/security group for port `8000`.

## 6. Later Fine-Tuning Path

When ready, use `LLM/data/`, `LLM/src/prepare_dataset.py`, `LLM/scripts/train_lora.sh`, and `LLM/scripts/merge_lora.sh` to train a LoRA adapter and switch `MODEL_PATH` to the merged model directory.
