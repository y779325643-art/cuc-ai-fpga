#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
echo "DEPRECATED: LLM/scripts/setup_server.sh -> training/scripts/setup_server.sh" >&2
exec "$REPO_ROOT/training/scripts/setup_server.sh" "$@"
