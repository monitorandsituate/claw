#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m compileall src
python -m py_compile src/openclaw_research_assistant/providers.py

if rg -n "^\s*import\s+ollama\b" src/openclaw_research_assistant/providers.py >/dev/null; then
  echo "Unexpected direct 'import ollama' found in providers.py"
  exit 1
fi

echo "Doctor checks passed."
