#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
echo "DEPRECATED: LLM/scripts/serve_qwen_vllm.sh -> training/scripts/serve_qwen_vllm.sh" >&2
exec "$REPO_ROOT/training/scripts/serve_qwen_vllm.sh" "$@"
