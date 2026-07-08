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


@dataclass
class VolumeLevelStrategy:
    """Rottura di livelli lasciati da candele ad alto volume (swing, H1/H4).

    Idea dell'utente portata su timeframe alto, dove i costi pesano poco: una barra
    con volume anomalo lascia un livello S/R che il prezzo "ricorda" per giorni. Si
    entra sulla ROTTURA del livello (long se lo supera al rialzo, short al ribasso),
    con conferma di `break_atr` × ATR. Stop/target/trailing li mette il risk_manager.
    """

    name: str = "vol_levels"
    vol_window: int = 100        # finestra per la mediana di volume
    vol_mult: float = 3.0        # soglia: volume ≥ vol_mult × mediana → livello
    level_life: int = 120        # barre di vita di un livello (memoria multi-day)
    break_atr: float = 0.1       # rottura netta: oltre il livello di break_atr×ATR
    atr_period: int = 14

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["atr"] = ind.atr(out, self.atr_period)
        vol_med = out["volume"].rolling(self.vol_window, min_periods=self.vol_window // 2).median()
        high_vol = (out["volume"] >= self.vol_mult * vol_med).to_numpy()
        close = out["close"].to_numpy()
        atr = out["atr"].to_numpy()
        n = len(out)
        long_break = [False] * n
        short_break = [False] * n
        levels: list[tuple[float, int]] = []  # (prezzo, indice di scadenza)
        for i in range(n):
            if levels:
                levels = [(p, e) for (p, e) in levels if e >= i]
            if i > 0 and not pd.isna(atr[i]) and atr[i] > 0:
                buf = self.break_atr * atr[i]
                pc, c = close[i - 1], close[i]
                for p, _ in levels:
                    if pc < p + buf <= c:
                        long_break[i] = True
                    elif pc > p - buf >= c:
                        short_break[i] = True
            if high_vol[i]:
                levels.append((close[i], i + self.level_life))
        out["long_break"] = long_break
        out["short_break"] = short_break
        return out

    @property
    def warmup(self) -> int:
        return self.vol_window + self.atr_period + 1

    def signal(self, df: pd.DataFrame, i: int) -> Signal:
        row = df.iloc[i]
        price, atr = float(row["close"]), float(row["atr"])
        if pd.isna(atr) or atr <= 0:
            return Signal(FLAT, price, 0.0)
        if row["long_break"]:
            return Signal(LONG, price, atr)
        if row["short_break"]:
            return Signal(SHORT, price, atr)
        return Signal(FLAT, price, atr)


def make_strategy(name: str, **params) -> Strategy:
    """Factory: traduce nome + parametri in un'istanza di strategia."""
    registry = {"pullback": PullbackStrategy, "vol_levels": VolumeLevelStrategy}
    if name not in registry:
        raise ValueError(
            f"Strategia '{name}' non disponibile. Disponibili: {', '.join(registry)}."
        )
    return registry[name](**params)
