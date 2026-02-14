# OpenClaw Autonomous Research Assistant

A lightweight, local-first research assistant designed to run on a freshly reset MacBook using **Ollama free models**.

It performs recurring research for:
- NBA prop bet signal hunting (pace/trend/usage-oriented summaries)
- Stock option idea scouting (volatility/chain/open-interest-oriented summaries)

> [!IMPORTANT]
> This project is for research and education only. It is **not financial advice** and **not betting advice**.

## What this repo gives you

- A simple Python project structure you can clone and run.
- Tooling to gather:
  - Web snippets (`duckduckgo-search`)
  - Equity/options snapshots (`yfinance`)
  - NBA player recent-game stats (`balldontlie` free API)
- An Ollama-powered synthesis layer to turn raw data into a daily memo.
- Scripts for one-command setup + optional macOS scheduled execution via `launchd`.

## Repository layout

```text
.
├── config/
│   ├── strategy.example.yaml
│   └── strategy.yaml               # your local settings (copy from example)
├── data/
│   └── reports/                    # generated markdown reports
├── logs/
├── scripts/
│   ├── bootstrap_mac.sh
│   ├── install_launchd.sh
│   └── run_assistant.sh
├── src/openclaw_research_assistant/
│   ├── __init__.py
│   ├── assistant.py
│   ├── config.py
│   ├── providers.py
│   └── tools.py
├── .env.example
├── requirements.txt
└── README.md
```

## Quick start (MacBook)

### 1) Clone

```bash
git clone <your-github-repo-url>
cd claw
```

### 2) Bootstrap machine

```bash
bash scripts/bootstrap_mac.sh
```

This script installs:
- Homebrew (if missing)
- Python 3
- Ollama
- Virtual environment + dependencies

### 3) Pull a free Ollama model

Recommended starting models:
- `llama3.1:8b`
- `qwen2.5:7b`
- `mistral:7b`

```bash
ollama pull llama3.1:8b
```

### 4) Configure strategy

```bash
cp config/strategy.example.yaml config/strategy.yaml
cp .env.example .env
```

Edit `config/strategy.yaml` with:
- NBA players/teams/watch terms
- Stock symbols/watch terms
- LLM model name

### 5) Run one research cycle

```bash
bash scripts/run_assistant.sh
```

Output report lands in:
- `data/reports/research_YYYYMMDD_HHMMSS.md`

## Optional: run automatically every morning

Install launch agent:

```bash
bash scripts/install_launchd.sh
```

By default it runs at 7:00 AM local time.

## Security notes for a freshly reset machine

- Keep API usage minimal (this project uses mostly free/public endpoints).
- Use local Ollama models so prompts/data stay on your Mac.
- Review `config/strategy.yaml` before scheduling.
- Consider FileVault + separate non-admin daily user account.

## Next improvements

- Add bookmaker odds feed integration (if you have legal access).
- Add brokerage/options API integration for higher-fidelity chain data.
- Add local vector DB for historical memo retrieval.
- Add backtesting notebook for signal validation.

## Troubleshooting

- If you previously hit an `SSL_CERT_FILE` / `FileNotFoundError` while running the assistant, re-run bootstrap to refresh dependencies:

```bash
bash scripts/bootstrap_mac.sh
```

This project talks to Ollama through its local HTTP API (`http://127.0.0.1:11434` by default), so it does not rely on the Python `ollama` package runtime.

