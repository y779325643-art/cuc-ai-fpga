#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"
MODEL="${MODEL:-cuc-ai-fpga}"

curl "$BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": \"用 Verilog 写一个 2 输入与门模块，并简短解释。必须使用模块名 and2。\"
      }
    ],
    \"temperature\": 0.2,
    \"max_tokens\": 512
  }"
