"""Test del backtester mean-reversion simmetrico forex. Dati sintetici, niente rete."""
import numpy as np
import pandas as pd

from src.backtest.fx_meanrev import FxMeanRevConfig, backtest


def _oscillating(n=600, seed=1) -> pd.DataFrame:
    """Sinusoide + rumore: RSI(2) scende sotto 10 e sale sopra 90 a ripetizione,
    così il backtester genera SIA long SIA short (comportamento simmetrico)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    close = 1.10 + 0.02 * np.sin(t / 3.0) + rng.normal(0, 0.0008, n)
    high = close + rng.uniform(0.0002, 0.0006, n)
    low = close - rng.uniform(0.0002, 0.0006, n)
    times = pd.date_range("2010-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"time": times, "open": close, "high": high, "low": low, "close": close})


def test_genera_long_e_short():
    """Il mean-reversion forex è simmetrico: su una serie oscillante deve aprire
    posizioni in entrambe le direzioni."""
    res = backtest(_oscillating(), FxMeanRevConfig(spread=0.0001))
    m = res["metrics"]
    assert m["n_long"] > 0, "nessun long generato"
    assert m["n_short"] > 0, "nessuno short generato"
    assert m["n_trades"] == m["n_long"] + m["n_short"]


def test_metriche_presenti_e_coerenti():
    res = backtest(_oscillating(), FxMeanRevConfig())
    m = res["metrics"]
    for k in ("n_trades", "win_rate", "profit_factor", "expectancy_R", "max_drawdown"):
        assert k in m
    assert 0.0 <= m["win_rate"] <= 1.0
    assert m["max_drawdown"] <= 0.0


def test_stop_protegge_dalla_deriva():
    """Prezzo che scende monotòno dopo un picco: uno short deve chiudere in profitto,
    ma un long aperto sull'ipervenduto viene protetto dallo stop (non scende all'infinito).
    Verifichiamo che esistano uscite 'stop' quando lo stop è stretto."""
    df = _oscillating()
    stretto = backtest(df, FxMeanRevConfig(atr_stop=1.0, spread=0.0001))
    largo = backtest(df, FxMeanRevConfig(atr_stop=6.0, spread=0.0001))
    stop_stretti = sum(1 for t in stretto["trades"] if t.reason == "stop")
    stop_larghi = sum(1 for t in largo["trades"] if t.reason == "stop")
    assert stop_stretti >= stop_larghi
    assert stop_stretti > 0


def test_spread_erode_il_risultato():
    """Aumentando lo spread, l'expectancy per trade non può migliorare."""
    df = _oscillating()
    basso = backtest(df, FxMeanRevConfig(spread=0.00005))["metrics"]["expectancy_R"]
    alto = backtest(df, FxMeanRevConfig(spread=0.0005))["metrics"]["expectancy_R"]
    assert alto <= basso
