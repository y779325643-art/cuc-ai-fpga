#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VENV_PATH="${TRAINING_VENV_PATH:-$REPO_ROOT/training/.venv}"
if [ -f "$VENV_PATH/bin/activate" ]; then
  source "$VENV_PATH/bin/activate"
fi

BASE_MODEL="${BASE_MODEL:-google/gemma-4-12B-it}"
ADAPTER_PATH="${ADAPTER_PATH:-artifacts/training/adapters/gemma4_12b_lora}"
OUTPUT_PATH="${OUTPUT_PATH:-artifacts/training/merged/gemma4_12b_fpga}"

python -m sr2fpga_training.merge_lora \
  --base-model "$BASE_MODEL" \
  --adapter "$ADAPTER_PATH" \
  --output "$OUTPUT_PATH"
