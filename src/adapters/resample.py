"""Ricampionamento OHLCV: da un timeframe fine (es. M1) a uno più grande.

Principio: NON si scarica ogni timeframe separatamente. Si scarica il più fine
disponibile (M1 per l'intraday, D per la storia lunga) e si **derivano** gli altri
per aggregazione. Un H4 è solo M1 aggregato — scaricarlo a parte è spreco.

Regole di aggregazione OHLCV canoniche:
  open = primo, high = max, low = min, close = ultimo, volume = somma.

Timeframe supportati: M1, M5, M15, M30, H1, H4, D, W (mappati su frequenze pandas).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# timeframe del progetto -> frequenza pandas
_TF_FREQ = {
    "M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
    "H1": "1h", "H4": "4h", "D": "1D", "W": "W-MON",
}

# ordine crescente, per validare che si aggrega solo verso l'alto
_TF_ORDER = ["M1", "M5", "M15", "M30", "H1", "H4", "D", "W"]

_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def supported_timeframes() -> list[str]:
    return list(_TF_ORDER)


def resample_ohlcv(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """Aggrega un DataFrame OHLCV al timeframe `target_tf`.

    `df` deve avere una colonna `time` (datetime, UTC) e le colonne OHLC (volume
    opzionale). Ritorna un nuovo DataFrame con le stesse colonne, una riga per barra
    del nuovo timeframe, senza buchi vuoti (le finestre senza scambi vengono scartate).
    """
    if target_tf not in _TF_FREQ:
        raise ValueError(f"Timeframe '{target_tf}' non supportato. Validi: {_TF_ORDER}")
    if "time" not in df.columns:
        raise ValueError("Manca la colonna 'time'.")

    out = df.copy()
    out["time"] = pd.to_datetime(out["time"], utc=True)
    out = out.sort_values("time").set_index("time")

    agg = {c: how for c, how in _AGG.items() if c in out.columns}
    res = out.resample(_TF_FREQ[target_tf], label="left", closed="left").agg(agg)
    res = res.dropna(subset=["open", "high", "low", "close"])
    return res.reset_index()


def load_tf(instrument: str, target_tf: str, cache_dir: Path | str = "raw/cache") -> pd.DataFrame:
    """Carica `instrument` al timeframe richiesto, ricampionando dal file più fine.

    Strategia di sorgente:
      - target D o W  → parte dal file _D.csv (storia lunga), W = resample di D.
      - target intraday (M5..H4) → parte dal file _M1.csv (se presente).
      - M1 → il file _M1.csv così com'è.
    Solleva FileNotFoundError se la sorgente adatta non è in cache.
    """
    cache = Path(cache_dir)

    def _read(suffix: str) -> pd.DataFrame:
        p = cache / f"{instrument}_{suffix}.csv"
        if not p.exists():
            raise FileNotFoundError(f"Sorgente mancante: {p}")
        d = pd.read_csv(p)
        d["time"] = pd.to_datetime(d["time"], utc=True)
        return d

    if target_tf == "M1":
        return _read("M1").sort_values("time").reset_index(drop=True)
    if target_tf in ("D", "W"):
        base = _read("D")
        return base.sort_values("time").reset_index(drop=True) if target_tf == "D" else resample_ohlcv(base, "W")
    # intraday: dal M1
    return resample_ohlcv(_read("M1"), target_tf)
