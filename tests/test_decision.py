"""Test della logica di decisione giornaliera mean-reversion (offline)."""
import numpy as np
import pandas as pd

from src.live.decision import MRParams, decide, position_size


def _bars(closes):
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame({
        "time": pd.date_range("2020-01-01", periods=len(closes), freq="D"),
        "open": closes, "high": closes + 1.0, "low": closes - 1.0,
        "close": closes, "volume": 1.0,
    })


def _uptrend(n=250, base=100.0, slope=1.0):
    return [base + slope * i for i in range(n)]


def test_buy_su_ipervenduto_in_uptrend():
    c = _uptrend()
    c[-2] = c[-3] - 15  # due giorni di forte calo → RSI2 crolla
    c[-1] = c[-2] - 15
    plan = decide(_bars(c), has_position=False, bars_held=None)
    assert plan.action == "BUY"
    assert plan.stop_price is not None and plan.stop_price < plan.close


def test_flat_nessun_setup_hold():
    c = _uptrend()  # ultimi giorni in salita → RSI2 alto → niente ingresso
    plan = decide(_bars(c), has_position=False, bars_held=None)
    assert plan.action == "HOLD"


def test_close_quando_rsi_risale():
    c = _uptrend()  # in salita → RSI2 alto → esci se sei long
    plan = decide(_bars(c), has_position=True, bars_held=2)
    assert plan.action == "CLOSE"


def test_close_per_max_hold():
    # coda in lieve calo: close < SMA5 (no exit MA) e RSI2 basso (no exit RSI),
    # così l'unico trigger resta il max_hold
    c = _uptrend(n=250)
    base = c[-6]
    c[-5:] = [base - 1, base - 2, base - 3, base - 4, base - 5]
    plan = decide(_bars(c), has_position=True, bars_held=10, p=MRParams(max_hold=10))
    assert plan.action == "CLOSE" and "max_hold" in plan.reason


def test_storia_insufficiente_hold():
    plan = decide(_bars(_uptrend(n=50)), has_position=False, bars_held=None)
    assert plan.action == "HOLD"


def test_position_size():
    # rischio 1% di 10000 = 100€; stop a 20 punti; point_value 1 → 5 contratti
    assert position_size(10000, 5000, 4980, point_value=1.0, p=MRParams(risk_pct=0.01)) == 5
    # dati non validi → 0
    assert position_size(10000, 5000, 5000, point_value=1.0, p=MRParams()) == 0
