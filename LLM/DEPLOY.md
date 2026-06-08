# Deploy Gemma 4 12B on a Cloud Server

This guide deploys `google/gemma-4-12B-it` directly with vLLM. Fine-tuning is optional and can be added later. On Windows cloud servers, use WSL2/Ubuntu rather than native Windows Python.

## 1. Server Assumptions

- NVIDIA RTX 4090 24GB or similar CUDA GPU.
- Ubuntu/Linux cloud server, or Windows cloud server with WSL2 + Ubuntu.
- Recent NVIDIA Windows driver with CUDA support when using WSL2.
- 64GB system RAM is recommended for non-quantized CPU weight offloading.
- Python 3.10 or newer.
- A Hugging Face account that has accepted access terms for `google/gemma-4-12B-it`.

## 2. Windows Cloud Server Setup

Run these commands in **Administrator PowerShell**:

```powershell
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
wsl --update
wsl --shutdown
```

Restart the Windows server if WSL asks for it. Install or update the NVIDIA Windows driver from NVIDIA/your cloud provider before continuing.

Open **Ubuntu** from the Start menu, then run:

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip curl
nvidia-smi
```

Do not install a Linux NVIDIA driver inside WSL2. CUDA is provided through the Windows NVIDIA driver.

## 3. Clone and Install

```bash
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga
bash LLM/scripts/setup_server.sh
source LLM/.venv/bin/activate
hf auth login
```

## 4. Configure vLLM

```bash
cp LLM/configs/serve_vllm.env.example LLM/configs/serve_vllm.env
```

Default values:

```bash
MODEL_PATH=google/gemma-4-12B-it
HOST=127.0.0.1
PORT=8000
SERVED_MODEL_NAME=cuc-ai-fpga
GPU_MEMORY_UTILIZATION=0.90
MAX_MODEL_LEN=2048
MAX_NUM_SEQS=1
CPU_OFFLOAD_GB=8
DTYPE=bfloat16
TRUST_REMOTE_CODE=false
LIMIT_MM_PER_PROMPT='{"image":0,"audio":0}'
ENFORCE_EAGER=false
```

These defaults run the base model in BF16 without quantization and bind the API to localhost for safer access. Because an RTX 4090 24GB cannot comfortably hold the model weights and KV cache together, vLLM offloads 8GB of model weights to system RAM. This is slower than full-GPU inference but preserves the non-quantized model.

## 5. Start the API Server

```bash
bash LLM/scripts/serve_vllm.sh
```

The service exposes an OpenAI-compatible API:

```text
http://<server-ip>:8000/v1
```

## 6. Smoke Test

In a second terminal:

```bash
BASE_URL=http://127.0.0.1:8000/v1 bash LLM/scripts/test_api.sh
```

From your laptop, replace `127.0.0.1` with the cloud server IP after opening the cloud firewall/security group for port `8000`.

For Windows cloud servers, prefer SSH port forwarding instead of exposing port `8000` publicly:

```bash
ssh -L 8000:127.0.0.1:8000 <windows-user>@<server-ip>
```

If startup fails with CUDA out-of-memory, edit `LLM/configs/serve_vllm.env`:

```bash
MAX_MODEL_LEN=1024
GPU_MEMORY_UTILIZATION=0.85
CPU_OFFLOAD_GB=10
ENFORCE_EAGER=true
```

## 7. Later Fine-Tuning Path

When ready, use `LLM/data/`, `LLM/src/prepare_dataset.py`, `LLM/scripts/train_lora.sh`, and `LLM/scripts/merge_lora.sh` to train a LoRA adapter and switch `MODEL_PATH` to the merged model directory.
