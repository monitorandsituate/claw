#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "No Python interpreter found (python/python3)."
  exit 1
fi

"$PYTHON_BIN" -m compileall src
"$PYTHON_BIN" -m py_compile src/openclaw_research_assistant/providers.py

if command -v rg >/dev/null 2>&1; then
  HAS_OLLAMA_IMPORT=$(rg -n "^\s*import\s+ollama\b" src/openclaw_research_assistant/providers.py || true)
else
  HAS_OLLAMA_IMPORT=$(grep -nE "^[[:space:]]*import[[:space:]]+ollama\b" src/openclaw_research_assistant/providers.py || true)
fi

if [[ -n "$HAS_OLLAMA_IMPORT" ]]; then
  echo "Unexpected direct 'import ollama' found in providers.py"
  echo "Your local checkout is likely stale. Run: git pull --ff-only"
  exit 1
fi

echo "Doctor checks passed."
