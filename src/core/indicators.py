"""Indicatori tecnici nativi (pandas/numpy), senza dipendenze esterne.

Funzioni pure: prendono una Series/DataFrame e restituiscono Series allineate
all'indice di input. Nessuno stato, nessuna rete: facili da testare e da comporre.
Il cervello (strategie) è broker-agnostico — vive qui, lontano dagli adapter.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Media mobile esponenziale."""
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder), 0–100."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100 - (100 / (1 + rs))
    # se avg_loss == 0 -> RSI 100 (nessuna perdita nel periodo)
    out = out.where(avg_loss != 0, 100.0)
    return out


def macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """MACD: ritorna colonne macd, signal, hist."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "hist": macd_line - signal_line}
    )


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (Wilder). Richiede colonne high, low, close."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Canale di Donchian: massimo/minimo degli ultimi `period` (escluso bar corrente)."""
    upper = df["high"].rolling(period).max().shift(1)
    lower = df["low"].rolling(period).min().shift(1)
    return pd.DataFrame({"dc_upper": upper, "dc_lower": lower})
