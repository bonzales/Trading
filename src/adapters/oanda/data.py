"""Adapter dati OANDA — storico profondo, multi-strumento, multi-timeframe.

Responsabilità UNICA: portare candele OHLCV da OANDA in modo affidabile. Niente
strategie, niente rischio: quelli stanno nel cervello (src/core, src/backtest).
Cambiare broker = riscrivere solo questo file.

La lezione n.1 di Kraken vive qui: l'API restituisce un numero limitato di candele
per richiesta (OANDA: max 5000). Chi non pagina crede di avere "3 anni" e ne ha 7
giorni. Per questo:
  - `iter_candles` pagina fino a coprire davvero l'intervallo richiesto;
  - `check_coverage` dice quanta storia REALE esiste, senza scaricarla tutta.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterator

import requests

from src.config import Settings

# OANDA restituisce al massimo questo numero di candele per richiesta.
MAX_CANDLES_PER_REQUEST = 5000

# Durata di una candela in secondi, per granularità OANDA.
# 'M' (mese) è calendario-dipendente e non ha una durata fissa: gestito a parte.
_GRANULARITY_SECONDS = {
    "S5": 5, "S10": 10, "S15": 15, "S30": 30,
    "M1": 60, "M2": 120, "M4": 240, "M5": 300, "M10": 600, "M15": 900, "M30": 1800,
    "H1": 3600, "H2": 7200, "H3": 10800, "H4": 14400, "H6": 21600, "H8": 28800,
    "H12": 43200,
    "D": 86400, "W": 604800,
}


def granularity_to_seconds(granularity: str) -> int:
    """Durata di una candela in secondi. Solleva ValueError se sconosciuta."""
    try:
        return _GRANULARITY_SECONDS[granularity]
    except KeyError:
        raise ValueError(
            f"Granularità '{granularity}' non supportata. "
            f"Valide: {', '.join(_GRANULARITY_SECONDS)}."
        )


def to_rfc3339(dt: datetime) -> str:
    """Formato timestamp accettato da OANDA (UTC, secondi interi)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")


def parse_candles(payload: dict, price: str = "M") -> list[dict]:
    """Estrae le candele complete da una risposta OANDA in record semplici.

    Funzione pura (nessuna rete): testabile offline. Le candele incomplete
    (l'ultima ancora in formazione) vengono SCARTATE: non sono fonte di verità.
    """
    field = {"M": "mid", "B": "bid", "A": "ask"}[price]
    out: list[dict] = []
    for c in payload.get("candles", []):
        if not c.get("complete", False):
            continue
        ohlc = c[field]
        out.append(
            {
                "time": c["time"],
                "open": float(ohlc["o"]),
                "high": float(ohlc["h"]),
                "low": float(ohlc["l"]),
                "close": float(ohlc["c"]),
                "volume": int(c.get("volume", 0)),
            }
        )
    return out


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


class OandaDataClient:
    """Client REST minimale per le candele OANDA v20.

    Usa `requests` direttamente per avere controllo pieno su paginazione, retry e
    rate limit. L'esecuzione ordini (broker-specifica) vivrà in `execution.py`.
    """

    def __init__(self, settings: Settings, *, timeout: float = 30.0, max_retries: int = 4):
        self._settings = settings
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {settings.api_token}",
                "Content-Type": "application/json",
            }
        )

    # --- HTTP grezzo -----------------------------------------------------------

    def _get(self, path: str, params: dict) -> dict:
        """GET con retry/backoff su errori di rete e rate limit (429/5xx)."""
        url = f"{self._settings.host}{path}"
        delay = 2.0
        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._session.get(url, params=params, timeout=self._timeout)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
                resp.raise_for_status()
                return resp.json()
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as err:
                last_err = err
                if attempt == self._max_retries - 1:
                    break
                time.sleep(delay)
                delay *= 2  # backoff esponenziale: 2s, 4s, 8s, 16s
        raise RuntimeError(f"Richiesta OANDA fallita dopo {self._max_retries} tentativi: {last_err}")

    def _candles_request(self, instrument: str, params: dict) -> dict:
        return self._get(f"/v3/instruments/{instrument}/candles", params)

    # --- candele ---------------------------------------------------------------

    def get_candles(
        self,
        instrument: str,
        granularity: str,
        *,
        count: int | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        price: str = "M",
        include_first: bool | None = None,
    ) -> list[dict]:
        """Una singola richiesta di candele (max 5000). Per lo storico usa fetch_history."""
        params: dict = {"granularity": granularity, "price": price}
        if count is not None:
            params["count"] = min(count, MAX_CANDLES_PER_REQUEST)
        if from_time is not None:
            params["from"] = to_rfc3339(from_time)
        if to_time is not None:
            params["to"] = to_rfc3339(to_time)
        if include_first is not None:
            params["includeFirst"] = str(include_first).lower()
        return parse_candles(self._candles_request(instrument, params), price)

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

        Avanza il cursore all'istante successivo all'ultima candela ricevuta, così
        non duplica né salta candele. Si ferma quando una pagina torna vuota o si
        supera `to_time`.
        """
        to_time = to_time or datetime.now(timezone.utc)
        step = timedelta(seconds=granularity_to_seconds(granularity))
        cursor = from_time
        first = True
        while cursor < to_time:
            batch = self.get_candles(
                instrument,
                granularity,
                count=MAX_CANDLES_PER_REQUEST,
                from_time=cursor,
                price=price,
                include_first=first,
            )
            if not batch:
                break
            for rec in batch:
                yield rec
            last_time = datetime.fromisoformat(batch[-1]["time"].replace("Z", "+00:00"))
            cursor = last_time + step
            first = False

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

    def earliest_candle(self, instrument: str, granularity: str) -> datetime | None:
        """Timestamp della PRIMA candela disponibile su OANDA per questo tf.

        Chiede una sola candela partendo da un passato remoto: OANDA risponde con
        la più antica che possiede. Una richiesta, nessun download massiccio.
        """
        records = self.get_candles(
            instrument,
            granularity,
            from_time=datetime(2000, 1, 1, tzinfo=timezone.utc),
            count=1,
            include_first=True,
        )
        if not records:
            return None
        return datetime.fromisoformat(records[0]["time"].replace("Z", "+00:00"))

    def latest_candle(self, instrument: str, granularity: str) -> datetime | None:
        """Timestamp dell'ultima candela COMPLETA disponibile."""
        records = self.get_candles(instrument, granularity, count=2)
        if not records:
            return None
        return datetime.fromisoformat(records[-1]["time"].replace("Z", "+00:00"))

    def check_coverage(self, instrument: str, granularity: str) -> Coverage | None:
        """Quanta storia REALE esiste, senza scaricarla tutta. None se assente."""
        earliest = self.earliest_candle(instrument, granularity)
        latest = self.latest_candle(instrument, granularity)
        if earliest is None or latest is None:
            return None
        return Coverage(instrument, granularity, earliest, latest)
