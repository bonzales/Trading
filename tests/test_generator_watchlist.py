"""Test di generatore, registro cumulativo e watchlist forward."""
import numpy as np
import pandas as pd

from src.research.generator import Spec, generate
from src.research.ledger import Ledger
from src.research.watchlist import Watchlist


def test_generate_esplora_varianti():
    from src.research.universe import Instrument
    uni = (Instrument("XAU_USD", "metal", 0.5, ("trend_long",)),)
    canon = generate("D", uni, explore=False)
    grid = generate("D", uni, explore=True)
    assert len(canon) == 1                      # solo canonico
    assert len(grid) > 1                        # canonico + varianti channel
    assert all(isinstance(s, Spec) for s in grid)


def test_spec_id_stabile_e_distinto():
    a = Spec("XAU_USD", "metal", 0.5, "trend_long", "D", {"channel": 55})
    b = Spec("XAU_USD", "metal", 0.5, "trend_long", "D", {"channel": 55})
    c = Spec("XAU_USD", "metal", 0.5, "trend_long", "D", {"channel": 20})
    assert a.id == b.id and a.id != c.id
    assert "channel=55" in a.label


def test_ledger_accumula(tmp_path):
    led = Ledger(tmp_path / "l.json")
    led.record(["a", "b", "a"]); led.save()
    led2 = Ledger(tmp_path / "l.json")           # persistito
    assert led2.n_distinct == 2                  # a, b
    assert led2.total_evaluations == 3
    led2.record(["c"]);
    assert led2.n_distinct == 3
    assert led2.expected_false_positives(0.05) == 3 * 0.05


def _price(n, start="2010-01-01"):
    t = pd.date_range(start, periods=n, freq="1D", tz="UTC")
    c = 100 + np.cumsum(np.random.default_rng(1).normal(0, 1, n))
    return pd.DataFrame({"time": t, "open": c, "high": c + 1, "low": c - 1, "close": c})


def test_watchlist_watching_se_poco_forward(tmp_path):
    wl = Watchlist(tmp_path / "w.json")
    spec = Spec("XAU_USD", "metal", 0.5, "trend_long", "D", {"channel": 40})
    assert wl.add_if_new(spec, 1.8, "2020-01-01") is True
    assert wl.add_if_new(spec, 1.8, "2020-01-02") is False   # gia' presente
    # forward cortissimo -> resta "watching"
    df = _price(30, "2020-01-01")
    wl.update_forward(lambda s, t: df, "2020-01-15")
    assert wl.items[spec.id].status == "watching"


def test_watchlist_persiste(tmp_path):
    wl = Watchlist(tmp_path / "w.json")
    spec = Spec("WTI", "commodity", 0.03, "trend_long", "D", {})
    wl.add_if_new(spec, 1.5, "2020-01-01"); wl.save()
    wl2 = Watchlist(tmp_path / "w.json")
    assert spec.id in wl2.items and wl2.items[spec.id].symbol == "WTI"
