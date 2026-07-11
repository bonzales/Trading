"""Backtest mean-reversion "compra il ribasso" sugli indici (stile Connors RSI-2).

Ipotesi: gli indici azionari hanno drift rialzista + rientri di breve. Comprare
quando il prezzo è ipervenduto MA sopra il trend di fondo, uscire quando rimbalza.
È l'edge complementare al trend-following, e proprio quello che ha funzionato nel
regime 2011-2026 (dove il TF è stato piatto).

Regole (canoniche, poche → poco overfitting):
  - filtro trend: close > SMA(ma_long)  (compriamo solo in uptrend di fondo)
  - ingresso long: RSI(rsi_period) < oversold
  - uscita: RSI > exit_rsi  OPPURE close > SMA(ma_short)  OPPURE max_hold barre
  - stop di protezione: atr_stop × ATR sotto l'ingresso
Long-only: sugli indici lo short mean-reversion è un'altra bestia (drift contro).

Uscite gestite qui (l'engine continuo fa trailing ATR, non adatto al MR).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.core import indicators as ind


@dataclass
class MeanRevConfig:
    ma_long: int = 200
    rsi_period: int = 2
    oversold: float = 10.0
    exit_rsi: float = 50.0
    ma_short: int = 5
    max_hold: int = 10
    atr_period: int = 14
    atr_stop: float = 3.0
    risk_pct: float = 0.02
    spread_pts: float = 1.0
    start_equity: float = 10_000.0


@dataclass
class MRTrade:
    entry: float
    exit: float
    r_multiple: float
    ret_pct: float
    bars: int
    reason: str
    exit_i: int = -1


def backtest(df: pd.DataFrame, cfg: MeanRevConfig | None = None) -> dict:
    cfg = cfg or MeanRevConfig()
    d = df.copy()
    close = d["close"].to_numpy(dtype=float)
    high = d["high"].to_numpy(dtype=float)
    low = d["low"].to_numpy(dtype=float)
    ma_long = d["close"].rolling(cfg.ma_long).mean().to_numpy()
    ma_short = d["close"].rolling(cfg.ma_short).mean().to_numpy()
    rsi = ind.rsi(d["close"], cfg.rsi_period).to_numpy()
    atr = ind.atr(d, cfg.atr_period).to_numpy()
    n = len(d)
    warmup = cfg.ma_long + 1
    half = cfg.spread_pts / 2.0

    trades: list[MRTrade] = []
    i = warmup
    while i < n:
        if (not np.isnan(ma_long[i]) and not np.isnan(rsi[i]) and not np.isnan(atr[i])
                and close[i] > ma_long[i] and rsi[i] < cfg.oversold and atr[i] > 0):
            entry = close[i] + half
            stop = entry - cfg.atr_stop * atr[i]
            r_pts = entry - stop
            exit_price = None
            reason = "end"
            j = i + 1
            while j < n:
                if low[j] <= stop:
                    exit_price, reason = stop - half, "stop"
                    break
                if rsi[j] > cfg.exit_rsi or close[j] > ma_short[j] or (j - i) >= cfg.max_hold:
                    exit_price = close[j] - half
                    reason = "rsi" if rsi[j] > cfg.exit_rsi else ("ma" if close[j] > ma_short[j] else "time")
                    break
                j += 1
            if exit_price is None:
                exit_price, j, reason = close[n - 1] - half, n - 1, "end"
            pnl_pts = exit_price - entry
            trades.append(MRTrade(entry, exit_price, pnl_pts / r_pts if r_pts > 0 else 0.0,
                                  pnl_pts / entry, j - i, reason, exit_i=j))
            i = j + 1
        else:
            i += 1
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
    return {
        "trades": trades,
        "metrics": {
            "n_trades": len(trades),
            "win_rate": float((r > 0).mean()) if len(r) else 0.0,
            "profit_factor": float(gw / gl) if gl > 0 else float("inf"),
            "expectancy_R": float(r.mean()) if len(r) else 0.0,
            "total_return": float(curve[-1] / curve[0] - 1),
            "cagr": float(cagr),
            "max_drawdown": float(dd.min()) if len(dd) else 0.0,
            "avg_bars": float(np.mean([t.bars for t in trades])) if trades else 0.0,
        },
    }
