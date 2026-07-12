"""Studio dell'effetto degli eventi macro su uno strumento + filtro di rischio.

Misura se i giorni ad alto impatto sono davvero diversi (soprattutto in VOLATILITÀ) e
fornisce il moltiplicatore di size da usare come filtro di rischio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def event_study(df: pd.DataFrame, flag: pd.Series) -> dict:
    """Confronta rendimento e volatilità giornalieri nei giorni-evento vs gli altri.

    `df` con colonne time, close. `flag` booleana allineata alle stesse date.
    """
    d = df.copy()
    d["time"] = pd.to_datetime(d["time"], utc=True)
    d = d.set_index("time")
    ret = d["close"].pct_change()
    f = pd.Series(flag).copy()
    f.index = pd.to_datetime(f.index, utc=True) if not isinstance(f.index, pd.DatetimeIndex) else f.index
    f = f.reindex(ret.index).fillna(False).astype(bool)

    r_ev = ret[f].dropna()
    r_ot = ret[~f].dropna()
    if len(r_ev) < 20 or r_ot.std() == 0:
        return {"n_event": len(r_ev), "vol_ratio": 1.0, "mean_event": 0.0,
                "mean_other": 0.0, "vol_event": 0.0, "vol_other": 0.0}
    return {
        "n_event": int(len(r_ev)),
        "vol_event": float(r_ev.std()),
        "vol_other": float(r_ot.std()),
        "vol_ratio": float(r_ev.std() / r_ot.std()),
        "mean_event": float(r_ev.mean()),
        "mean_other": float(r_ot.mean()),
    }


def size_multiplier(is_event_day: bool, damp: float = 0.5) -> float:
    """Moltiplicatore di size per il filtro di rischio: nei giorni-evento riduce
    l'esposizione (damp=0.5 → metà size). Nessuna pretesa di prevedere la direzione,
    solo di non farsi sorprendere dalla volatilità.
    """
    return damp if is_event_day else 1.0
