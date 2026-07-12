"""Backtest mean-reversion SIMMETRICO sui forex major (RSI-2, long e short).

A differenza degli indici (drift rialzista → solo long, con filtro trend), le valute
non hanno drift direzionale: oscillano e rientrano verso la media. Quindi qui il
mean-reversion è SIMMETRICO e SENZA filtro di trend:

Regole (canoniche, poche → poco overfitting):
  - ingresso LONG:  RSI(rsi_period) < oversold        (~10)
  - ingresso SHORT: RSI(rsi_period) > (100 − oversold) (~90)
  - uscita LONG:  RSI > exit_rsi  OPPURE max_hold barre  OPPURE stop
  - uscita SHORT: RSI < exit_rsi  OPPURE max_hold barre  OPPURE stop
  - stop di protezione: atr_stop × ATR oltre l'ingresso (sotto per i long, sopra per gli short)

Questa è la validazione TRADE-LEVEL (stop, sizing sul rischio, costi spread) del segnale
che era stato confermato solo a livello di serie di rendimenti (posizione ±1). È il gate
mancante prima del paper, gemello di src/backtest/meanrev.py (che è long-only indici).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.core import indicators as ind


@dataclass
class FxMeanRevConfig:
    rsi_period: int = 2
    oversold: float = 10.0        # overbought = 100 − oversold
    exit_rsi: float = 50.0
    max_hold: int = 10
    atr_period: int = 14
    atr_stop: float = 3.0
    risk_pct: float = 0.01        # rischio per trade sul capitale
    spread: float = 0.00008       # spread in unità di PREZZO (non punti): EUR/USD ~0,8 pip
    start_equity: float = 10_000.0


@dataclass
class FxTrade:
    side: int          # +1 long, −1 short
    entry: float
    exit: float
    r_multiple: float  # P&L in multipli del rischio iniziale (1R = distanza stop)
    ret_pct: float
    bars: int
    reason: str
    entry_i: int = -1
    exit_i: int = -1


def backtest(df: pd.DataFrame, cfg: FxMeanRevConfig | None = None) -> dict:
    cfg = cfg or FxMeanRevConfig()
    d = df.copy()
    close = d["close"].to_numpy(dtype=float)
    high = d["high"].to_numpy(dtype=float)
    low = d["low"].to_numpy(dtype=float)
    rsi = ind.rsi(d["close"], cfg.rsi_period).to_numpy()
    atr = ind.atr(d, cfg.atr_period).to_numpy()
    n = len(d)
    warmup = cfg.atr_period + 1
    half = cfg.spread / 2.0
    overbought = 100.0 - cfg.oversold

    trades: list[FxTrade] = []
    i = warmup
    while i < n:
        valid = not np.isnan(rsi[i]) and not np.isnan(atr[i]) and atr[i] > 0
        side = 0
        if valid:
            if rsi[i] < cfg.oversold:
                side = 1
            elif rsi[i] > overbought:
                side = -1
        if side == 0:
            i += 1
            continue

        # entra pagando metà spread nella direzione sfavorevole
        entry = close[i] + side * half
        stop = entry - side * cfg.atr_stop * atr[i]
        r_pts = abs(entry - stop)
        exit_price = None
        reason = "end"
        j = i + 1
        while j < n:
            # stop intrabar (conservativo: se toccato, esce allo stop)
            if side == 1 and low[j] <= stop:
                exit_price, reason = stop - half, "stop"
                break
            if side == -1 and high[j] >= stop:
                exit_price, reason = stop + half, "stop"
                break
            # uscita mean-reversion: RSI rientra oltre exit_rsi, o tempo massimo
            rsi_exit = (side == 1 and rsi[j] > cfg.exit_rsi) or (side == -1 and rsi[j] < cfg.exit_rsi)
            if rsi_exit or (j - i) >= cfg.max_hold:
                exit_price = close[j] - side * half
                reason = "rsi" if rsi_exit else "time"
                break
            j += 1
        if exit_price is None:
            exit_price, j, reason = close[n - 1] - side * half, n - 1, "end"

        pnl_pts = side * (exit_price - entry)
        trades.append(FxTrade(side, entry, exit_price,
                              pnl_pts / r_pts if r_pts > 0 else 0.0,
                              pnl_pts / entry, j - i, reason, entry_i=i, exit_i=j))
        i = j + 1
    return _summarize(trades, cfg, d)


def _summarize(trades, cfg, d) -> dict:
    equity = cfg.start_equity
    curve = [equity]
    for t in trades:
        equity += t.r_multiple * cfg.risk_pct * equity
        curve.append(equity)
    curve = np.array(curve)
    r = np.array([t.r_multiple for t in trades]) if trades else np.array([])
    gw = r[r > 0].sum()
    gl = -r[r < 0].sum()
    peak = np.maximum.accumulate(curve)
    dd = (curve - peak) / peak
    years = max((pd.to_datetime(d["time"].iloc[-1]) - pd.to_datetime(d["time"].iloc[0])).days / 365.25, 0.1)
    cagr = curve[-1] ** (1 / years) * (cfg.start_equity ** (-1 / years)) - 1 if curve[-1] > 0 else -1
    longs = [t for t in trades if t.side == 1]
    shorts = [t for t in trades if t.side == -1]
    return {
        "trades": trades,
        "metrics": {
            "n_trades": len(trades),
            "n_long": len(longs),
            "n_short": len(shorts),
            "win_rate": float((r > 0).mean()) if len(r) else 0.0,
            "profit_factor": float(gw / gl) if gl > 0 else float("inf"),
            "expectancy_R": float(r.mean()) if len(r) else 0.0,
            "total_return": float(curve[-1] / curve[0] - 1),
            "cagr": float(cagr),
            "max_drawdown": float(dd.min()) if len(dd) else 0.0,
            "avg_bars": float(np.mean([t.bars for t in trades])) if trades else 0.0,
        },
    }
