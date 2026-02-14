from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests


def ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


def synthesize_report(model: str, temperature: float, payload: Dict[str, Any]) -> str:
    system = (
        "You are an autonomous research analyst. "
        "Use evidence from provided data only. "
        "Do not fabricate odds, lines, or prices. "
        "Provide uncertainty notes and risk controls."
    )
    prompt = (
        "Create a concise daily memo with sections:\n"
        "1) NBA Prop Research Signals\n"
        "2) Stock Option Research Signals\n"
        "3) Risks and Invalidators\n"
        "4) Next Data To Collect\n\n"
        "Data payload JSON:\n"
        f"{json.dumps(payload, indent=2)}"
    )

    response = requests.post(
        f"{ollama_host().rstrip('/')}/api/chat",
        json={
            "model": model,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        },
        timeout=180,
    )
    response.raise_for_status()
    body = response.json()

    message = body.get("message", {})
    content = message.get("content")
    if not content:
        raise RuntimeError(f"Unexpected Ollama response format: {body}")
    return content
