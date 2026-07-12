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
    mode: str = "breakout"       # "breakout" (rottura) | "bounce" (rimbalzo)
    vol_window: int = 100        # finestra per la mediana di volume
    vol_mult: float = 3.0        # soglia: volume ≥ vol_mult × mediana → livello
    level_life: int = 120        # barre di vita di un livello (memoria multi-day)
    break_atr: float = 0.1       # tolleranza/rottura in multipli di ATR
    atr_period: int = 14

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["atr"] = ind.atr(out, self.atr_period)
        vol_med = out["volume"].rolling(self.vol_window, min_periods=self.vol_window // 2).median()
        high_vol = (out["volume"] >= self.vol_mult * vol_med).to_numpy()
        close = out["close"].to_numpy()
        high = out["high"].to_numpy()
        low = out["low"].to_numpy()
        atr = out["atr"].to_numpy()
        n = len(out)
        long_sig = [False] * n
        short_sig = [False] * n
        bounce = self.mode == "bounce"
        levels: list[tuple[float, int]] = []  # (prezzo, indice di scadenza)
        for i in range(n):
            if levels:
                levels = [(p, e) for (p, e) in levels if e >= i]
            if i > 0 and not pd.isna(atr[i]) and atr[i] > 0:
                buf = self.break_atr * atr[i]
                pc, c, hi, lo = close[i - 1], close[i], high[i], low[i]
                for p, _ in levels:
                    if bounce:
                        # rimbalzo: prezzo TORNA sul livello e lo RISPETTA (market-neutral)
                        if pc > p and lo <= p + buf and c >= p:      # supporto tiene → long
                            long_sig[i] = True
                        elif pc < p and hi >= p - buf and c <= p:    # resistenza tiene → short
                            short_sig[i] = True
                    else:
                        # rottura: prezzo ATTRAVERSA il livello con forza
                        if pc < p + buf <= c:
                            long_sig[i] = True
                        elif pc > p - buf >= c:
                            short_sig[i] = True
            if high_vol[i]:
                levels.append((close[i], i + self.level_life))
        out["long_break"] = long_sig
        out["short_break"] = short_sig
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


@dataclass
class DonchianStrategy:
    """Trend-following classico (stile Turtle): rottura del canale di Donchian.

    Long quando il prezzo chiude sopra il massimo degli ultimi `channel` giorni,
    short sotto il minimo. Niente target: stop/trailing ATR (dal risk_manager) fanno
    correre i trend. È lo stile con più evidenza storica di un edge reale e modesto,
    soprattutto DIVERSIFICATO su molti mercati (indici, forex, materie prime).
    """

    name: str = "donchian"
    channel: int = 20
    atr_period: int = 14

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        dc = ind.donchian(out, self.channel)
        out["dc_upper"] = dc["dc_upper"]
        out["dc_lower"] = dc["dc_lower"]
        out["atr"] = ind.atr(out, self.atr_period)
        return out

    @property
    def warmup(self) -> int:
        return max(self.channel, self.atr_period) + 1

    def signal(self, df: pd.DataFrame, i: int) -> Signal:
        row = df.iloc[i]
        price, atr = float(row["close"]), float(row["atr"])
        if pd.isna(atr) or atr <= 0 or pd.isna(row["dc_upper"]):
            return Signal(FLAT, price, 0.0)
        if price > row["dc_upper"]:
            return Signal(LONG, price, atr)
        if price < row["dc_lower"]:
            return Signal(SHORT, price, atr)
        return Signal(FLAT, price, atr)


@dataclass
class DonchianLongStrategy(DonchianStrategy):
    """Donchian trend-following SOLO LONG.

    Sugli asset con drift rialzista di fondo (indici, ORO) gli short remano contro
    la deriva e peggiorano l'edge: sull'oro il solo-long batte nettamente il long/short
    (PF ~2 vs ~1,3, maxDD -8%, OOS che migliora). Stessa lezione del mean-reversion sugli
    indici ([[rsi2_meanrev]]). Vedi research/strategies/gold_trend.md.
    """

    name: str = "donchian_long"

    def signal(self, df: pd.DataFrame, i: int) -> Signal:
        sig = super().signal(df, i)
        return sig if sig.side == LONG else Signal(FLAT, sig.price, sig.atr)


@dataclass
class IchimokuStrategy:
    """Ichimoku Kinko Hyo — regole canoniche (trend-following).

    Linee: Tenkan (9), Kijun (26), Senkou A = (Tenkan+Kijun)/2 proiettata +26,
    Senkou B (52) proiettata +26, Chikou = close spostata −26. Ingresso "a tre
    conferme": prezzo dal lato giusto della nuvola (Kumo) + incrocio Tenkan/Kijun
    + conferma Chikou (close vs close di 26 barre fa). Uscita: stop/trailing ATR
    dell'engine. Nessun lookahead: tutte le linee usano dati ≤ i.
    """

    name: str = "ichimoku"
    tenkan: int = 9
    kijun: int = 26
    senkou_b: int = 52
    shift: int = 26
    atr_period: int = 14

    @staticmethod
    def _mid(df: pd.DataFrame, n: int) -> pd.Series:
        return (df["high"].rolling(n).max() + df["low"].rolling(n).min()) / 2.0

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        tk = self._mid(out, self.tenkan)
        kj = self._mid(out, self.kijun)
        out["tenkan"] = tk
        out["kijun"] = kj
        # nuvola: medie proiettate 26 avanti → al bar i usano dati di i-26 (no lookahead)
        out["ssa"] = ((tk + kj) / 2.0).shift(self.shift)
        out["ssb"] = self._mid(out, self.senkou_b).shift(self.shift)
        out["cloud_top"] = out[["ssa", "ssb"]].max(axis=1)
        out["cloud_bot"] = out[["ssa", "ssb"]].min(axis=1)
        out["close_lag"] = out["close"].shift(self.shift)  # per la conferma Chikou
        out["atr"] = ind.atr(out, self.atr_period)
        return out

    @property
    def warmup(self) -> int:
        return self.senkou_b + self.shift + self.atr_period + 1

    def signal(self, df: pd.DataFrame, i: int) -> Signal:
        row = df.iloc[i]
        price, atr = float(row["close"]), float(row["atr"])
        if pd.isna(atr) or atr <= 0 or pd.isna(row["cloud_top"]) or pd.isna(row["close_lag"]):
            return Signal(FLAT, price, 0.0)
        long_ok = (price > row["cloud_top"] and row["tenkan"] > row["kijun"]
                   and price > row["close_lag"])
        short_ok = (price < row["cloud_bot"] and row["tenkan"] < row["kijun"]
                    and price < row["close_lag"])
        if long_ok:
            return Signal(LONG, price, atr)
        if short_ok:
            return Signal(SHORT, price, atr)
        return Signal(FLAT, price, atr)


def make_strategy(name: str, **params) -> Strategy:
    """Factory: traduce nome + parametri in un'istanza di strategia."""
    registry = {
        "pullback": PullbackStrategy,
        "vol_levels": VolumeLevelStrategy,
        "donchian": DonchianStrategy,
        "donchian_long": DonchianLongStrategy,
        "ichimoku": IchimokuStrategy,
    }
    if name not in registry:
        raise ValueError(
            f"Strategia '{name}' non disponibile. Disponibili: {', '.join(registry)}."
        )
    return registry[name](**params)
