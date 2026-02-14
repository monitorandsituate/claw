"""OpenClaw autonomous agent with Ollama tool-calling loop.

Provides a conversational agent that can use tools to perform research,
read/modify the repository, and run shell commands.  Designed to be driven
by the Telegram bot but can also be used standalone.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .providers import ollama_host
from .tools import nba_recent_player_stats, stock_option_snapshot, web_search

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Tool definitions (OpenAI-compatible format used by Ollama)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web via DuckDuckGo. "
                "Returns a list of {title, href, body} dicts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default 5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_snapshot",
            "description": (
                "Fetch current price, key metrics, and top options chain "
                "entries for a stock ticker symbol."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol, e.g. AAPL",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nba_stats",
            "description": "Get recent game averages for an NBA player.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_name": {
                        "type": "string",
                        "description": "Full or partial player name",
                    },
                    "games": {
                        "type": "integer",
                        "description": "Number of recent games (default 8)",
                    },
                },
                "required": ["player_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of a file inside the repository. "
                "Path is relative to the repo root."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path, e.g. src/openclaw_research_assistant/tools.py",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create or overwrite a file in the repository. "
                "Parent directories are created automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from repo root",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and sub-directories. Use '.' for repo root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path (default '.')",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": (
                "Execute a shell command inside the repo directory. "
                "Useful for git, tests, pip, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to run",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_research_cycle",
            "description": (
                "Run a full research cycle: gather NBA stats, stock data, "
                "and web searches, then synthesize a daily memo via Ollama."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

_BLOCKED_COMMANDS = ["rm -rf /", "sudo rm", "mkfs", "dd if=", "> /dev/sd"]


def _execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Run a single tool and return its result as a string."""
    try:
        if name == "web_search":
            result = web_search(
                arguments["query"], arguments.get("max_results", 5)
            )
            return json.dumps(result, indent=2, default=str)

        if name == "stock_snapshot":
            result = stock_option_snapshot(arguments["symbol"])
            return json.dumps(result, indent=2, default=str)

        if name == "nba_stats":
            result = nba_recent_player_stats(
                arguments["player_name"], arguments.get("games", 8)
            )
            return json.dumps(result, indent=2, default=str)

        if name == "read_file":
            filepath = (REPO_ROOT / arguments["path"]).resolve()
            if not filepath.is_relative_to(REPO_ROOT):
                return "Error: path escapes repository root"
            if not filepath.exists():
                return f"Error: file not found: {arguments['path']}"
            text = filepath.read_text(encoding="utf-8", errors="replace")
            if len(text) > 12000:
                text = text[:12000] + "\n... (truncated)"
            return text

        if name == "write_file":
            filepath = (REPO_ROOT / arguments["path"]).resolve()
            if not filepath.is_relative_to(REPO_ROOT):
                return "Error: path escapes repository root"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(arguments["content"], encoding="utf-8")
            return f"Wrote {len(arguments['content'])} bytes to {arguments['path']}"

        if name == "list_directory":
            dirpath = (REPO_ROOT / arguments.get("path", ".")).resolve()
            if not dirpath.is_relative_to(REPO_ROOT):
                return "Error: path escapes repository root"
            if not dirpath.is_dir():
                return f"Error: not a directory: {arguments['path']}"
            entries = sorted(dirpath.iterdir())
            lines = [
                f"{'[dir]  ' if e.is_dir() else '[file] '}{e.name}"
                for e in entries
                if e.name != ".git"
            ]
            return "\n".join(lines) if lines else "(empty directory)"

        if name == "run_shell":
            cmd = arguments["command"]
            if any(b in cmd for b in _BLOCKED_COMMANDS):
                return "Error: command blocked for safety"
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=120,
            )
            output = proc.stdout
            if proc.stderr:
                output += f"\nSTDERR: {proc.stderr}"
            if proc.returncode != 0:
                output += f"\nExit code: {proc.returncode}"
            return output[:6000] if output else "(no output)"

        if name == "run_research_cycle":
            from .assistant import run as run_assistant

            strategy_path = REPO_ROOT / "config" / "strategy.yaml"
            report_dir = REPO_ROOT / os.getenv("REPORT_DIR", "data/reports")
            if not strategy_path.exists():
                return (
                    "Error: config/strategy.yaml not found. "
                    "Copy from config/strategy.example.yaml first."
                )
            path = run_assistant(strategy_path, report_dir)
            return f"Research cycle complete. Report saved to: {path}"

        return f"Error: unknown tool '{name}'"

    except Exception as exc:  # noqa: BLE001
        logger.exception("Tool %s failed", name)
        return f"Error executing {name}: {exc}"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are **OpenClaw**, an autonomous AI research assistant and software engineer.

