#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VENV_PATH="${TRAINING_VENV_PATH:-$REPO_ROOT/training/.venv}"
mkdir -p "$(dirname "$VENV_PATH")"

python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e "training[train,serve]"

echo "Server environment is ready. Activate it with: source $VENV_PATH/bin/activate"
echo "If the base model requires Hugging Face access, run: huggingface-cli login"
