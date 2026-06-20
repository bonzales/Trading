"""Test degli indicatori: valori noti e proprietà di base. Nessuna rete."""
import numpy as np
import pandas as pd

from src.core import indicators as ind


def test_ema_segue_la_serie():
    s = pd.Series([1.0] * 50)
    assert ind.ema(s, 10).iloc[-1] == 1.0  # serie costante -> EMA costante


def test_rsi_estremi():
    up = pd.Series(np.arange(1, 60, dtype=float))  # sempre in salita
    rsi_up = ind.rsi(up, 14).iloc[-1]
    assert rsi_up > 95  # nessuna perdita -> RSI vicino a 100

    down = pd.Series(np.arange(60, 1, -1, dtype=float))
    rsi_down = ind.rsi(down, 14).iloc[-1]
    assert rsi_down < 5


def test_atr_positivo():
    n = 60
    df = pd.DataFrame({
        "high": np.linspace(10, 20, n) + 0.5,
        "low": np.linspace(10, 20, n) - 0.5,
        "close": np.linspace(10, 20, n),
    })
    atr = ind.atr(df, 14)
    assert atr.iloc[-1] > 0
    assert atr.notna().iloc[-1]


def test_macd_colonne():
    s = pd.Series(np.sin(np.linspace(0, 10, 100)) + 10)
    macd = ind.macd(s)
    assert set(macd.columns) == {"macd", "signal", "hist"}
    assert len(macd) == len(s)
