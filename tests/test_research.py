"""Test del motore di ricerca: la logica del GATE di robustezza è la parte critica."""
import numpy as np
import pandas as pd

import src.research.engine as engine
from src.research.engine import evaluate, run_sweep, summarize


def _df(n=800):
    t = pd.date_range("2010-01-01", periods=n, freq="1D", tz="UTC")
    c = 100 + np.cumsum(np.random.default_rng(0).normal(0, 1, n))
    return pd.DataFrame({"time": t, "open": c, "high": c + 1, "low": c - 1, "close": c})


def _stub(pf_full, pf_h1, pf_h2, pf_train, pf_oos, n=100):
    """Restituisce un run_template finto che dà PF diversi per ciascuna fetta,
    riconoscendo la fetta dalla lunghezza del df passato."""
    def fake(name, df, spread, params=None):
        L = len(df)
        full = 800
        if L == full: pf = pf_full
        elif L == 400: pf = pf_h1 if df["close"].iloc[0] == FULL["close"].iloc[0] else pf_h2
        elif L == 480: pf = pf_train
        elif L == 320: pf = pf_oos
        else: pf = pf_full
        return {"pf": pf, "win": 0.5, "maxdd": -0.1, "n": n, "sharpe": None}
    return fake


FULL = _df(800)


def test_confirmed_quando_tutto_positivo(monkeypatch):
    monkeypatch.setattr(engine, "run_template", _stub(2.0, 1.5, 1.8, 1.6, 1.7))
    ev = evaluate(FULL, "x", 0.0)
    assert ev["verdict"] == "confirmed"
    assert ev["robust_score"] == 1.5  # il minimo dei PF


def test_suspect_quando_una_meta_fallisce(monkeypatch):
    monkeypatch.setattr(engine, "run_template", _stub(1.8, 0.9, 1.8, 1.6, 1.7))  # 1ª metà <1
    assert evaluate(FULL, "x", 0.0)["verdict"] == "suspect"


def test_suspect_quando_oos_fallisce(monkeypatch):
    monkeypatch.setattr(engine, "run_template", _stub(1.5, 1.2, 1.3, 1.4, 0.9))  # OOS <1
    assert evaluate(FULL, "x", 0.0)["verdict"] == "suspect"


def test_rejected_quando_pieno_non_positivo(monkeypatch):
    monkeypatch.setattr(engine, "run_template", _stub(0.9, 1.2, 1.3, 1.1, 1.2))
    assert evaluate(FULL, "x", 0.0)["verdict"] == "rejected"


def test_thin_quando_pochi_trade(monkeypatch):
    monkeypatch.setattr(engine, "run_template", _stub(2.0, 1.5, 1.8, 1.6, 1.7, n=5))
    assert evaluate(FULL, "x", 0.0, min_trades=20)["verdict"] == "thin"


def test_smoke_sweep_dati_reali():
    """Sweep su un mini-universo con dati reali: US500 MR dev'essere confermato."""
    from src.research.universe import Instrument
    uni = (Instrument("US500", "index", 0.6, ("mr_indices",)),)
    res = run_sweep(timeframe="D", universe=uni)
    assert len(res) == 1
    assert res[0].symbol == "US500"
    assert res[0].verdict == "confirmed"
    s = summarize(res)
    assert s["n_combos"] == 1 and s["confirmed"] == 1
