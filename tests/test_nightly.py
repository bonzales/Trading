"""Test del riepilogo Telegram del job notturno (rilevamento novità)."""
from src.research.engine import Result
from src.research.nightly import telegram_summary


def _r(symbol, template, tf="D", verdict="confirmed", pf=1.5):
    return Result(symbol, "index", tf, template, verdict, pf, pf, pf, pf, pf, pf, None, -0.1, 100)


def test_nessuna_novita_se_tutto_noto():
    res = {"D": [_r("US500", "mr_indices")]}  # gia' in KNOWN_D
    msg = telegram_summary(res, {"D": {"n_combos": 1, "confirmed": 1}})
    assert "Nessuna novità" in msg


def test_segnala_novita_daily():
    res = {"D": [_r("USD_JPY", "mr_fx")]}  # non in KNOWN_D
    msg = telegram_summary(res, {"D": {"n_combos": 1, "confirmed": 1}})
    assert "Novità" in msg and "USD_JPY" in msg


def test_intraday_confermato_e_sempre_novita():
    res = {"H4": [_r("US500", "mr_indices", tf="H4")]}  # noto a D, ma H4 e' nuovo
    msg = telegram_summary(res, {"H4": {"n_combos": 1, "confirmed": 1}})
    assert "Novità" in msg and "H4" in msg


def test_suspect_non_e_novita():
    res = {"D": [_r("USD_JPY", "mr_fx", verdict="suspect")]}
    msg = telegram_summary(res, {"D": {"n_combos": 1, "confirmed": 0}})
    assert "Nessuna novità" in msg
