#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Server environment is ready. Activate it with: source LLM/.venv/bin/activate"
echo "If the base model requires Hugging Face access, run: huggingface-cli login"
