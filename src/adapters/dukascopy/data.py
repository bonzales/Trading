"""Adapter dati Dukascopy — storico OHLCV gratuito per il backtesting.

Responsabilità UNICA: portare candele OHLCV da Dukascopy in modo affidabile,
nella STESSA forma degli altri adapter (record con time/open/high/low/close/
volume, `check_coverage`, `fetch_history`). Il resto del sistema (engine,
data_fetcher, report) non sa e non deve sapere da dove vengono i dati.

Dukascopy fornisce BID e ASK separati (niente "mid"). Per il prezzo M (mid)
scarichiamo entrambi i lati e ne facciamo la media OHLC: è il mid più onesto che
possiamo costruire. Lo spread reale lo modella comunque il CostModel nel backtest.

La libreria `dukascopy_python` fa la paginazione e il download; qui ci mettiamo la
mappatura strumenti/timeframe e la lezione n.1 (profondità storica REALE).
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.timeframes import Coverage

# Mappa dei nostri codici timeframe -> costanti intervallo Dukascopy.
# Nota: Dukascopy non ha H2/H3/H8/S5 come barre aggregate: non li mappiamo.
_INTERVAL = {
    "M1": "INTERVAL_MIN_1", "M5": "INTERVAL_MIN_5", "M10": "INTERVAL_MIN_10",
    "M15": "INTERVAL_MIN_15", "M30": "INTERVAL_MIN_30",
    "H1": "INTERVAL_HOUR_1", "H4": "INTERVAL_HOUR_4",
    "D": "INTERVAL_DAY_1", "W": "INTERVAL_WEEK_1",
}


def resolve_interval(granularity: str):
    """Costante intervallo Dukascopy per il nostro codice timeframe."""
    import dukascopy_python as d

    name = _INTERVAL.get(granularity)
    if name is None:
        raise ValueError(
            f"Timeframe '{granularity}' non supportato da Dukascopy in questo "
            f"adapter. Validi: {', '.join(_INTERVAL)}."
        )
    return getattr(d, name)


def resolve_instrument(instrument: str):
    """Risolve 'EUR_USD' nella costante strumento Dukascopy corrispondente.

    Le costanti Dukascopy sono raggruppate (INSTRUMENT_FX_MAJORS_EUR_USD,
    INSTRUMENT_FX_METALS_XAU_USD, …). Cerchiamo per suffisso così non dobbiamo
    conoscere il gruppo a priori.
    """
    from dukascopy_python import instruments as I

    suffix = f"_{instrument.upper()}"
    matches = [n for n in dir(I) if n.startswith("INSTRUMENT_") and n.endswith(suffix)]
    if not matches:
        raise ValueError(
            f"Strumento '{instrument}' non trovato tra le costanti Dukascopy. "
            f"Usa il formato BASE_QUOTE (es. EUR_USD, XAU_USD, GBP_USD)."
        )
    if len(matches) > 1:
        # Preferiamo i major/metals espliciti se c'è ambiguità.
        matches.sort(key=lambda n: ("MAJORS" not in n, "METALS" not in n, n))
    return getattr(I, matches[0])


def _df_to_records(df) -> list[dict]:
    """DataFrame Dukascopy (index=timestamp UTC) -> record OHLCV standard."""
    out: list[dict] = []
    for ts, row in df.iterrows():
        t = ts.to_pydatetime().astimezone(timezone.utc)
        out.append(
            {
                "time": t.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]) if row["volume"] == row["volume"] else 0,
            }
        )
    return out


def _average_ohlc(bid_df, ask_df):
    """Media OHLC di bid e ask -> mid. Allinea sugli indici comuni."""
    common = bid_df.index.intersection(ask_df.index)
    b, a = bid_df.loc[common], ask_df.loc[common]
    mid = (b[["open", "high", "low", "close"]] + a[["open", "high", "low", "close"]]) / 2.0
    mid["volume"] = b["volume"].fillna(0) + a["volume"].fillna(0)
    return mid


class DukascopyDataClient:
    """Client storico Dukascopy. Nessuna credenziale, nessun processo ponte."""

    def __init__(self):
        # import ritardato: la libreria serve solo a runtime (test offline felici).
        import dukascopy_python as d
        self._d = d

    # --- candele ---------------------------------------------------------------

    def fetch_history(
        self,
        instrument: str,
        granularity: str,
        from_time: datetime,
        to_time: datetime | None = None,
        *,
        price: str = "M",
    ) -> list[dict]:
        """Storico completo come lista di record OHLCV (paginazione a carico lib)."""
        d = self._d
        to_time = to_time or datetime.now(timezone.utc)
        interval = resolve_interval(granularity)
        symbol = resolve_instrument(instrument)

        if price == "M":
            bid = d.fetch(symbol, interval, d.OFFER_SIDE_BID, from_time, to_time)
            ask = d.fetch(symbol, interval, d.OFFER_SIDE_ASK, from_time, to_time)
            df = _average_ohlc(bid, ask)
        else:
            side = d.OFFER_SIDE_ASK if price == "A" else d.OFFER_SIDE_BID
            df = d.fetch(symbol, interval, side, from_time, to_time)

        if df is None or len(df) == 0:
            return []
        return _df_to_records(df.sort_index())

    # --- profondità storica (lezione n.1) -------------------------------------

    def check_coverage(self, instrument: str, granularity: str) -> Coverage | None:
        """Quanta storia REALE esiste. Sonda con candele giornaliere da lontano.

        Non scarica il timeframe fine (sarebbe pesante): usa il daily dal 2000 per
        misurare l'estensione, poi la riporta sul timeframe richiesto.
        """
        d = self._d
        symbol = resolve_instrument(instrument)
        probe = d.fetch(
            symbol, d.INTERVAL_DAY_1, d.OFFER_SIDE_BID,
            datetime(2000, 1, 1, tzinfo=timezone.utc),
            datetime.now(timezone.utc),
        )
        if probe is None or len(probe) == 0:
            return None
        earliest = probe.index[0].to_pydatetime().astimezone(timezone.utc)
        latest = probe.index[-1].to_pydatetime().astimezone(timezone.utc)
        return Coverage(instrument, granularity, earliest, latest)
