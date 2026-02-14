"""Telegram interface for the OpenClaw agent.

Run directly:  python -m openclaw_research_assistant.telegram_bot
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Set

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .agent import Agent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_agent(context: ContextTypes.DEFAULT_TYPE) -> Agent:
    """Lazily initialise a single Agent instance in bot_data."""
    if "agent" not in context.bot_data:
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))
        context.bot_data["agent"] = Agent(model=model, temperature=temperature)
    return context.bot_data["agent"]


def _allowed_chat_ids() -> Optional[Set[int]]:
    raw = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return None
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


async def _send_long(update: Update, text: str) -> None:
    """Send a reply, splitting at Telegram's 4096-char limit."""
    if not text:
        text = "(no response)"
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i : i + 4000])


def _is_allowed(update: Update) -> bool:
    allowed = _allowed_chat_ids()
    if allowed is None:
        return True
    return update.effective_chat.id in allowed


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "OpenClaw agent online.\n\n"
        "Commands:\n"
        "/research  — run a full research cycle\n"
        "/status    — system health check\n"
        "/reset     — clear conversation\n"
        "/improve <desc> — self-improve the codebase\n\n"
        "Or just send a message to chat."
    )


async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    agent = _get_agent(context)
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("Running research cycle — this may take a few minutes …")
    try:
        reply = agent.chat(
            chat_id,
            "Run a full research cycle using run_research_cycle and summarise the key findings.",
        )
        await _send_long(update, reply)
    except Exception as exc:
        logger.exception("research command failed")
        await update.message.reply_text(f"Research cycle failed: {exc}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    agent = _get_agent(context)
    chat_id = str(update.effective_chat.id)
    try:
        reply = agent.chat(
            chat_id,
            "Check system status: is Ollama reachable? Does config/strategy.yaml exist? "
            "List recent reports. Give a short summary.",
        )
        await _send_long(update, reply)
    except Exception as exc:
        logger.exception("status command failed")
        await update.message.reply_text(f"Status check failed: {exc}")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    agent = _get_agent(context)
    agent.reset(str(update.effective_chat.id))
    await update.message.reply_text("Conversation history cleared.")


async def cmd_improve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    agent = _get_agent(context)
    chat_id = str(update.effective_chat.id)
    description = " ".join(context.args) if context.args else "general improvements"
    await update.message.reply_text(f"Working on: {description}")
    try:
        reply = agent.chat(
            chat_id,
            f"Improve the codebase: {description}. "
            "Read relevant files, implement changes, write them back, "
            "then run 'git add -A && git commit -m \"<message>\"' to commit. "
            "Explain what you changed.",
        )
        await _send_long(update, reply)
    except Exception as exc:
        logger.exception("improve command failed")
        await update.message.reply_text(f"Improvement failed: {exc}")


# ---------------------------------------------------------------------------
# Free-form message handler
# ---------------------------------------------------------------------------


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    agent = _get_agent(context)
    chat_id = str(update.effective_chat.id)
    user_text = update.message.text or ""
    try:
        reply = agent.chat(chat_id, user_text)
        await _send_long(update, reply)
    except Exception as exc:
        logger.exception("message handler error")
        await update.message.reply_text(f"Error: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not set. "
            "Create a bot via @BotFather on Telegram and add the token to .env"
        )

    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        level=logging.INFO,
    )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("improve", cmd_improve))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("OpenClaw Telegram bot starting (model=%s) …", os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
