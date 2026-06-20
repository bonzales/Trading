"""Strategie e factory.

Una strategia fa UNA cosa: data la storia dei prezzi fino alla barra `i`, decide
se entrare (long/short) o stare ferma. Non gestisce rischio né esecuzione: quelli
stanno in risk_manager.py e negli adapter.

Default: `pullback` — l'unica che su Kraken non perdeva. Da ri-validare su OANDA da
zero (vedi research/strategies/pullback.md): un comportamento su crypto non si
trasferisce automaticamente al forex.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd

from src.core import indicators as ind

LONG, SHORT, FLAT = 1, -1, 0


@dataclass
class Signal:
    """Decisione di ingresso su una barra."""

    side: int  # LONG | SHORT | FLAT
    price: float  # prezzo di riferimento (close della barra)
    atr: float  # volatilità corrente, per dimensionare lo stop


class Strategy(Protocol):
    name: str

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge le colonne indicatore. Ritorna un nuovo DataFrame."""

    def signal(self, df: pd.DataFrame, i: int) -> Signal:
        """Decisione sulla barra `i` (df già passato per prepare)."""

    @property
    def warmup(self) -> int:
        """Barre iniziali da saltare (indicatori non ancora validi)."""


@dataclass
class PullbackStrategy:
    """Entra nel trend durante un ritracciamento, con conferma di momentum.

    Long quando: trend su (ema_fast > ema_slow), RSI dentro la banda di pullback,
    MACD conferma (state: macd>signal; cross: incrocio rialzista sulla barra).
    Servono almeno `min_conditions` condizioni vere. Short speculare.
    """

    name: str = "pullback"
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    rsi_low: float = 40.0
    rsi_high: float = 60.0
    macd_mode: str = "state"  # "state" | "cross"
    atr_period: int = 14
    min_conditions: int = 3

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ind.ema(out["close"], self.ema_fast)
        out["ema_slow"] = ind.ema(out["close"], self.ema_slow)
        out["rsi"] = ind.rsi(out["close"], self.rsi_period)
        macd = ind.macd(out["close"])
        out["macd"] = macd["macd"]
        out["macd_signal"] = macd["signal"]
        out["atr"] = ind.atr(out, self.atr_period)
        return out

    @property
    def warmup(self) -> int:
        return max(self.ema_slow, self.rsi_period, self.atr_period, 35) + 1

    def signal(self, df: pd.DataFrame, i: int) -> Signal:
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        price, atr = float(row["close"]), float(row["atr"])

        if pd.isna(atr) or pd.isna(row["ema_slow"]) or pd.isna(row["rsi"]):
            return Signal(FLAT, price, 0.0)

        trend_up = row["ema_fast"] > row["ema_slow"]
        rsi_in_band = self.rsi_low <= row["rsi"] <= self.rsi_high

        if self.macd_mode == "cross":
            macd_up = prev["macd"] <= prev["macd_signal"] and row["macd"] > row["macd_signal"]
            macd_dn = prev["macd"] >= prev["macd_signal"] and row["macd"] < row["macd_signal"]
        else:  # state
            macd_up = row["macd"] > row["macd_signal"]
            macd_dn = row["macd"] < row["macd_signal"]

        long_conditions = sum([trend_up, rsi_in_band, macd_up])
        short_conditions = sum([not trend_up, rsi_in_band, macd_dn])

        if trend_up and long_conditions >= self.min_conditions:
            return Signal(LONG, price, atr)
        if (not trend_up) and short_conditions >= self.min_conditions:
            return Signal(SHORT, price, atr)
        return Signal(FLAT, price, atr)


def make_strategy(name: str, **params) -> Strategy:
    """Factory: traduce nome + parametri in un'istanza di strategia."""
    registry = {"pullback": PullbackStrategy}
    if name not in registry:
        raise ValueError(
            f"Strategia '{name}' non disponibile. Disponibili: {', '.join(registry)}."
        )
    return registry[name](**params)
