#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VENV_PATH="${TRAINING_VENV_PATH:-$REPO_ROOT/training/.venv}"
if [ -f "$VENV_PATH/bin/activate" ]; then
  source "$VENV_PATH/bin/activate"
fi

if [ -f "training/configs/local/serve_vllm.env" ]; then
  set -a
  source training/configs/local/serve_vllm.env
  set +a
fi

MODEL_PATH="${MODEL_PATH:-google/gemma-4-12B-it}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
DTYPE="${DTYPE:-float16}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-1024}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.85}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-1}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-cuc-ai-fpga}"

cat >&2 <<'EOF'
WARNING: Gemma 4 12B uses the Gemma4 Unified architecture. The current
vLLM/Transformers combination may fail during EngineCore profiling with an
attention o_proj matrix shape mismatch. Use this script for compatibility
testing; use serve_qwen_vllm.sh for the stable RTL/Verilog service path.
EOF

vllm serve "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --dtype "$DTYPE" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --trust-remote-code \
  --enforce-eager \
  --language-model-only
