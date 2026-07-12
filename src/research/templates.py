"""Template di strategia con interfaccia UNIFORME per il motore di ricerca.

Ogni template è una funzione `(df, spread) -> dict` con le stesse chiavi
(pf, win, maxdd, n, sharpe), così il motore le tratta tutte allo stesso modo.
Sono wrapper sui backtester già validati del progetto — non nuova logica.
"""
from __future__ import annotations

import pandas as pd


def _mr_indices(df: pd.DataFrame, spread: float, params: dict) -> dict:
    from src.backtest.meanrev import MeanRevConfig, backtest
    m = backtest(df, MeanRevConfig(spread_pts=spread, **params))["metrics"]
    return {"pf": m["profit_factor"], "win": m["win_rate"], "maxdd": m["max_drawdown"],
            "n": m["n_trades"], "sharpe": None}


def _mr_fx(df: pd.DataFrame, spread: float, params: dict) -> dict:
    from src.backtest.fx_meanrev import FxMeanRevConfig, backtest
    m = backtest(df, FxMeanRevConfig(spread=spread, **params))["metrics"]
    return {"pf": m["profit_factor"], "win": m["win_rate"], "maxdd": m["max_drawdown"],
            "n": m["n_trades"], "sharpe": None}


def _trend(df: pd.DataFrame, spread: float, params: dict, long_only: bool) -> dict:
    from src.backtest.backtest_engine import CostModel, run_backtest
    from src.core.risk_manager import RiskParams
    from src.core.strategy import make_strategy
    name = "donchian_long" if long_only else "donchian"
    channel = int(params.get("channel", 40))
    r = run_backtest(df, make_strategy(name, channel=channel), risk=RiskParams(),
                     costs=CostModel(spread=spread), periods_per_year=252)
    m = r.metrics
    return {"pf": m.profit_factor, "win": m.win_rate, "maxdd": m.max_drawdown,
            "n": m.n_trades, "sharpe": m.sharpe}


def _trend_long(df: pd.DataFrame, spread: float, params: dict) -> dict:
    return _trend(df, spread, params, long_only=True)


def _trend_ls(df: pd.DataFrame, spread: float, params: dict) -> dict:
    return _trend(df, spread, params, long_only=False)


TEMPLATES = {
    "mr_indices": _mr_indices,   # mean-reversion long-only (filtro trend 200)
    "mr_fx": _mr_fx,             # mean-reversion simmetrico
    "trend_long": _trend_long,   # trend-following solo-long (Donchian)
    "trend_ls": _trend_ls,       # trend-following long/short (Donchian)
}

# parametri che ciascun template accetta dal generatore (per esplorare varianti)
TEMPLATE_PARAMS = {
    "mr_indices": {"oversold": [5, 10, 15], "max_hold": [5, 10], "atr_stop": [2.0, 3.0]},
    "mr_fx": {"oversold": [5, 10, 15], "atr_stop": [2.0, 3.0]},
    "trend_long": {"channel": [20, 40, 55]},
    "trend_ls": {"channel": [20, 40, 55]},
}


def run_template(name: str, df: pd.DataFrame, spread: float, params: dict | None = None) -> dict:
    if name not in TEMPLATES:
        raise ValueError(f"Template '{name}' sconosciuto. Validi: {list(TEMPLATES)}")
    return TEMPLATES[name](df, spread, params or {})
