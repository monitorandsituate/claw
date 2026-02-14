from __future__ import annotations

import json
import os
from typing import Any, Dict

import ollama


def ollama_client() -> ollama.Client:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    return ollama.Client(host=host)


def synthesize_report(model: str, temperature: float, payload: Dict[str, Any]) -> str:
    client = ollama_client()
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

    response = client.chat(
        model=model,
        options={"temperature": temperature},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"]
