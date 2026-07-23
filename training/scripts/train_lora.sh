#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VENV_PATH="${TRAINING_VENV_PATH:-$REPO_ROOT/training/.venv}"
if [ -f "$VENV_PATH/bin/activate" ]; then
  source "$VENV_PATH/bin/activate"
fi

python -m sr2fpga_training.train_lora \
  --config "${1:-training/configs/train_lora.example.yaml}"
