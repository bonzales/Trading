"""Adapter dati Interactive Brokers — storico OHLCV, multi-strumento, multi-tf.

Responsabilità UNICA: portare candele OHLCV da IBKR in modo affidabile. Niente
strategie, niente rischio: quelli stanno nel cervello (src/core, src/backtest).
Cambiare broker = riscrivere solo questo file (stessa interfaccia del vecchio
adapter OANDA: `check_coverage`, `fetch_history`, `iter_candles`, …).

Differenze rispetto a OANDA, da tenere a mente:
  - IBKR NON è una REST con token. Si parla con un processo ponte (IB Gateway o
    TWS) via socket. Qui usiamo la libreria `ib_async` (fork mantenuto di
    ib_insync). Il Gateway deve essere acceso e loggato (sul VPS, headless).
  - La lezione n.1 di Kraken vive comunque qui: `reqHistoricalData` torna un
    numero limitato di barre per chiamata e ha *pacing limit*. Per questo
    `iter_candles` pagina all'indietro fino a coprire l'intervallo, e
    `check_coverage` usa `reqHeadTimeStamp` per sapere quanta storia REALE
    esiste senza scaricarla tutta.

Il modulo è progettato per essere testabile offline: tutte le funzioni "pure"
(mappature, shaping dei record, Coverage) non toccano la rete, e il client
accetta un oggetto IB iniettabile (vedi test) al posto della connessione vera.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterator

from src.config import Settings

# Durata di una candela in secondi, per i codici timeframe stile OANDA che il
# resto del sistema (CLI, engine) continua a usare. 'M' (mese) è calendario-
# dipendente e non ha durata fissa: non lo gestiamo qui.
_GRANULARITY_SECONDS = {
    "S5": 5, "S15": 15, "S30": 30,
    "M1": 60, "M2": 120, "M5": 300, "M10": 600, "M15": 900, "M30": 1800,
    "H1": 3600, "H2": 7200, "H3": 10800, "H4": 14400, "H8": 28800,
    "D": 86400, "W": 604800,
}

# Mappa timeframe nostro -> `barSizeSetting` IBKR.
_BAR_SIZE = {
    "S5": "5 secs", "S15": "15 secs", "S30": "30 secs",
    "M1": "1 min", "M2": "2 mins", "M5": "5 mins", "M10": "10 mins",
    "M15": "15 mins", "M30": "30 mins",
    "H1": "1 hour", "H2": "2 hours", "H3": "3 hours", "H4": "4 hours",
    "H8": "8 hours",
    "D": "1 day", "W": "1 week",
}

# Durata richiesta per ogni chiamata `reqHistoricalData` (durationStr IBKR), per
# timeframe. Tenuta conservativa per non sforare il pacing limit: poche barre per
# i tf piccoli, fino a 1 anno per quelli grandi.
_CHUNK_DURATION = {
    "S5": "3600 S", "S15": "14400 S", "S30": "28800 S",
    "M1": "2 D", "M2": "4 D", "M5": "1 W", "M10": "2 W", "M15": "1 M",
    "M30": "1 M",
    "H1": "2 M", "H2": "3 M", "H3": "6 M", "H4": "1 Y", "H8": "1 Y",
    "D": "1 Y", "W": "5 Y",
}

# price M/B/A -> whatToShow IBKR (per forex usiamo MIDPOINT/BID/ASK).
_WHAT_TO_SHOW = {"M": "MIDPOINT", "B": "BID", "A": "ASK"}


def granularity_to_seconds(granularity: str) -> int:
    """Durata di una candela in secondi. Solleva ValueError se sconosciuta."""
    try:
        return _GRANULARITY_SECONDS[granularity]
    except KeyError:
        raise ValueError(
            f"Granularità '{granularity}' non supportata. "
            f"Valide: {', '.join(_GRANULARITY_SECONDS)}."
        )


def bar_size(granularity: str) -> str:
    """`barSizeSetting` IBKR per il nostro codice timeframe."""
    try:
        return _BAR_SIZE[granularity]
    except KeyError:
        raise ValueError(
            f"Granularità '{granularity}' senza mappatura IBKR. "
            f"Valide: {', '.join(_BAR_SIZE)}."
        )


def to_ib_datetime(dt: datetime) -> str:
    """Formato endDateTime accettato da IBKR, in UTC esplicito.

    IBKR (TWS 9.73+) accetta 'YYYYMMDD-HH:MM:SS' interpretato come UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%d-%H:%M:%S")


