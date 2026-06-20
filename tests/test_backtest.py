"""Test del motore di backtest su dati sintetici. Nessuna rete, nessuna credenziale."""
import numpy as np
import pandas as pd

from src.backtest.backtest_engine import CostModel, run_backtest, walk_forward
from src.core import reporting
from src.core.risk_manager import RiskParams, position_size
from src.core.strategy import LONG, make_strategy


def _synthetic_ohlc(n=1500, seed=0) -> pd.DataFrame:
    """Serie con trend alternati + rumore: dà segnali long e short."""
    rng = np.random.default_rng(seed)
    # trend a tratti
    trend = np.concatenate([
        np.linspace(0, 5, n // 3),
        np.linspace(5, 1, n // 3),
        np.linspace(1, 6, n - 2 * (n // 3)),
    ])
    noise = np.cumsum(rng.normal(0, 0.05, n))
    close = 100 + trend + noise
    high = close + rng.uniform(0.05, 0.2, n)
    low = close - rng.uniform(0.05, 0.2, n)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close})


# --- metriche ---------------------------------------------------------------

def test_profit_factor():
    assert reporting.profit_factor([10, -5, 5]) == 3.0
    assert reporting.profit_factor([10, 5]) == float("inf")
    assert reporting.profit_factor([]) == 0.0


def test_max_drawdown():
    assert reporting.max_drawdown([100, 120, 60, 90]) == -0.5  # 120 -> 60


def test_position_size_scala_col_rischio():
    risk = RiskParams(risk_per_trade=0.01, atr_mult=2.0)
    size = position_size(10_000, atr=0.5, params=risk)
    # rischio 100 / distanza (2*0.5=1.0) = 100 unità
    assert abs(size - 100.0) < 1e-9


# --- engine -----------------------------------------------------------------

def test_run_backtest_produce_risultati():
    df = _synthetic_ohlc()
    strat = make_strategy("pullback", min_conditions=2)
    res = run_backtest(df, strat)
    assert res.bars == len(df)
    assert len(res.equity_curve) > 0
    assert res.metrics.n_trades >= 1
    # ogni trade ha un pnl numerico
    assert all(isinstance(p, float) for p in res.pnls)


def test_run_backtest_no_lookahead_equity_length():
    df = _synthetic_ohlc()
    strat = make_strategy("pullback")
    res = run_backtest(df, strat)
    assert len(res.equity_curve) == len(df) - strat.warmup


def test_walk_forward_ritorna_finestre():
    df = _synthetic_ohlc(n=2000)
    grid = {"ema_fast": [10, 20], "ema_slow": [50], "min_conditions": [2, 3]}
    wf = walk_forward(df, "pullback", grid, n_windows=3)
    assert len(wf.windows) >= 1
    assert isinstance(wf.oos_profit_factor, float)
    # overfitting è un bool coerente
    assert wf.overfitting in (True, False)


def test_costi_riducono_il_pnl():
    df = _synthetic_ohlc()
    strat = make_strategy("pullback", min_conditions=2)
    no_cost = run_backtest(df, strat, costs=CostModel(spread=0.0))
    with_cost = run_backtest(df, strat, costs=CostModel(spread=0.01))
    assert with_cost.metrics.final_equity < no_cost.metrics.final_equity
