#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -f "LLM/.venv/bin/activate" ]; then
  source LLM/.venv/bin/activate
fi

python -m LLM.src.train_lora --config "${1:-LLM/configs/train_lora.yaml}"
