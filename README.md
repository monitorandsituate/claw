# OpenClaw — Autonomous Research Agent (Telegram + Ollama)

A local-first, self-improving AI research agent you talk to through **Telegram**.
It runs on your MacBook, uses **Ollama** for free local LLMs, and has full access
to its own repository so it can iterate and improve itself.

> [!IMPORTANT]
> This project is for research and education only. It is **not financial advice** and **not betting advice**.

## What you get

- **Telegram chatbot** — talk to OpenClaw from your phone or desktop.
- **Tool-calling agent** — the LLM can autonomously search the web, pull
  stock/options data, fetch NBA stats, read/write repo files, and run shell
  commands.
- **Self-improvement** — ask the agent to add features or fix bugs; it reads its
  own source, writes changes, and commits them.
- **Research cycles** — one command gathers market + sports data and synthesises
  a daily memo via Ollama.
- **One-script setup** — clone, run `setup.sh`, done.

## Repository layout

```text
.
├── config/
│   ├── strategy.example.yaml
│   └── strategy.yaml               # your local settings
├── data/
│   └── reports/                     # generated markdown reports
├── logs/
├── scripts/
│   ├── setup.sh                     # <-- one-command setup
│   ├── run_telegram.sh              # start the Telegram bot
│   ├── bootstrap_mac.sh             # lower-level bootstrap
│   ├── run_assistant.sh             # headless research cycle
│   ├── install_launchd.sh           # optional scheduled runs
│   └── doctor.sh                    # health checks
├── src/openclaw_research_assistant/
│   ├── __init__.py
│   ├── agent.py                     # core agent + tool-calling loop
│   ├── assistant.py                 # research cycle runner
│   ├── config.py                    # strategy YAML loader
│   ├── providers.py                 # Ollama HTTP integration
│   ├── telegram_bot.py              # Telegram interface
│   └── tools.py                     # web, stock, NBA tools
├── .env.example
├── requirements.txt
├── Makefile
└── README.md
```

## Quick start (MacBook)

### 1) Clone

```bash
git clone https://github.com/monitorandsituate/claw.git
cd claw
```

### 2) Run setup

```bash
bash scripts/setup.sh
```

This single script:
1. Installs **Homebrew** (if missing)
2. Installs **Python 3** and **Ollama**
3. Pulls the default Ollama model (`llama3.1:8b`)
4. Creates a Python virtual environment and installs dependencies
5. Copies config templates
6. Prompts you for a **Telegram bot token** (get one from
   [@BotFather](https://t.me/BotFather))
7. Offers to start the Telegram bot immediately

### 3) Get a Telegram bot token

1. Open Telegram and message **@BotFather**.
2. Send `/newbot` and follow the prompts.
3. Copy the token and paste it when `setup.sh` asks (or add it to `.env`
   manually as `TELEGRAM_BOT_TOKEN=<your-token>`).

### 4) Talk to OpenClaw

Open a chat with your new bot in Telegram and send `/start`.

**Commands:**
| Command | Description |
|---------|-------------|
| `/start` | Show welcome message |
| `/research` | Run a full research cycle |
| `/status` | Check system health |
| `/reset` | Clear conversation history |
| `/improve <desc>` | Ask the agent to improve its own code |

Or just type a free-form message — the agent will respond conversationally and
use tools as needed.

## Running the bot manually

```bash
bash scripts/run_telegram.sh
```

## Running a headless research cycle (no Telegram)

```bash
bash scripts/run_assistant.sh
```

Output lands in `data/reports/research_YYYYMMDD_HHMMSS.md`.

## Optional: scheduled daily runs

```bash
bash scripts/install_launchd.sh
```

Runs at 07:00 local time via macOS `launchd`.

## Configuration

Edit `config/strategy.yaml` to customise:
- NBA players / teams / query terms
- Stock symbols / query terms
- LLM model and temperature

Edit `.env` for:
- `TELEGRAM_BOT_TOKEN` — required for Telegram mode
- `TELEGRAM_ALLOWED_CHAT_IDS` — optional comma-separated whitelist
- `OLLAMA_MODEL` — default `llama3.1:8b`
- `OLLAMA_HOST` — default `http://127.0.0.1:11434`

## How the agent works

1. You send a message via Telegram.
2. The bot forwards it to the **Agent** class which maintains conversation
   history per chat.
3. The agent calls Ollama's `/api/chat` with **tool definitions** (web search,
   stock data, NBA stats, file read/write, shell commands, research cycle).
4. If Ollama returns tool calls, the agent executes them and feeds results back.
5. This loop continues (up to 15 iterations) until the model produces a final
   text response.
6. The response is sent back to you in Telegram.

For self-improvement, the agent reads its own source files, writes changes, and
can commit via `git`.

## Security notes

- All LLM inference stays **local** (Ollama).
- The agent can run shell commands inside the repo — review `TELEGRAM_ALLOWED_CHAT_IDS`
  to restrict access.
- API usage is minimal (DuckDuckGo, yfinance, balldontlie — all free/public).
- Consider FileVault + separate non-admin macOS user account.

## Troubleshooting

```bash
bash scripts/doctor.sh
```

- **SSL errors**: re-run `bash scripts/bootstrap_mac.sh`
- **Stale code**: `git pull --ff-only`
- **Ollama not responding**: `ollama serve` (or restart via `brew services restart ollama`)
- **NBA data unavailable**: the run continues and records errors in the report