You are running locally on the user's Mac, communicating via Telegram.
You have full access to your own repository and can read, modify, and improve it.

### Capabilities
- **Research**: search the web, pull stock/options snapshots, fetch NBA stats.
- **Repo access**: read files, write files, list directories.
- **Shell**: run git, tests, pip, or other commands in the repo.
- **Research cycle**: trigger a full gather-and-synthesize research run.
- **Self-improvement**: iterate on your own codebase to add features or fix bugs.

### Guidelines
1. Be concise but thorough.
2. When modifying code, read the file first, make targeted changes, and verify.
3. Commit meaningful improvements with clear git messages.
4. Never fabricate data — if a tool returns an error, say so.
5. For multi-step tasks, work through them systematically and report progress.
"""

# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

MAX_TOOL_ITERATIONS = 15
MAX_CONVERSATION_MESSAGES = 60


class Agent:
    """Conversational agent backed by Ollama with tool-calling."""

    def __init__(
        self,
        model: str = "llama3.1:8b",
        temperature: float = 0.3,
    ) -> None:
        self.model = model
        self.temperature = temperature
        # chat_id -> message list
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}

    # -- conversation management ---------------------------------------------

    def _get_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        if chat_id not in self._conversations:
            self._conversations[chat_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self._conversations[chat_id]

    def _trim(self, msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(msgs) <= MAX_CONVERSATION_MESSAGES:
            return msgs
        return [msgs[0]] + msgs[-(MAX_CONVERSATION_MESSAGES - 1) :]

    def reset(self, chat_id: str) -> None:
        self._conversations.pop(chat_id, None)

    # -- main chat loop ------------------------------------------------------

    def chat(self, chat_id: str, user_message: str) -> str:
        """Send *user_message* through the agent loop and return the reply."""
        msgs = self._get_messages(chat_id)
        msgs.append({"role": "user", "content": user_message})
        msgs = self._trim(msgs)
        self._conversations[chat_id] = msgs

        for iteration in range(MAX_TOOL_ITERATIONS):
            logger.info("Agent iteration %d for chat %s", iteration, chat_id)

            body = self._call_ollama(msgs)
            msg = body.get("message", {})

            tool_calls = msg.get("tool_calls") or []

            if not tool_calls:
                # Final textual answer
                content = msg.get("content", "").strip()
                if content:
                    msgs.append({"role": "assistant", "content": content})
                    self._conversations[chat_id] = msgs
                    return content
                # Empty content and no tool calls — break to fallback
                break

            # The model wants to call tools
            msgs.append(msg)  # record assistant turn with tool_calls

            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name", "unknown")
                try:
                    tool_args = fn.get("arguments", {})
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)
                except (json.JSONDecodeError, TypeError):
                    tool_args = {}

                logger.info("Calling tool %s(%s)", tool_name, tool_args)
                result = _execute_tool(tool_name, tool_args)
                msgs.append({"role": "tool", "content": result})

        return "I completed the available tool steps. Let me know if you need anything else."

    # -- Ollama HTTP call ----------------------------------------------------

    def _call_ollama(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{ollama_host().rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
            "options": {"temperature": self.temperature},
            "stream": False,
        }
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()
