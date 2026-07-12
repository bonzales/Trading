"""Scarica il COT dall'API pubblica CFTC (Socrata), instradando ogni strumento al
report GIUSTO:

  - Disaggregated (72hh-3qpy) per le COMMODITY → isola Managed Money (fondi trend) e
    Producer/Merchant (veri hedger). Molto meglio del Legacy grezzo.
  - Traders in Financial Futures / TFF (gpe5-46if) per FOREX e INDICI → isola
    Leveraged Funds (hedge fund = speculatori) e Asset Manager (real money).
  - Legacy (6dca-aqww) come fallback (categorie grossolane commercial/non-commercial).

Tutti i report vengono NORMALIZZATI allo stesso schema:
    date, oi, nc_long, nc_short (gruppo "speculatori/fondi"), c_long, c_short ("hedger").
Così factor.py li tratta allo stesso modo. La parte di rete è separata dal parsing (testabile).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

_ENDPOINT = "https://publicreporting.cftc.gov/resource/{dataset}.json"

# campi sorgente → schema normalizzato, per ciascun tipo di report.
# nc_* = gruppo speculativo/fondi; c_* = gruppo hedger/istituzionale.
LEGACY_FIELDS = {
    "report_date_as_yyyy_mm_dd": "date", "open_interest_all": "oi",
    "noncomm_positions_long_all": "nc_long", "noncomm_positions_short_all": "nc_short",
    "comm_positions_long_all": "c_long", "comm_positions_short_all": "c_short",
}
DISAGG_FIELDS = {
    "report_date_as_yyyy_mm_dd": "date", "open_interest_all": "oi",
    "m_money_positions_long_all": "nc_long", "m_money_positions_short_all": "nc_short",
    "prod_merc_positions_long": "c_long", "prod_merc_positions_short": "c_short",
}
TFF_FIELDS = {
    "report_date_as_yyyy_mm_dd": "date", "open_interest_all": "oi",
    "lev_money_positions_long": "nc_long", "lev_money_positions_short": "nc_short",
    "asset_mgr_positions_long": "c_long", "asset_mgr_positions_short": "c_short",
}

_REPORTS = {
    "legacy": {"dataset": "6dca-aqww", "fields": LEGACY_FIELDS},
    "disaggregated": {"dataset": "72hh-3qpy", "fields": DISAGG_FIELDS},
    "tff": {"dataset": "gpe5-46if", "fields": TFF_FIELDS},
}

# strumento → (report giusto, codice contratto CFTC)
SYMBOL_ROUTING: dict[str, tuple[str, str]] = {
    # commodity → Disaggregated (Managed Money vs Producer)
    "XAU_USD": ("disaggregated", "088691"), "XAG_USD": ("disaggregated", "084691"),
    "COPPER": ("disaggregated", "085692"), "WTI": ("disaggregated", "067651"),
    "NATGAS": ("disaggregated", "023651"),
    # forex + indici → TFF (Leveraged Funds vs Asset Manager)
    "EUR_USD": ("tff", "099741"), "GBP_USD": ("tff", "096742"), "USD_JPY": ("tff", "097741"),
    "AUD_USD": ("tff", "232741"), "USD_CAD": ("tff", "090741"), "USD_CHF": ("tff", "092741"),
    "NZD_USD": ("tff", "112741"),
    "US500": ("tff", "13874+"), "NAS100": ("tff", "209742"), "US30": ("tff", "12460+"),
    # DAX, UK100: non disponibili (futures europei, fuori CFTC)
}

_NUM = ["oi", "nc_long", "nc_short", "c_long", "c_short"]


def parse_cot(records: list[dict], fields: dict = LEGACY_FIELDS) -> pd.DataFrame:
    """Normalizza i record grezzi (di un qualsiasi report) nello schema comune."""
    cols = ["date", *_NUM]
    if not records:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(records).rename(columns=fields)
    df = df[[c for c in cols if c in df.columns]]
    df["date"] = pd.to_datetime(df["date"], utc=True)
    for c in _NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)


def fetch_cot(symbol: str, cache_dir: str | Path = "raw/cache/cot", refresh: bool = False) -> pd.DataFrame:
    """Scarica (o legge da cache) lo storico COT per uno strumento, dal report giusto."""
    if symbol not in SYMBOL_ROUTING:
        raise KeyError(f"{symbol} non ha un contratto CFTC noto. Disponibili: {list(SYMBOL_ROUTING)}")
    report, code = SYMBOL_ROUTING[symbol]
    spec = _REPORTS[report]
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{symbol}_{report}_cot.csv"
    if path.exists() and not refresh:
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"], utc=True)
        return df

    import requests
    params = {
        "$where": f"cftc_contract_market_code='{code}'",
        "$select": ",".join(spec["fields"]),
        "$limit": 50000,
        "$order": "report_date_as_yyyy_mm_dd",
    }
    resp = requests.get(_ENDPOINT.format(dataset=spec["dataset"]), params=params, timeout=60)
    resp.raise_for_status()
    df = parse_cot(resp.json(), spec["fields"])
    df.to_csv(path, index=False)
    return df
