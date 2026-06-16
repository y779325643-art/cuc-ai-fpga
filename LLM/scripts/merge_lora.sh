#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

VENV_PATH="${LLM_VENV_PATH:-/mnt/e/Aowen/venvs/cuc-ai-fpga}"
if [ -f "$VENV_PATH/bin/activate" ]; then
  source "$VENV_PATH/bin/activate"
elif [ -f "LLM/.venv/bin/activate" ]; then
  source LLM/.venv/bin/activate
fi

BASE_MODEL="${BASE_MODEL:-google/gemma-4-12B-it}"
ADAPTER_PATH="${ADAPTER_PATH:-LLM/runs/gemma4_12b_lora}"
OUTPUT_PATH="${OUTPUT_PATH:-LLM/merged/gemma4_12b_fpga}"

python -m LLM.src.merge_lora \
  --base-model "$BASE_MODEL" \
  --adapter "$ADAPTER_PATH" \
  --output "$OUTPUT_PATH"
