#!/usr/bin/env bash
# Start the OpenClaw Telegram bot.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ---- virtual-env check -----------------------------------------------------
if [[ ! -d ".venv" ]]; then
  echo "Virtual environment missing. Run:  bash scripts/setup.sh"
  exit 1
fi

source .venv/bin/activate

# ---- fix SSL certs (Homebrew Python can leave SSL_CERT_FILE dangling) ------
if [[ -n "${SSL_CERT_FILE:-}" ]] && [[ ! -f "${SSL_CERT_FILE}" ]]; then
  export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())" 2>/dev/null || true)
fi
if [[ -z "${SSL_CERT_FILE:-}" ]]; then
  export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())" 2>/dev/null || true)
fi

# ---- ensure Ollama is running ----------------------------------------------
if ! pgrep -qx "ollama" 2>/dev/null; then
  echo "Starting Ollama daemon …"
  ollama serve &>/dev/null &
  sleep 3
fi

# ---- load .env and launch --------------------------------------------------
set -a; source .env 2>/dev/null || true; set +a

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN not set in .env"
  echo "Get one from @BotFather on Telegram, then add it to .env"
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

echo "Starting OpenClaw Telegram bot …"
exec python -m openclaw_research_assistant.telegram_bot
