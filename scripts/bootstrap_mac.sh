#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v brew >/dev/null 2>&1; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "Installing runtime dependencies..."
brew install python ollama

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Bootstrap complete."
echo "Next steps:"
echo "  1) cp config/strategy.example.yaml config/strategy.yaml"
echo "  2) cp .env.example .env"
echo "  3) ollama pull llama3.1:8b"
echo "  4) bash scripts/run_assistant.sh"
