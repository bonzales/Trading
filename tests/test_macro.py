"""Test del calendario macro e dell'event-study. Niente rete."""
import numpy as np
import pandas as pd

from src.adapters.macro.calendar import first_fridays, high_impact_flags
from src.adapters.macro.eventstudy import event_study, size_multiplier


def test_primi_venerdi():
    idx = pd.date_range("2024-01-01", "2024-03-31", freq="1D", tz="UTC")
    ff = first_fridays(idx)
    marked = idx[ff.values]
    # gennaio 2024: primo venerdì = 5; febbraio = 2; marzo = 1
    assert set(m.day for m in marked) <= {5, 2, 1}
    assert all(m.weekday() == 4 for m in marked)
    assert len(marked) == 3


def test_flag_rilevanza_strumento():
    idx = pd.date_range("2024-01-01", "2024-06-30", freq="1D", tz="UTC")
    us = high_impact_flags("US500", idx, events=("NFP",))
    ecb_only = high_impact_flags("US500", idx, events=("ECB",))  # US500 non tra i rilevanti ECB
    assert us.sum() > 0
    assert ecb_only.sum() == 0


def test_event_study_rileva_vol():
    # costruisco una serie dove i primi venerdì hanno rendimenti più grandi
    idx = pd.date_range("2020-01-01", "2023-12-31", freq="B", tz="UTC")
    rng = np.random.default_rng(0)
    ff = first_fridays(idx).values
    ret = rng.normal(0, 0.005, len(idx))
    ret[ff] = rng.normal(0, 0.02, ff.sum())  # venerdì NFP più volatili
    close = 100 * np.exp(np.cumsum(ret))
    df = pd.DataFrame({"time": idx, "close": close})
    flag = pd.Series(ff, index=idx)
    res = event_study(df, flag)
    assert res["vol_ratio"] > 1.5      # deve accorgersi della vol maggiore
    assert res["n_event"] > 20


def test_size_multiplier():
    assert size_multiplier(True, damp=0.5) == 0.5
    assert size_multiplier(False) == 1.0
