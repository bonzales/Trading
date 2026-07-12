"""Test dei moduli COT: parsing e fattori. Nessuna rete (fixture in memoria)."""
import numpy as np
import pandas as pd

from src.adapters.cot.download import parse_cot
from src.adapters.cot.factor import add_factors, align_to_daily


def _records(n=200):
    recs = []
    for i in range(n):
        recs.append({
            "report_date_as_yyyy_mm_dd": (pd.Timestamp("2010-01-05", tz="UTC") + pd.Timedelta(weeks=i)).isoformat(),
            "open_interest_all": "100000",
            "noncomm_positions_long_all": str(30000 + i * 50),
            "noncomm_positions_short_all": "20000",
            "comm_positions_long_all": "40000",
            "comm_positions_short_all": str(50000 + i * 50),
        })
    return recs


def test_parse_ordina_e_tipizza():
    df = parse_cot(_records(10))
    assert list(df.columns) == ["date", "oi", "nc_long", "nc_short", "c_long", "c_short"]
    assert df["date"].is_monotonic_increasing
    assert df["oi"].dtype.kind in "if"  # numerico (int o float)
    assert len(df) == 10


def test_parse_vuoto():
    df = parse_cot([])
    assert df.empty and "net_comm" not in df.columns


def test_factors_net_e_index():
    df = add_factors(parse_cot(_records(200)), window=156)
    # net = (long-short)/oi
    row = df.iloc[0]
    assert np.isclose(row["net_spec"], (row["nc_long"] - row["nc_short"]) / row["oi"])
    # il COT index sta in [0,100] dove definito
    idx = df["cot_index_spec"].dropna()
    assert (idx >= 0).all() and (idx <= 100).all()
    # con net_spec crescente monotòno, l'ultimo COT index deve essere ~100
    assert df["cot_index_spec"].iloc[-1] > 95


def test_align_no_lookahead():
    cot = add_factors(parse_cot(_records(50)))
    daily = pd.date_range("2010-01-01", "2010-06-30", freq="1D", tz="UTC")
    al = align_to_daily(cot, daily)
    # prima del primo report i valori sono NaN (nessun look-ahead)
    assert al.loc[al.index < cot["date"].iloc[0]].isna().all().all()
    # dopo, forward-fill: nessun NaN una volta iniziati i dati
    assert not al.loc[al.index >= cot["date"].iloc[0]]["net_comm"].isna().all()
