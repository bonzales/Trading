"""Logica di decisione GIORNALIERA della strategia mean-reversion (rsi2_meanrev).

Pura e testabile: date le candele daily + lo stato attuale della posizione, decide
cosa fare oggi (BUY / CLOSE / HOLD). Nessuna rete, nessun broker qui — l'esecuzione
sta in adapters/ibkr/execution.py, l'orchestrazione in live/paper_bot.py.

Regole (identiche al backtest edge-confirmed, vedi research/strategies/rsi2_meanrev.md):
  - filtro trend: close > SMA(ma_long)
  - ingresso long: RSI(rsi_period) < oversold
  - uscita: RSI > exit_rsi  OPPURE  close > SMA(ma_short)  OPPURE  giorni_tenuti >= max_hold
  - lo STOP di protezione (atr_stop × ATR) è un ordine a riposo presso il broker,
    non una decisione giornaliera: qui ne calcoliamo solo il prezzo all'ingresso.
Long-only (l'edge vive sugli indici al rialzo).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.core import indicators as ind


@dataclass(frozen=True)
class MRParams:
    ma_long: int = 200
    rsi_period: int = 2
    oversold: float = 10.0
    exit_rsi: float = 50.0
    ma_short: int = 5
    max_hold: int = 10
    atr_period: int = 14
    atr_stop: float = 3.0
    risk_pct: float = 0.01


@dataclass(frozen=True)
class Plan:
    action: str          # "BUY" | "CLOSE" | "HOLD"
    reason: str
    close: float
    atr: float
    stop_price: float | None = None   # valorizzato solo su BUY


def _last_indicators(bars: pd.DataFrame, p: MRParams) -> dict:
    close = bars["close"]
    return {
        "close": float(close.iloc[-1]),
        "sma_long": float(close.rolling(p.ma_long).mean().iloc[-1]),
        "sma_short": float(close.rolling(p.ma_short).mean().iloc[-1]),
        "rsi": float(ind.rsi(close, p.rsi_period).iloc[-1]),
        "atr": float(ind.atr(bars, p.atr_period).iloc[-1]),
    }


def decide(bars: pd.DataFrame, has_position: bool, bars_held: int | None,
           p: MRParams | None = None) -> Plan:
    """Decisione per l'ULTIMA candela daily disponibile (già chiusa).

    `bars`: DataFrame daily con colonne open/high/low/close (ordinato nel tempo).
    `has_position`: siamo già long su questo strumento?
    `bars_held`: da quanti giorni (per il max_hold); None se flat.
    """
    p = p or MRParams()
    if len(bars) < p.ma_long + 1:
        return Plan("HOLD", "storia insufficiente", float("nan"), float("nan"))
    v = _last_indicators(bars, p)
    if any(pd.isna(v[k]) for k in ("sma_long", "rsi", "atr")):
        return Plan("HOLD", "indicatori non pronti", v["close"], v.get("atr", float("nan")))

    if not has_position:
        if v["close"] > v["sma_long"] and v["rsi"] < p.oversold and v["atr"] > 0:
            stop = v["close"] - p.atr_stop * v["atr"]
            return Plan("BUY", f"RSI{p.rsi_period} {v['rsi']:.1f}<{p.oversold} sopra SMA{p.ma_long}",
                        v["close"], v["atr"], stop_price=stop)
        return Plan("HOLD", "nessun setup d'ingresso", v["close"], v["atr"])

    # in posizione: valutiamo l'uscita
    if v["rsi"] > p.exit_rsi:
        return Plan("CLOSE", f"RSI risalito >{p.exit_rsi}", v["close"], v["atr"])
    if v["close"] > v["sma_short"]:
        return Plan("CLOSE", f"close>SMA{p.ma_short} (rimbalzo)", v["close"], v["atr"])
    if bars_held is not None and bars_held >= p.max_hold:
        return Plan("CLOSE", f"max_hold {p.max_hold} giorni", v["close"], v["atr"])
    return Plan("HOLD", "posizione in corso", v["close"], v["atr"])


def position_size(equity: float, close: float, stop_price: float,
                  point_value: float, p: MRParams) -> int:
    """Numero di contratti/unità perché la perdita allo stop ≈ risk_pct × equity.

    point_value = valore di 1 punto indice per contratto (dipende dal CFD del broker).
    Ritorna 0 se il calcolo non è valido (evita ordini insensati).
    """
    dist = abs(close - stop_price)
    if dist <= 0 or point_value <= 0 or equity <= 0:
        return 0
    risk_amount = p.risk_pct * equity
    qty = risk_amount / (dist * point_value)
    return max(int(qty), 0)
