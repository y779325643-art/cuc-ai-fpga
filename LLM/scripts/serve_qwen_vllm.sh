#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f "LLM/.venv/bin/activate" ]; then
  source LLM/.venv/bin/activate
fi

MODEL_PATH="${QWEN_MODEL_PATH:-/mnt/c/Users/Administrator/models/Qwen2.5-Coder-7B-Instruct}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
DTYPE="${DTYPE:-float16}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-cuc-ai-fpga}"

# The WSL image has the NVIDIA runtime but no CUDA Toolkit/nvcc. Disable the
# FlashInfer sampler so vLLM uses the PyTorch sampler without JIT compilation.
export VLLM_USE_FLASHINFER_SAMPLER="${VLLM_USE_FLASHINFER_SAMPLER:-0}"

if [ ! -d "$MODEL_PATH" ]; then
  cat >&2 <<EOF
Qwen model directory not found: $MODEL_PATH

Download it with ModelScope:
  mkdir -p /mnt/c/Users/Administrator/models
  modelscope download --model Qwen/Qwen2.5-Coder-7B-Instruct \
    --local_dir /mnt/c/Users/Administrator/models/Qwen2.5-Coder-7B-Instruct

Or start with another complete local snapshot:
  QWEN_MODEL_PATH=/path/to/Qwen2.5-Coder-7B-Instruct bash LLM/scripts/serve_qwen_vllm.sh
EOF
  exit 1
fi

vllm serve "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --dtype "$DTYPE" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --served-model-name "$SERVED_MODEL_NAME"
