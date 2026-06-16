#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

VENV_PATH="${LLM_VENV_PATH:-/mnt/e/Aowen/venvs/cuc-ai-fpga}"
mkdir -p "$(dirname "$VENV_PATH")"

python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Server environment is ready. Activate it with: source $VENV_PATH/bin/activate"
echo "If the base model requires Hugging Face access, run: huggingface-cli login"
