"""Test del riepilogo Telegram del job notturno (stato watchlist)."""
from src.research.nightly import telegram_summary
from src.research.watchlist import Watched, Watchlist


class _WL:
    """Watchlist minima con stati prefissati."""
    def __init__(self, **counts):
        self._by = counts

    def by_status(self, status):
        return self._by.get(status, [])


def _w(symbol, template, status, fwd_pf=1.5, n=45, tf="D"):
    return Watched(spec_id="x", symbol=symbol, template=template, timeframe=tf,
                   params={}, spread=0.5, discovered="2020-01-01", discovery_pf=1.8,
                   status=status, fwd_pf=fwd_pf, fwd_trades=n)


def test_conteggi_base():
    msg = telegram_summary({"D": []}, {"D": {"n_combos": 100, "confirmed": 12}})
    assert "100 combo testate" in msg and "12 candidati" in msg


def test_nessun_graduato_niente_attenzione():
    wl = _WL(watching=[_w("US500", "mr_indices", "watching")], holding=[], failing=[], graduated=[])
    msg = telegram_summary({"D": []}, {"D": {"n_combos": 10, "confirmed": 1}}, wl)
    assert "Nessun graduato" in msg and "1 in osservazione" in msg


def test_graduato_va_segnalato():
    wl = _WL(watching=[], holding=[], failing=[],
             graduated=[_w("WTI", "trend_long", "graduated", fwd_pf=1.9, n=50)])
    msg = telegram_summary({"D": []}, {"D": {"n_combos": 10, "confirmed": 1}}, wl)
    assert "GRADUATI" in msg and "WTI" in msg and "fwd PF 1.90" in msg


def test_nuovi_candidati_segnalati():
    wl = _WL(watching=[], holding=[], failing=[], graduated=[])
    msg = telegram_summary({"D": []}, {"D": {"n_combos": 10, "confirmed": 2}}, wl, new_added=2)
    assert "2 nuovi candidati" in msg


def test_ledger_scetticismo_in_coda():
    class _L:
        n_distinct = 200
        def expected_false_positives(self, a=0.05):
            return 10.0
    wl = _WL(graduated=[])
    msg = telegram_summary({"D": []}, {"D": {"n_combos": 10, "confirmed": 0}}, wl, _L())
    assert "200 ipotesi" in msg and "falsi positivi" in msg
