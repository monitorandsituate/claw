#!/usr/bin/env bash
# ============================================================================
# OpenClaw — one-command setup
#
# Usage:
#   git clone https://github.com/monitorandsituate/claw.git && cd claw
#   bash scripts/setup.sh
#
# After this script finishes the Telegram bot is running in the foreground.
# Press Ctrl-C to stop it.
# ============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ---- colours ---------------------------------------------------------------
bold=$(tput bold 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)
step() { echo; echo "${bold}▸ $*${reset}"; }

# ---- 1) Homebrew -----------------------------------------------------------
step "Checking Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "Installing Homebrew …"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Make brew available in this session
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
else
  echo "Homebrew already installed."
fi

# ---- 2) System dependencies ------------------------------------------------
step "Installing system packages (python, ollama)"
brew install python ollama 2>/dev/null || true

# ---- 3) Start Ollama daemon ------------------------------------------------
step "Starting Ollama service"
if ! pgrep -qx "ollama" 2>/dev/null; then
  ollama serve &>/dev/null &
  sleep 3
  echo "Ollama daemon started."
else
  echo "Ollama already running."
fi

# ---- 4) Pull default model -------------------------------------------------
MODEL="${OLLAMA_MODEL:-llama3.1:8b}"
step "Pulling Ollama model: $MODEL"
ollama pull "$MODEL"

# ---- 5) Python virtual environment ----------------------------------------
step "Setting up Python virtual environment"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencies installed."

# ---- 6) Config files -------------------------------------------------------
step "Preparing configuration"
if [[ ! -f config/strategy.yaml ]]; then
  cp config/strategy.example.yaml config/strategy.yaml
  echo "Created config/strategy.yaml (edit to customise)."
else
  echo "config/strategy.yaml already exists — skipping."
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from template."
else
  echo ".env already exists — skipping."
fi

# ---- 7) Telegram bot token -------------------------------------------------
step "Telegram bot token"

# Source .env so we can check existing value
set -a; source .env 2>/dev/null || true; set +a

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo ""
  echo "To connect via Telegram you need a bot token."
  echo "Open Telegram, message @BotFather, send /newbot, and follow the prompts."
  echo ""
  read -rp "Paste your Telegram bot token (or press Enter to skip for now): " TOKEN
  if [[ -n "$TOKEN" ]]; then
    # Append or replace in .env
    if grep -q "^TELEGRAM_BOT_TOKEN=" .env 2>/dev/null; then
      sed -i '' "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$TOKEN|" .env
    else
      echo "" >> .env
      echo "TELEGRAM_BOT_TOKEN=$TOKEN" >> .env
    fi
    echo "Token saved to .env"
  else
    echo "Skipped — add TELEGRAM_BOT_TOKEN to .env later."
  fi
else
  echo "TELEGRAM_BOT_TOKEN already set."
fi

# ---- 8) Optional: restrict by chat ID -------------------------------------
set -a; source .env 2>/dev/null || true; set +a
if [[ -z "${TELEGRAM_ALLOWED_CHAT_IDS:-}" ]]; then
  echo ""
  echo "(Optional) You can restrict the bot to specific Telegram chat IDs."
  echo "Send /start to the bot, then check the logs for your chat ID."
  echo "Set TELEGRAM_ALLOWED_CHAT_IDS in .env as a comma-separated list."
fi

# ---- 9) Sanity check -------------------------------------------------------
step "Running doctor checks"
bash scripts/doctor.sh || true

# ---- 10) Directory scaffolding ---------------------------------------------
mkdir -p data/reports logs

# ---- Done -------------------------------------------------------------------
echo ""
echo "${bold}========================================${reset}"
echo "${bold}  OpenClaw setup complete!${reset}"
echo "${bold}========================================${reset}"
echo ""
echo "To start the Telegram bot:"
echo "  bash scripts/run_telegram.sh"
echo ""
echo "To run a one-off research cycle:"
echo "  bash scripts/run_assistant.sh"
echo ""

# If the token is set, offer to start the bot now
set -a; source .env 2>/dev/null || true; set +a
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  read -rp "Start the Telegram bot now? [Y/n] " START
  START="${START:-Y}"
  if [[ "$START" =~ ^[Yy] ]]; then
    exec bash scripts/run_telegram.sh
  fi
fi
