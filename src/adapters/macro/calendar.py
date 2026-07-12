"""Calendario degli eventi macro ad alto impatto, per strumento.

Eventi DERIVABILI senza dati esterni:
  - NFP (buste paga USA): primo venerdì del mese. L'evento macro più importante,
    impatta tutto ciò che è denominato in USD (indici USA, oro, materie prime, FX major).

Eventi che richiedono un elenco di date (FOMC, CPI, BCE): si caricano da un CSV
opzionale `raw/cache/macro_events.csv` (colonne: date,event). Finché non c'è, si usa
solo l'NFP — onesto: meglio un evento derivato bene che tre date sbagliate a memoria.

Uso principale: `high_impact_flags(symbol, index)` → serie booleana dei giorni ad alto
impatto per quello strumento. Serve da FILTRO DI RISCHIO (size/stop), non da predittore
di direzione.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# quali strumenti sono sensibili a ciascun evento (USD-denominati → NFP li muove tutti).
# DAX/UK100 sono indici non-USA ma reagiscono al rischio globale → inclusi.
_USD_SENSITIVE = {
    "US500", "US30", "NAS100", "DAX", "UK100",
    "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CHF", "USD_CAD", "NZD_USD",
    "XAU_USD", "XAG_USD", "WTI", "BRENT", "NATGAS", "COPPER",
}
EVENT_RELEVANCE = {
    "NFP": _USD_SENSITIVE,
    "FOMC": _USD_SENSITIVE,
    "CPI": _USD_SENSITIVE,
    "ECB": {"EUR_USD", "DAX", "GBP_USD"},
}


def first_fridays(index: pd.DatetimeIndex) -> pd.Series:
    """True sui primi venerdì del mese (giorni NFP)."""
    idx = pd.DatetimeIndex(index)
    return pd.Series((idx.weekday == 4) & (idx.day <= 7), index=idx)


def load_extra_events(path: str | Path = "raw/cache/macro_events.csv") -> dict[str, set]:
    """Carica eventi extra (FOMC/CPI/ECB) da CSV se presente: date,event → {event: {date}}."""
    p = Path(path)
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    out: dict[str, set] = {}
    for _, row in df.iterrows():
        d = pd.to_datetime(row["date"], utc=True).normalize()
        out.setdefault(str(row["event"]).upper(), set()).add(d)
    return out


def high_impact_flags(symbol: str, index: pd.DatetimeIndex,
                      events: tuple[str, ...] = ("NFP",),
                      extra: dict[str, set] | None = None) -> pd.Series:
    """Serie booleana: True nei giorni ad alto impatto per `symbol`.

    Considera solo gli eventi in `events` che sono rilevanti per lo strumento.
    """
    idx = pd.DatetimeIndex(index)
    flag = pd.Series(False, index=idx)
    extra = extra or {}
    for ev in events:
        if symbol not in EVENT_RELEVANCE.get(ev, set()):
            continue
        if ev == "NFP":
            flag |= first_fridays(idx).values
        elif ev in extra:
            dates = extra[ev]
            flag |= pd.Series(idx.normalize().isin(dates), index=idx).values
    return flag
