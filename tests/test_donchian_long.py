"""Il Donchian solo-long non deve MAI emettere segnali short. Dati sintetici."""
import numpy as np
import pandas as pd

from src.core.strategy import FLAT, LONG, SHORT, make_strategy


def _ohlc_with_downbreaks(n=400, seed=3) -> pd.DataFrame:
    """Serie con rotture sia al rialzo sia al ribasso, così il Donchian classico
    genererebbe short: verifichiamo che la variante long li sopprima."""
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 1.0, n))
    high = close + rng.uniform(0.2, 0.6, n)
    low = close - rng.uniform(0.2, 0.6, n)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close})


def test_registro_donchian_long():
    s = make_strategy("donchian_long", channel=20)
    assert s.name == "donchian_long"


def test_mai_short():
    df = _ohlc_with_downbreaks()
    long_only = make_strategy("donchian_long", channel=20)
    classic = make_strategy("donchian", channel=20)
    data = long_only.prepare(df)
    sides_long = [long_only.signal(data, i).side for i in range(long_only.warmup, len(data))]
    sides_classic = [classic.signal(data, i).side for i in range(classic.warmup, len(data))]
    assert SHORT not in sides_long, "la variante long ha emesso uno short"
    # sanity: la serie generava davvero degli short nel Donchian classico
    assert SHORT in sides_classic
    # e i long sopravvivono (dove il classico è long, il long-only è long)
    assert any(s == LONG for s in sides_long)
    assert set(sides_long) <= {LONG, FLAT}
