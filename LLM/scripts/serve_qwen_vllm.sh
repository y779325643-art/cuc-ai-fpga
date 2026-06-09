#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f "LLM/.venv/bin/activate" ]; then
  source LLM/.venv/bin/activate
fi

MODEL_PATH="${QWEN_MODEL_PATH:-Qwen/Qwen2.5-Coder-7B-Instruct}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
DTYPE="${DTYPE:-float16}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-cuc-ai-fpga}"

vllm serve "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --dtype "$DTYPE" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --served-model-name "$SERVED_MODEL_NAME"
