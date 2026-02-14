from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class AssistantSettings(BaseModel):
    model: str = "llama3.1:8b"
    temperature: float = 0.2
    max_web_results: int = 5
    nba_games_to_analyze: int = 8


class NbaSettings(BaseModel):
    watch_players: List[str] = Field(default_factory=list)
    watch_teams: List[str] = Field(default_factory=list)
    query_terms: List[str] = Field(default_factory=list)


class StockSettings(BaseModel):
    watch_symbols: List[str] = Field(default_factory=list)
    query_terms: List[str] = Field(default_factory=list)


class OutputSettings(BaseModel):
    include_risk_section: bool = True


class StrategyConfig(BaseModel):
    assistant: AssistantSettings = Field(default_factory=AssistantSettings)
    nba: NbaSettings = Field(default_factory=NbaSettings)
    stocks: StockSettings = Field(default_factory=StockSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)


def load_strategy(path: Path) -> StrategyConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Strategy file not found at {path}. Copy config/strategy.example.yaml -> config/strategy.yaml"
        )

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return StrategyConfig.model_validate(raw)
