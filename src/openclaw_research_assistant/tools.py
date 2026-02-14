from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import requests
import yfinance as yf
from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
        return [
            {
                "title": str(item.get("title", "")),
                "href": str(item.get("href", "")),
                "body": str(item.get("body", "")),
            }
            for item in results
        ]


def stock_option_snapshot(symbol: str) -> Dict[str, Any]:
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info or {}
    expirations = ticker.options

    chain_summary: List[Dict[str, Any]] = []
    if expirations:
        first_exp = expirations[0]
        chain = ticker.option_chain(first_exp)
        top_calls = chain.calls.sort_values("openInterest", ascending=False).head(5)
        top_puts = chain.puts.sort_values("openInterest", ascending=False).head(5)
        chain_summary = [
            {
                "expiration": first_exp,
                "top_calls_by_oi": top_calls[["strike", "lastPrice", "openInterest", "impliedVolatility"]]
                .to_dict(orient="records"),
                "top_puts_by_oi": top_puts[["strike", "lastPrice", "openInterest", "impliedVolatility"]]
                .to_dict(orient="records"),
            }
        ]

    return {
        "symbol": symbol,
        "as_of": datetime.utcnow().isoformat(),
        "price": info.get("lastPrice"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "year_high": info.get("yearHigh"),
        "year_low": info.get("yearLow"),
        "volume": info.get("lastVolume"),
        "options": chain_summary,
    }


def nba_recent_player_stats(player_name: str, games: int = 8) -> Dict[str, Any]:
    players_resp = requests.get(
        "https://www.balldontlie.io/api/v1/players",
        params={"search": player_name, "per_page": 1},
        timeout=20,
    )
    players_resp.raise_for_status()
    players_data = players_resp.json().get("data", [])
    if not players_data:
        return {"player": player_name, "error": "Player not found"}

    player = players_data[0]
    player_id = player["id"]

    stats_resp = requests.get(
        "https://www.balldontlie.io/api/v1/stats",
        params={"player_ids[]": player_id, "per_page": games, "postseason": False},
        timeout=20,
    )
    stats_resp.raise_for_status()
    stats = stats_resp.json().get("data", [])
    if not stats:
        return {"player": player_name, "error": "No recent stats available"}

    def avg(key: str) -> float:
        values = [float(item.get(key, 0) or 0) for item in stats]
        return round(sum(values) / max(len(values), 1), 2)

    return {
        "player": f"{player['first_name']} {player['last_name']}",
        "sample_games": len(stats),
        "averages": {
            "pts": avg("pts"),
            "reb": avg("reb"),
            "ast": avg("ast"),
            "min": avg("min"),
            "fg3m": avg("fg3m"),
            "turnover": avg("turnover"),
        },
    }
