"""Scarica il COT (Legacy Futures-Only) dall'API pubblica CFTC (Socrata).

La parte di rete e la parte di parsing sono separate, così il parser è testabile
senza toccare Internet. I dati sono settimanali; li mettiamo in cache in raw/cache/cot/.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

CFTC_ENDPOINT = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

# strumento del progetto -> codice contratto CFTC (canonici, verificati)
SYMBOL_TO_CODE: dict[str, str] = {
    "XAU_USD": "088691",  # GOLD - COMEX
    "XAG_USD": "084691",  # SILVER - COMEX
    "COPPER": "085692",   # COPPER grade #1 - COMEX
    "WTI": "067651",      # CRUDE OIL LIGHT SWEET - NYMEX
    "NATGAS": "023651",   # NATURAL GAS Henry Hub - NYMEX
    "EUR_USD": "099741",  # EURO FX - CME
    "GBP_USD": "096742",  # BRITISH POUND - CME
    "USD_JPY": "097741",  # JAPANESE YEN - CME
    "AUD_USD": "232741",  # AUSTRALIAN DOLLAR - CME
    "USD_CAD": "090741",  # CANADIAN DOLLAR - CME
    "USD_CHF": "092741",  # SWISS FRANC - CME
    "NZD_USD": "112741",  # NEW ZEALAND DOLLAR - CME
    "US500": "13874+",    # E-MINI S&P 500 consolidated - CME
    "NAS100": "209742",   # NASDAQ-100 E-MINI - CME
    "US30": "12460+",     # DJIA consolidated - CBOT
    # DAX, UK100: non disponibili (futures europei, fuori CFTC)
}

_COLS = {
    "report_date_as_yyyy_mm_dd": "date",
    "open_interest_all": "oi",
    "noncomm_positions_long_all": "nc_long",
    "noncomm_positions_short_all": "nc_short",
    "comm_positions_long_all": "c_long",
    "comm_positions_short_all": "c_short",
}


def parse_cot(records: list[dict]) -> pd.DataFrame:
    """Trasforma i record grezzi dell'API in un DataFrame settimanale pulito e ordinato."""
    if not records:
        return pd.DataFrame(columns=["date", "oi", "nc_long", "nc_short", "c_long", "c_short"])
    df = pd.DataFrame(records)
    df = df[[c for c in _COLS if c in df.columns]].rename(columns=_COLS)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    for c in ["oi", "nc_long", "nc_short", "c_long", "c_short"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)


def fetch_cot(symbol: str, cache_dir: str | Path = "raw/cache/cot", refresh: bool = False) -> pd.DataFrame:
    """Scarica (o legge da cache) lo storico COT per uno strumento del progetto."""
    if symbol not in SYMBOL_TO_CODE:
        raise KeyError(f"{symbol} non ha un contratto CFTC noto. Disponibili: {list(SYMBOL_TO_CODE)}")
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{symbol}_cot.csv"
    if path.exists() and not refresh:
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"], utc=True)
        return df

    import requests
    code = SYMBOL_TO_CODE[symbol]
    params = {
        "$where": f"cftc_contract_market_code='{code}'",
        "$select": ",".join(_COLS),
        "$limit": 50000,
        "$order": "report_date_as_yyyy_mm_dd",
    }
    resp = requests.get(CFTC_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    df = parse_cot(resp.json())
    df.to_csv(path, index=False)
    return df
