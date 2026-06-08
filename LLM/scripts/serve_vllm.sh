#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f "LLM/.venv/bin/activate" ]; then
  source LLM/.venv/bin/activate
fi

if [ -f "LLM/configs/serve_vllm.env" ]; then
  set -a
  source LLM/configs/serve_vllm.env
  set +a
fi

MODEL_PATH="${MODEL_PATH:-google/gemma-4-12B-it}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-cuc-ai-fpga}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.92}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
DTYPE="${DTYPE:-auto}"
TRUST_REMOTE_CODE="${TRUST_REMOTE_CODE:-false}"

ARGS=(
  --model "$MODEL_PATH" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --max-model-len "$MAX_MODEL_LEN" \
  --dtype "$DTYPE"
)

if [ "$TRUST_REMOTE_CODE" = "true" ]; then
  ARGS+=(--trust-remote-code)
fi

python -m vllm.entrypoints.openai.api_server "${ARGS[@]}"
