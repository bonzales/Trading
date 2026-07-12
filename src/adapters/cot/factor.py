"""Fattori derivati dal COT: posizione netta e "COT index" normalizzato.

- net commerciali / speculatori = long − short (in % dell'open interest, così è
  confrontabile tra strumenti e nel tempo).
- COT index = dove sta la posizione netta OGGI rispetto al suo range degli ultimi
  `window` periodi, scalato 0-100. 100 = massimo storico di net-long, 0 = massimo net-short.
  È il modo classico di leggere gli estremi di posizionamento (segnale contrarian sui
  commercial, o di estremo speculativo).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_factors(cot: pd.DataFrame, window: int = 156) -> pd.DataFrame:
    """Aggiunge le colonne dei fattori a un DataFrame COT (da parse_cot).

    window=156 settimane ≈ 3 anni (finestra classica per il COT index).
    """
    df = cot.copy()
    oi = df["oi"].replace(0, np.nan)
    df["net_comm"] = (df["c_long"] - df["c_short"]) / oi          # frazione dell'OI
    df["net_spec"] = (df["nc_long"] - df["nc_short"]) / oi
    df["cot_index_comm"] = _rolling_index(df["net_comm"], window)
    df["cot_index_spec"] = _rolling_index(df["net_spec"], window)
    return df


def _rolling_index(x: pd.Series, window: int) -> pd.Series:
    """Scala x nel range [min,max] della finestra mobile → 0..100 (NaN finché la
    finestra non è piena)."""
    lo = x.rolling(window, min_periods=window).min()
    hi = x.rolling(window, min_periods=window).max()
    rng = (hi - lo).replace(0, np.nan)
    return ((x - lo) / rng * 100.0).clip(0, 100)


def align_to_daily(cot_factors: pd.DataFrame, daily_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Porta i fattori COT (settimanali) su un indice giornaliero con forward-fill.

    Il COT esce il venerdì per il martedì: usiamo l'ultimo dato NOTO a ogni data
    (forward-fill), niente look-ahead.
    """
    f = cot_factors.set_index("date").sort_index()
    cols = ["net_comm", "net_spec", "cot_index_comm", "cot_index_spec"]
    return f[cols].reindex(f.index.union(daily_index)).ffill().reindex(daily_index)