def _bar_time_to_utc(value) -> datetime:
    """Normalizza il timestamp di una barra IBKR a datetime UTC (aware)."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):  # epoch (formatDate=2)
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
    else:  # stringa
        s = str(value).strip()
        # IBKR può tornare 'YYYYMMDD HH:MM:SS', 'YYYYMMDD' o ISO.
        for fmt in ("%Y%m%d %H:%M:%S", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(s.replace("Z", ""), fmt)
                break
            except ValueError:
                continue
        else:  # ultimo tentativo: ISO con tz
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def bars_to_records(bars) -> list[dict]:
    """Converte le barre IBKR in record OHLCV semplici e ordinati nel tempo.

    Funzione pura (nessuna rete): testabile offline. Accetta oggetti con
    attributi (`bar.date`, `bar.open`, …) oppure dict equivalenti. Il `volume`
    IBKR per il forex è spesso -1 (non significativo): lo normalizziamo a 0.
    """
    def attr(b, name):
        return b[name] if isinstance(b, dict) else getattr(b, name)

    out: list[dict] = []
    for b in bars:
        t = _bar_time_to_utc(attr(b, "date"))
        vol = attr(b, "volume")
        try:
            vol = int(vol)
        except (TypeError, ValueError):
            vol = 0
        out.append(
            {
                "time": t.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                "open": float(attr(b, "open")),
                "high": float(attr(b, "high")),
                "low": float(attr(b, "low")),
                "close": float(attr(b, "close")),
                "volume": max(vol, 0),
            }
        )
    out.sort(key=lambda r: r["time"])
    return out


def make_contract(instrument: str):
    """Risolve uno strumento (stile OANDA, es. 'EUR_USD') in un contratto IBKR.

    Per ora: coppie 'BASE_QUOTE' -> Forex('BASEQUOTE') (vale anche per metalli
    quotati come forex, es. 'XAU_USD'). Indici/CFD verranno aggiunti quando li
    testeremo davvero: meglio una mappa esplicita che indovinare.
    """
    from ib_async import Forex  # import locale: la libreria serve solo a runtime

    base, sep, quote = instrument.partition("_")
    if not sep:
        raise ValueError(
            f"Strumento '{instrument}' non riconosciuto. Usa il formato "
            f"'BASE_QUOTE' (es. EUR_USD, XAU_USD)."
        )
    return Forex(base + quote)


@dataclass
class Coverage:
    """Profondità storica REALE per (strumento, timeframe)."""

    instrument: str
    granularity: str
    earliest: datetime
    latest: datetime

    @property
    def span(self) -> timedelta:
        return self.latest - self.earliest

    @property
    def years(self) -> float:
        return self.span.total_seconds() / (365.25 * 86400)

    @property
    def theoretical_candles(self) -> int:
        """Candele teoriche se il mercato fosse aperto 24/7 (limite SUPERIORE).

        Il conteggio reale è minore: forex chiude nel weekend e fuori orario.
        Serve solo come sanity-check d'ordine di grandezza, non come verità.
        """
        return int(self.span.total_seconds() // granularity_to_seconds(self.granularity))


class IBKRDataClient:
    """Client storico IBKR basato su `ib_async`.

    L'esecuzione ordini (broker-specifica) vivrà in `execution.py`. Qui solo dati.

    Il client gestisce la connessione al Gateway/TWS. Per i test si può iniettare
    un oggetto `ib` finto (deve esporre `reqHistoricalData`, `reqHeadTimeStamp`,
    `isConnected`, `connect`, `disconnect`): così la logica di paginazione si
    verifica offline senza una connessione vera.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        ib=None,
        contract_factory=make_contract,
        pacing_sleep: float = 1.0,
        max_pages: int = 5000,
    ):
        self._settings = settings
        self._pacing_sleep = pacing_sleep
        self._max_pages = max_pages
        self._ib = ib  # se None, creato/connesso pigramente in _connect()
        # iniettabile nei test: evita di importare ib_async offline.
        self._make_contract = contract_factory

    # --- connessione -----------------------------------------------------------

    def _connect(self):
        """Restituisce un oggetto IB connesso (lazy). Riusa quello iniettato."""
        if self._ib is not None:
            if hasattr(self._ib, "isConnected") and not self._ib.isConnected():
                self._ib.connect(
                    self._settings.host, self._settings.port,
                    clientId=self._settings.client_id,
                )
            return self._ib

        from ib_async import IB  # import locale: serve solo a runtime
        ib = IB()
        ib.connect(
            self._settings.host, self._settings.port,
            clientId=self._settings.client_id,
        )
        self._ib = ib
        return ib

    def close(self) -> None:
        if self._ib is not None and hasattr(self._ib, "isConnected") and self._ib.isConnected():
            self._ib.disconnect()

    def __enter__(self) -> "IBKRDataClient":
        self._connect()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- una pagina di candele -------------------------------------------------

    def _request_bars(
        self,
        contract,
        granularity: str,
        end_time: datetime | None,
        duration: str,
        what_to_show: str,
    ):
        """Una singola `reqHistoricalData`. Isolata per poterla sostituire nei test."""
        ib = self._connect()
        return ib.reqHistoricalData(
            contract,
            endDateTime=to_ib_datetime(end_time) if end_time else "",
            durationStr=duration,
            barSizeSetting=bar_size(granularity),
            whatToShow=what_to_show,
            useRTH=False,          # mercato intero, non solo orario regolare
            formatDate=2,          # timestamp in epoch UTC: niente ambiguità tz
        )

    # --- paginazione storica (lezione n.1) ------------------------------------

    def iter_candles(
        self,
        instrument: str,
        granularity: str,
        from_time: datetime,
        to_time: datetime | None = None,
        *,
        price: str = "M",
    ) -> Iterator[dict]:
        """Pagina lo storico da `from_time` a `to_time` (default: adesso).

        IBKR scarica all'INDIETRO: ogni chiamata chiede `_CHUNK_DURATION` di barre
        che terminano a `end`. Spostiamo `end` alla barra più vecchia ricevuta
        finché non copriamo `from_time` o una pagina torna vuota. I record sono
        prodotti in ordine cronologico crescente, deduplicati a valle.
        """
        to_time = to_time or datetime.now(timezone.utc)
        what = _WHAT_TO_SHOW.get(price, "MIDPOINT")
        duration = _CHUNK_DURATION.get(granularity, "1 M")
        contract = self._make_contract(instrument)

        collected: list[dict] = []
        end = to_time
        seen_earliest: datetime | None = None
        for _ in range(self._max_pages):
            bars = self._request_bars(contract, granularity, end, duration, what)
            records = bars_to_records(bars)
            if not records:
                break
            collected.extend(records)
            earliest = _bar_time_to_utc(records[0]["time"].replace("Z", "+00:00"))
            if earliest <= from_time:
                break
            if seen_earliest is not None and earliest >= seen_earliest:
                break  # nessun progresso: evita loop infinito
            seen_earliest = earliest
            end = earliest
            if self._pacing_sleep:
                time.sleep(self._pacing_sleep)

        # dedup + ordina + ritaglia all'intervallo richiesto
        by_time = {r["time"]: r for r in collected}
        for t in sorted(by_time):
            rec = by_time[t]
            ts = _bar_time_to_utc(t.replace("Z", "+00:00"))
            if from_time <= ts <= to_time:
                yield rec

    def fetch_history(
        self,
        instrument: str,
        granularity: str,
        from_time: datetime,
        to_time: datetime | None = None,
        *,
        price: str = "M",
    ) -> list[dict]:
        """Storico completo e paginato come lista di record OHLCV."""
        return list(self.iter_candles(instrument, granularity, from_time, to_time, price=price))

    # --- profondità storica (lezione n.1) -------------------------------------

    def earliest_candle(self, instrument: str, granularity: str, *, price: str = "M") -> datetime | None:
        """Timestamp della PRIMA barra disponibile su IBKR per questo strumento.

        Usa `reqHeadTimeStamp`: una sola chiamata, nessun download massiccio.
        """
        ib = self._connect()
        contract = self._make_contract(instrument)
        what = _WHAT_TO_SHOW.get(price, "MIDPOINT")
        head = ib.reqHeadTimeStamp(contract, whatToShow=what, useRTH=False, formatDate=2)
        if not head:
            return None
        return _bar_time_to_utc(head)

    def latest_candle(self, instrument: str, granularity: str, *, price: str = "M") -> datetime | None:
        """Timestamp dell'ultima barra disponibile (chiede l'ultimo chunk corto)."""
        contract = self._make_contract(instrument)
        what = _WHAT_TO_SHOW.get(price, "MIDPOINT")
        # un chunk breve che termina "adesso": prendiamo l'ultima barra.
        short = {"D": "5 D", "W": "1 M"}.get(granularity, "1 D")
        bars = self._request_bars(contract, granularity, None, short, what)
        records = bars_to_records(bars)
        if not records:
            return None
        return _bar_time_to_utc(records[-1]["time"].replace("Z", "+00:00"))

    def check_coverage(self, instrument: str, granularity: str) -> Coverage | None:
        """Quanta storia REALE esiste, senza scaricarla tutta. None se assente."""
        earliest = self.earliest_candle(instrument, granularity)
        latest = self.latest_candle(instrument, granularity)
        if earliest is None or latest is None:
            return None
        return Coverage(instrument, granularity, earliest, latest)
