#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

VENV_PATH="${LLM_VENV_PATH:-/mnt/e/Aowen/venvs/cuc-ai-fpga}"
if [ -f "$VENV_PATH/bin/activate" ]; then
  source "$VENV_PATH/bin/activate"
elif [ -f "LLM/.venv/bin/activate" ]; then
  source LLM/.venv/bin/activate
fi

python -m LLM.src.train_lora --config "${1:-LLM/configs/train_lora.yaml}"
