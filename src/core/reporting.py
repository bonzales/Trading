"""Metriche di performance condivise (vedi docs/reference/metriche.md).

Funzioni pure su liste di trade ed equity curve. Un win rate alto non basta: il
segnale che conta per promuovere è l'esito out-of-sample (lo calcola il
walk-forward), ma queste metriche descrivono il singolo run.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass
class Metrics:
    n_trades: int
    win_rate: float
    profit_factor: float
    sharpe: float
    max_drawdown: float
    total_return: float
    final_equity: float

    def as_dict(self) -> dict:
        return asdict(self)


def profit_factor(pnls: list[float]) -> float:
    """Profitti lordi / perdite lorde. inf se non ci sono perdite."""
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = -sum(p for p in pnls if p < 0)
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def win_rate(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    return sum(1 for p in pnls if p > 0) / len(pnls)


def max_drawdown(equity_curve: list[float]) -> float:
    """Peggiore caduta picco-valle, come frazione (0.2 = -20%)."""
    peak = -math.inf
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def sharpe(equity_curve: list[float], periods_per_year: float = 252 * 24) -> float:
    """Sharpe annualizzato dai rendimenti periodici dell'equity (rf=0).

    `periods_per_year` di default ~ ore di trading l'anno (H1). Adattalo al tf.
    """
    if len(equity_curve) < 3:
        return 0.0
    returns = [
        equity_curve[i] / equity_curve[i - 1] - 1.0
        for i in range(1, len(equity_curve))
        if equity_curve[i - 1] > 0
    ]
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(periods_per_year)


def compute_metrics(
    pnls: list[float], equity_curve: list[float], periods_per_year: float = 252 * 24
) -> Metrics:
    initial = equity_curve[0] if equity_curve else 0.0
    final = equity_curve[-1] if equity_curve else 0.0
    return Metrics(
        n_trades=len(pnls),
        win_rate=win_rate(pnls),
        profit_factor=profit_factor(pnls),
        sharpe=sharpe(equity_curve, periods_per_year),
        max_drawdown=max_drawdown(equity_curve),
        total_return=(final / initial - 1.0) if initial > 0 else 0.0,
        final_equity=final,
    )
