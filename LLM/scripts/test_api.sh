#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
echo "DEPRECATED: LLM/scripts/test_api.sh -> training/scripts/test_api.sh" >&2
exec "$REPO_ROOT/training/scripts/test_api.sh" "$@"
