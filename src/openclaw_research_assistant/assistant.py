from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from .config import StrategyConfig, load_strategy
from .providers import synthesize_report
from .tools import nba_recent_player_stats, stock_option_snapshot, web_search


def gather_research_payload(cfg: StrategyConfig) -> Dict[str, Any]:
    nba = {
        "players": [
            nba_recent_player_stats(name, cfg.assistant.nba_games_to_analyze)
            for name in cfg.nba.watch_players
        ],
        "search": [
            {
                "query": f"NBA {team} {term}",
                "results": web_search(
                    f"NBA {team} {term}", max_results=cfg.assistant.max_web_results
                ),
            }
            for team in cfg.nba.watch_teams
            for term in cfg.nba.query_terms
        ],
    }

    stocks = {
        "symbols": [stock_option_snapshot(sym) for sym in cfg.stocks.watch_symbols],
        "search": [
            {
                "query": f"{symbol} {term}",
                "results": web_search(
                    f"{symbol} {term}", max_results=cfg.assistant.max_web_results
                ),
            }
            for symbol in cfg.stocks.watch_symbols
            for term in cfg.stocks.query_terms
        ],
    }

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "nba": nba,
        "stocks": stocks,
    }


def save_report(markdown: str, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = report_dir / f"research_{stamp}.md"
    out_path.write_text(markdown, encoding="utf-8")
    return out_path


def save_raw_payload(payload: Dict[str, Any], report_path: Path) -> Path:
    json_path = report_path.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json_path


def run(strategy_path: Path, report_dir: Path) -> Path:
    load_dotenv()
    cfg = load_strategy(strategy_path)

    payload = gather_research_payload(cfg)
    memo = synthesize_report(
        model=cfg.assistant.model,
        temperature=cfg.assistant.temperature,
        payload=payload,
    )

    report_path = save_report(memo, report_dir)
    save_raw_payload(payload, report_path)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenClaw research assistant runner")
    parser.add_argument(
        "--strategy",
        default="config/strategy.yaml",
        help="Path to strategy YAML",
    )
    parser.add_argument(
        "--report-dir",
        default="data/reports",
        help="Directory for generated markdown reports",
    )
    args = parser.parse_args()

    path = run(Path(args.strategy), Path(args.report_dir))
    print(f"Research memo generated: {path}")


if __name__ == "__main__":
    main()
