"""Motore di backtest event-driven + optimize() + walk_forward().

Disciplina (CLAUDE.md §5): un backtest in-sample positivo NON è un edge. La verità
si scopre out-of-sample. Per questo `walk_forward` non è opzionale: ottimizza sui
dati di training e valida su dati MAI visti. Se crolla, è overfitting e si scarta.

Modello di esecuzione, assunzioni esplicite (un backtest onesto le dichiara):
  - una posizione alla volta;
  - ingresso al CLOSE della barra del segnale (niente lookahead);
  - gestione di stop/target dalla barra SUCCESSIVA, su high/low di barra;
  - in caso di ambiguità intrabar lo stop ha precedenza sul target (caso peggiore);
  - costo = metà spread per ogni fill (round-trip = 1 spread per unità).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import pandas as pd

from src.core import reporting
from src.core.risk_manager import RiskParams, position_size, stop_distance
from src.core.strategy import FLAT, LONG, SHORT, Strategy, make_strategy


@dataclass
class CostModel:
    """Costi di transazione in unità di prezzo (es. EUR_USD spread ~0.00015)."""

    spread: float = 0.00015

    def per_fill(self, qty: float) -> float:
        return (self.spread / 2.0) * qty


@dataclass
class _Position:
    side: int
    entry: float
    size: float
    stop: float
    tp1: float
    atr: float
    remaining: float
    realized: float = 0.0
    tp1_done: bool = False


@dataclass
class BacktestResult:
    pnls: list[float]
    equity_curve: list[float]
    trades: list[dict]
    metrics: reporting.Metrics
    bars: int

    def summary(self) -> dict:
        m = self.metrics.as_dict()
        m["bars"] = self.bars
        return m


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    risk: RiskParams | None = None,
    costs: CostModel | None = None,
    initial_equity: float = 10_000.0,
    periods_per_year: float = 252 * 24,
) -> BacktestResult:
    """Esegue un backtest su un DataFrame OHLCV (colonne: open/high/low/close)."""
    risk = risk or RiskParams()
    costs = costs or CostModel()
    data = strategy.prepare(df).reset_index(drop=True)

    equity = initial_equity
    pos: _Position | None = None
    pnls: list[float] = []
    trades: list[dict] = []
    equity_curve: list[float] = []

    def close_fill(p: _Position, price: float, qty: float) -> float:
        pnl = p.side * (price - p.entry) * qty - costs.per_fill(qty)
        return pnl

    for i in range(strategy.warmup, len(data)):
        row = data.iloc[i]
        high, low, close = float(row["high"]), float(row["low"]), float(row["close"])
        atr = float(row["atr"]) if not pd.isna(row["atr"]) else 0.0

        # --- gestione posizione aperta (dalla barra successiva all'ingresso) ----
        if pos is not None:
            exited = False
            # 1) stop (precedenza, caso peggiore)
            hit_stop = low <= pos.stop if pos.side == LONG else high >= pos.stop
            if hit_stop:
                pnl = close_fill(pos, pos.stop, pos.remaining)
                pos.realized += pnl
                equity += pnl
                pnls.append(pos.realized)
                trades.append({"side": pos.side, "entry": pos.entry, "exit": pos.stop,
                               "pnl": pos.realized, "reason": "stop"})
                pos, exited = None, True

            # 2) TP1 parziale + breakeven
            if not exited and not pos.tp1_done:
                hit_tp1 = high >= pos.tp1 if pos.side == LONG else low <= pos.tp1
                if hit_tp1:
                    qty = pos.size * risk.tp1_fraction
                    pnl = close_fill(pos, pos.tp1, qty)
                    pos.realized += pnl
                    equity += pnl
                    pos.remaining -= qty
                    pos.tp1_done = True
                    pos.stop = pos.entry  # breakeven

            # 3) trailing dopo il TP1
            if not exited and pos is not None and pos.tp1_done and atr > 0:
                if pos.side == LONG:
                    pos.stop = max(pos.stop, close - risk.trail_atr_mult * atr)
                else:
                    pos.stop = min(pos.stop, close + risk.trail_atr_mult * atr)

        # --- nuovo ingresso (solo se flat) -------------------------------------
        if pos is None:
            sig = strategy.signal(data, i)
            if sig.side != FLAT and sig.atr > 0:
                dist = stop_distance(sig.atr, risk)
                size = position_size(equity, sig.atr, risk)
                if size > 0:
                    entry = close
                    stop = entry - sig.side * dist
                    tp1 = entry + sig.side * dist * risk.tp1_r
                    equity -= costs.per_fill(size)  # costo d'ingresso
                    pos = _Position(
                        side=sig.side, entry=entry, size=size, stop=stop, tp1=tp1,
                        atr=sig.atr, remaining=size, realized=-costs.per_fill(size),
                    )

        # mark-to-market per la curva equity
        unreal = 0.0
        if pos is not None:
            unreal = pos.side * (close - pos.entry) * pos.remaining
        equity_curve.append(equity + unreal)

    metrics = reporting.compute_metrics(pnls, equity_curve, periods_per_year)
    return BacktestResult(pnls, equity_curve, trades, metrics, bars=len(data))


# --- ottimizzazione e validazione ---------------------------------------------


def _grid(param_grid: dict) -> list[dict]:
    keys = list(param_grid)
    return [dict(zip(keys, combo)) for combo in itertools.product(*param_grid.values())]


def optimize(
    df: pd.DataFrame,
    strategy_name: str,
    param_grid: dict,
    risk: RiskParams | None = None,
    costs: CostModel | None = None,
    min_trades: int = 20,
) -> tuple[dict, reporting.Metrics]:
    """Grid search: restituisce (parametri_migliori, metriche) per profit factor.

    Scarta combinazioni con troppo pochi trade: poche operazioni = campione
    inaffidabile, non un edge (vedi docs/reference/metriche.md).
    """
    best_params, best_metrics, best_pf = None, None, -1.0
    for params in _grid(param_grid):
        strat = make_strategy(strategy_name, **params)
        res = run_backtest(df, strat, risk, costs)
        if res.metrics.n_trades < min_trades:
            continue
        pf = res.metrics.profit_factor
        if pf > best_pf:
            best_params, best_metrics, best_pf = params, res.metrics, pf
    if best_params is None:
        # nessuna combinazione con abbastanza trade: ritorna la prima così com'è
        first = _grid(param_grid)[0]
        return first, run_backtest(df, make_strategy(strategy_name, **first), risk, costs).metrics
    return best_params, best_metrics


@dataclass
class WalkForwardWindow:
    train_metrics: reporting.Metrics
    test_metrics: reporting.Metrics
    best_params: dict


@dataclass
class WalkForwardResult:
    windows: list[WalkForwardWindow]
    is_profit_factor: float  # media in-sample
    oos_profit_factor: float  # media out-of-sample
    overfitting: bool

    def as_dict(self) -> dict:
        return {
            "n_windows": len(self.windows),
            "is_profit_factor": self.is_profit_factor,
            "oos_profit_factor": self.oos_profit_factor,
            "overfitting": self.overfitting,
            "windows": [
                {
                    "best_params": w.best_params,
                    "train": w.train_metrics.as_dict(),
                    "test": w.test_metrics.as_dict(),
                }
                for w in self.windows
            ],
        }


def walk_forward(
    df: pd.DataFrame,
    strategy_name: str,
    param_grid: dict,
    n_windows: int = 4,
    train_frac: float = 0.7,
    risk: RiskParams | None = None,
    costs: CostModel | None = None,
    min_trades: int = 10,
) -> WalkForwardResult:
    """Walk-forward rolling: ottimizza su train, valida su test (mai visto).

    Divide i dati in `n_windows` finestre; in ognuna ottimizza sui primi
    `train_frac` e applica i parametri sul resto. L'edge regge solo se l'OOS
    medio resta sopra 1. Se IS è buono ma OOS crolla: overfitting -> scarta.
    """
    n = len(df)
    win_size = n // n_windows
    windows: list[WalkForwardWindow] = []

    for w in range(n_windows):
        start = w * win_size
        end = n if w == n_windows - 1 else (w + 1) * win_size
        block = df.iloc[start:end].reset_index(drop=True)
        if len(block) < 50:
            continue
        split = int(len(block) * train_frac)
        train, test = block.iloc[:split], block.iloc[split:].reset_index(drop=True)

        best_params, train_metrics = optimize(
            train, strategy_name, param_grid, risk, costs, min_trades
        )
        test_res = run_backtest(test, make_strategy(strategy_name, **best_params), risk, costs)
        windows.append(WalkForwardWindow(train_metrics, test_res.metrics, best_params))

    def _avg_pf(values: list[float]) -> float:
        finite = [v for v in values if v != float("inf")]
        return sum(finite) / len(finite) if finite else 0.0

    is_pf = _avg_pf([w.train_metrics.profit_factor for w in windows])
    oos_pf = _avg_pf([w.test_metrics.profit_factor for w in windows])
    overfitting = is_pf > 1.0 and oos_pf <= 1.0
    return WalkForwardResult(windows, is_pf, oos_pf, overfitting)
