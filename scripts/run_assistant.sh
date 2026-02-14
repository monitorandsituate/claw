#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Virtual environment missing. Run: bash scripts/bootstrap_mac.sh"
  exit 1
fi

if [[ ! -f "config/strategy.yaml" ]]; then
  echo "Missing config/strategy.yaml. Copy from config/strategy.example.yaml first."
  exit 1
fi

source .venv/bin/activate

# Catch stale/broken local checkouts early (e.g. providers.py indentation/import regressions).
bash scripts/doctor.sh

export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"
python -m openclaw_research_assistant.assistant --strategy config/strategy.yaml --report-dir "${REPORT_DIR:-data/reports}"
