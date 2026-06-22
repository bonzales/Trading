"""Test offline dell'adapter dati IBKR: nessuna rete, nessuna connessione.

Verifichiamo la logica pura (mappature, shaping dei record, coverage) e la
paginazione all'indietro, con un oggetto IB finto che simula `reqHistoricalData`
e `reqHeadTimeStamp`.
"""
from datetime import datetime, timezone

import pytest

from src.adapters.ibkr.data import (
    Coverage,
    IBKRDataClient,
    bar_size,
    bars_to_records,
    granularity_to_seconds,
    to_ib_datetime,
)
from src.config import Settings


def _settings():
    return Settings(
        account_id="DU123", host="127.0.0.1", port=4002,
        client_id=1, environment="practice",
    )


class _Bar:
    """Mima una BarData di ib_async (attributi date/open/high/low/close/volume)."""

    def __init__(self, date, close):
        self.date = date
        self.open = 1.0
        self.high = 1.1
        self.low = 0.9
        self.close = close
        self.volume = -1  # forex IBKR: volume non significativo -> normalizzato a 0


def test_granularity_to_seconds():
    assert granularity_to_seconds("H1") == 3600
    assert granularity_to_seconds("M5") == 300
    assert granularity_to_seconds("D") == 86400
    with pytest.raises(ValueError):
        granularity_to_seconds("X9")


def test_bar_size_mapping():
    assert bar_size("H1") == "1 hour"
    assert bar_size("M15") == "15 mins"
    assert bar_size("D") == "1 day"
    with pytest.raises(ValueError):
        bar_size("X9")


def test_bars_to_records_normalizza_e_ordina():
    bars = [
        _Bar("20260101 01:00:00", 1.06),
        _Bar("20260101 00:00:00", 1.05),  # arriva fuori ordine
    ]
    rows = bars_to_records(bars)
    assert len(rows) == 2
    assert rows[0]["time"].startswith("2026-01-01T00:00:00")  # riordinato
    assert rows[0]["close"] == 1.05
    assert rows[0]["high"] == 1.1
    assert rows[0]["volume"] == 0  # -1 normalizzato a 0


def test_bars_to_records_accetta_epoch_e_dict():
    epoch = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
    rows = bars_to_records([
        {"date": epoch, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 7},
    ])
    assert rows[0]["time"].startswith("2026-01-01T00:00:00")
    assert rows[0]["volume"] == 7


def test_to_ib_datetime_forza_utc():
    dt = datetime(2026, 6, 20, 12, 0, 0)
    assert to_ib_datetime(dt) == "20260620-12:00:00"


def test_coverage_calcola_anni_e_candele_teoriche():
    cov = Coverage(
        "EUR_USD", "H1",
        earliest=datetime(2023, 1, 1, tzinfo=timezone.utc),
        latest=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert 2.99 < cov.years < 3.01
    assert cov.theoretical_candles == pytest.approx(3 * 365 * 24, rel=0.01)


class _FakeIB:
    """IB finto: serve pagine all'indietro per testare la paginazione.

    `pages` è una lista di liste di barre, restituite in ordine: ogni chiamata a
    reqHistoricalData consuma la pagina successiva (l'ultima vuota ferma il loop).
    """

    def __init__(self, pages, head=None):
        self._pages = pages
        self._head = head
        self.calls = 0

    def isConnected(self):
        return True

    def connect(self, *a, **k):
        pass

    def disconnect(self):
        pass

    def reqHistoricalData(self, *a, **k):
        page = self._pages[self.calls] if self.calls < len(self._pages) else []
        self.calls += 1
        return page

    def reqHeadTimeStamp(self, *a, **k):
        return self._head


def test_iter_candles_pagina_indietro_e_si_ferma():
    # IBKR scarica all'indietro: pagina 1 = più recente, pagina 2 = più vecchia.
    page_recent = [_Bar(f"20260101 {h:02d}:00:00", 1.0 + h / 100) for h in range(3, 6)]
    page_old = [_Bar(f"20260101 {h:02d}:00:00", 1.0 + h / 100) for h in range(0, 3)]
    ib = _FakeIB([page_recent, page_old, []])
    client = IBKRDataClient(_settings(), ib=ib, pacing_sleep=0, contract_factory=lambda inst: inst)

    rows = client.fetch_history(
        "EUR_USD", "H1",
        from_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        to_time=datetime(2026, 1, 1, 23, tzinfo=timezone.utc),
    )
    assert len(rows) == 6
    times = [r["time"] for r in rows]
    assert times == sorted(times)  # output cronologico crescente
    assert times[0].startswith("2026-01-01T00:00:00")


def test_iter_candles_dedup():
    # due pagine che si sovrappongono su una barra -> niente duplicati
    overlap = _Bar("20260101 02:00:00", 1.02)
    page1 = [_Bar("20260101 03:00:00", 1.03), overlap]
    page2 = [_Bar("20260101 02:00:00", 1.02), _Bar("20260101 01:00:00", 1.01)]
    ib = _FakeIB([page1, page2, []])
    client = IBKRDataClient(_settings(), ib=ib, pacing_sleep=0, contract_factory=lambda inst: inst)

    rows = client.fetch_history(
        "EUR_USD", "H1",
        from_time=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        to_time=datetime(2026, 1, 1, 3, tzinfo=timezone.utc),
    )
    times = [r["time"] for r in rows]
    assert len(times) == len(set(times)) == 3


def test_check_coverage_usa_headtimestamp():
    head = int(datetime(2005, 1, 3, tzinfo=timezone.utc).timestamp())
    last = [_Bar("20260101 00:00:00", 1.05)]
    ib = _FakeIB([last], head=head)
    client = IBKRDataClient(_settings(), ib=ib, pacing_sleep=0, contract_factory=lambda inst: inst)

    cov = client.check_coverage("EUR_USD", "H1")
    assert cov is not None
    assert cov.earliest.year == 2005
    assert cov.latest.year == 2026
    assert cov.years > 20
