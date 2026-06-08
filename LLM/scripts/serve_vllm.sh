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
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-cuc-ai-fpga}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-2048}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-1}"
CPU_OFFLOAD_GB="${CPU_OFFLOAD_GB:-8}"
DTYPE="${DTYPE:-bfloat16}"
TRUST_REMOTE_CODE="${TRUST_REMOTE_CODE:-false}"
LIMIT_MM_PER_PROMPT="${LIMIT_MM_PER_PROMPT:-{\"image\":0,\"audio\":0}}"
ENFORCE_EAGER="${ENFORCE_EAGER:-false}"

ARGS=(
  --model "$MODEL_PATH" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --max-model-len "$MAX_MODEL_LEN" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --cpu-offload-gb "$CPU_OFFLOAD_GB" \
  --dtype "$DTYPE"
)

if [ -n "$LIMIT_MM_PER_PROMPT" ]; then
  ARGS+=(--limit-mm-per-prompt "$LIMIT_MM_PER_PROMPT")
fi

if [ "$TRUST_REMOTE_CODE" = "true" ]; then
  ARGS+=(--trust-remote-code)
fi

if [ "$ENFORCE_EAGER" = "true" ]; then
  ARGS+=(--enforce-eager)
fi

python -m vllm.entrypoints.openai.api_server "${ARGS[@]}"
