"""Test offline dell'adapter dati: nessuna rete, nessuna credenziale.

Verifichiamo la logica pura (parsing, granularità, coverage) e la paginazione,
con un client finto che simula le risposte OANDA.
"""
from datetime import datetime, timezone

import pytest

from src.adapters.oanda.data import (
    Coverage,
    OandaDataClient,
    granularity_to_seconds,
    parse_candles,
    to_rfc3339,
)
from src.config import Settings


def _candle(t, c, complete=True):
    return {"time": t, "complete": complete, "volume": 10,
            "mid": {"o": "1.0", "h": "1.1", "l": "0.9", "c": str(c)}}


def test_granularity_to_seconds():
    assert granularity_to_seconds("H1") == 3600
    assert granularity_to_seconds("M5") == 300
    assert granularity_to_seconds("D") == 86400
    with pytest.raises(ValueError):
        granularity_to_seconds("X9")


def test_parse_candles_scarta_incomplete():
    payload = {"candles": [
        _candle("2026-01-01T00:00:00.000000000Z", 1.05),
        _candle("2026-01-01T01:00:00.000000000Z", 1.06, complete=False),
    ]}
    rows = parse_candles(payload)
    assert len(rows) == 1
    assert rows[0]["close"] == 1.05
    assert rows[0]["high"] == 1.1


def test_to_rfc3339_forza_utc():
    dt = datetime(2026, 6, 20, 12, 0, 0)
    assert to_rfc3339(dt).endswith("Z")
    assert "2026-06-20T12:00:00" in to_rfc3339(dt)


def test_coverage_calcola_anni_e_candele_teoriche():
    cov = Coverage(
        "EUR_USD", "H1",
        earliest=datetime(2023, 1, 1, tzinfo=timezone.utc),
        latest=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert 2.99 < cov.years < 3.01
    # 3 anni di ore, limite superiore 24/7
    assert cov.theoretical_candles == pytest.approx(3 * 365 * 24, rel=0.01)


class _FakeClient(OandaDataClient):
    """Sovrascrive l'HTTP: serve pagine finte invece di chiamare OANDA."""

    def __init__(self, pages):
        settings = Settings(account_id="x", api_token="y", environment="practice")
        super().__init__(settings)
        self._pages = pages
        self.calls = 0

    def _candles_request(self, instrument, params):
        page = self._pages[self.calls] if self.calls < len(self._pages) else {"candles": []}
        self.calls += 1
        return page


def test_iter_candles_pagina_e_si_ferma():
    # due pagine piene + una vuota -> deve concatenare e fermarsi
    page1 = {"candles": [_candle(f"2026-01-01T{h:02d}:00:00.000000000Z", 1.0 + h / 100) for h in range(3)]}
    page2 = {"candles": [_candle(f"2026-01-01T{h:02d}:00:00.000000000Z", 1.0 + h / 100) for h in range(3, 6)]}
    client = _FakeClient([page1, page2, {"candles": []}])

    rows = client.fetch_history(
        "EUR_USD", "H1",
        from_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        to_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    assert len(rows) == 6
    times = [r["time"] for r in rows]
    assert times == sorted(times)  # concatenate in ordine cronologico
    assert times[0].startswith("2026-01-01T00:00:00")
    assert client.calls == 3
