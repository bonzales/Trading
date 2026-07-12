"""Test del resampler OHLCV. Dati sintetici, niente rete."""
import numpy as np
import pandas as pd
import pytest

from src.adapters.resample import resample_ohlcv, supported_timeframes


def _m1(n=240, seed=0) -> pd.DataFrame:
    """4 ore di barre M1 con OHLC coerenti."""
    rng = np.random.default_rng(seed)
    t = pd.date_range("2024-01-01 00:00", periods=n, freq="1min", tz="UTC")
    close = 100 + np.cumsum(rng.normal(0, 0.05, n))
    high = close + rng.uniform(0.01, 0.1, n)
    low = close - rng.uniform(0.01, 0.1, n)
    openp = np.concatenate([[close[0]], close[:-1]])
    vol = rng.uniform(1, 10, n)
    return pd.DataFrame({"time": t, "open": openp, "high": high, "low": low, "close": close, "volume": vol})


def test_h1_aggrega_60_barre():
    df = _m1(240)
    h1 = resample_ohlcv(df, "H1")
    assert len(h1) == 4  # 240 minuti / 60
    # la prima barra H1 aggrega i primi 60 minuti
    first60 = df.iloc[:60]
    assert h1.iloc[0]["open"] == first60.iloc[0]["open"]
    assert h1.iloc[0]["close"] == first60.iloc[59]["close"]
    assert h1.iloc[0]["high"] == first60["high"].max()
    assert h1.iloc[0]["low"] == first60["low"].min()
    assert np.isclose(h1.iloc[0]["volume"], first60["volume"].sum())


def test_ohlc_invarianti():
    """Su qualunque aggregazione: high >= open/close/low, low <= tutto."""
    h4 = resample_ohlcv(_m1(240), "H4")
    assert (h4["high"] >= h4[["open", "close", "low"]].max(axis=1)).all()
    assert (h4["low"] <= h4[["open", "close", "high"]].min(axis=1)).all()


def test_volume_conservato():
    df = _m1(240)
    for tf in ("M5", "M15", "M30", "H1", "H4"):
        r = resample_ohlcv(df, tf)
        assert np.isclose(r["volume"].sum(), df["volume"].sum()), tf


def test_tf_non_valido():
    with pytest.raises(ValueError):
        resample_ohlcv(_m1(60), "X9")


def test_supported():
    assert "M1" in supported_timeframes() and "W" in supported_timeframes()
