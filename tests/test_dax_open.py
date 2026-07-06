"""Test offline della strategia intraday DAX open-volume, su una giornata sintetica.

Costruiamo un giorno con una candela-segnale ad alto volume e un rimbalzo di
supporto, e verifichiamo che find_signal la trovi e run_day apra un long corretto.
"""
import pandas as pd

from src.backtest.dax_open import DaxOpenConfig, backtest, find_signal, run_day


def _synthetic_day():
    idx = pd.date_range("2025-06-16 08:30", "2025-06-16 09:35", freq="1min",
                        tz="Europe/Berlin")
    df = pd.DataFrame(
        {"open": 95.0, "high": 95.0, "low": 95.0, "close": 95.0, "volume": 1.0},
        index=idx,
    )
    def setbar(hm, o, h, l, c, v):
        ts = pd.Timestamp(f"2025-06-16 {hm}", tz="Europe/Berlin")
        df.loc[ts, ["open", "high", "low", "close", "volume"]] = [o, h, l, c, v]

    # candela segnale 09:01: volume 8x baseline (=1), rialzista, zona [90,100]
    setbar("09:01", 91, 100, 90, 98, 8.0)
    # 09:02: prezzo sale sopra la zona (prepara "venuto dall'alto")
    setbar("09:02", 99, 106, 98, 105, 1.0)
    # 09:03: rientra sulla zona (low 101 ~ estremo alto) e rimbalza su -> LONG
    setbar("09:03", 102, 104, 101, 104, 1.0)
    return df


def test_find_signal_trova_candela_volume():
    sig = find_signal(_synthetic_day(), DaxOpenConfig())
    assert sig is not None
    assert sig["high"] == 100 and sig["low"] == 90 and sig["close"] == 98
    assert sig["ratio"] >= 5.0


def test_run_day_apre_long_su_rimbalzo():
    cfg = DaxOpenConfig()
    tr = run_day(_synthetic_day(), cfg)
    assert tr is not None
    assert tr.side == "long"
    # stop dietro il minimo della candela segnale (90) meno buffer (2)
    assert abs(tr.stop - 88.0) < 1e-9
    # rischio = entry(104 + mezzo spread) - stop(88)
    assert abs(tr.r_points - (104 + cfg.spread_pts / 2 - 88)) < 1e-9
    assert tr.reason == "session_close"  # i dati finiscono alle 09:35


def test_backtest_nessun_setup_giorno_piatto():
    # giorno senza picco di volume: nessun trade
    idx = pd.date_range("2025-06-17 08:30", "2025-06-17 09:35", freq="1min",
                        tz="Europe/Berlin")
    flat = pd.DataFrame(
        {"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 1.0},
        index=idx,
    ).reset_index(names="time")
    flat["time"] = flat["time"].dt.tz_convert("UTC")
    res = backtest(flat, DaxOpenConfig())
    assert res["metrics"]["n_trades"] == 0
