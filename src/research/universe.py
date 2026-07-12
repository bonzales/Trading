"""L'universo degli strumenti liquidi e quali template testare su ciascuno.

Lo spread è in unità di PREZZO (per gli indici = punti indice). I template sono i
nomi delle strategie candidate: il motore li prova tutti e lascia che sia il gate di
robustezza a separare l'edge dal rumore — così "testiamo tutte le possibilità" senza
farci ingannare dal miglior numero (vedi src/research/engine.py).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset_class: str          # index | fx | metal | commodity
    spread: float             # in unità di prezzo
    templates: tuple[str, ...]


# template candidati per classe di asset (proviamo sia MR sia trend ovunque abbia senso)
_IDX_T = ("mr_indices", "trend_long", "trend_ls")
_FX_T = ("mr_fx", "trend_long", "trend_ls")
_CMD_T = ("trend_long", "trend_ls", "mr_fx")   # commodity vogliono trend; mr_fx come controprova

UNIVERSE: tuple[Instrument, ...] = (
    # indici
    Instrument("US500", "index", 0.6, _IDX_T),
    Instrument("NAS100", "index", 2.5, _IDX_T),
    Instrument("US30", "index", 3.5, _IDX_T),
    Instrument("DAX", "index", 1.5, _IDX_T),
    Instrument("UK100", "index", 1.5, _IDX_T),
    # forex major
    Instrument("EUR_USD", "fx", 0.00010, _FX_T),
    Instrument("GBP_USD", "fx", 0.00015, _FX_T),
    Instrument("USD_JPY", "fx", 0.010, _FX_T),
    Instrument("AUD_USD", "fx", 0.00012, _FX_T),
    Instrument("USD_CHF", "fx", 0.00012, _FX_T),
    Instrument("USD_CAD", "fx", 0.00013, _FX_T),
    Instrument("NZD_USD", "fx", 0.00018, _FX_T),
    # metalli
    Instrument("XAU_USD", "metal", 0.5, _CMD_T),
    Instrument("XAG_USD", "metal", 0.02, _CMD_T),
    # materie prime
    Instrument("WTI", "commodity", 0.03, _CMD_T),
    Instrument("BRENT", "commodity", 0.03, _CMD_T),
    Instrument("NATGAS", "commodity", 0.005, _CMD_T),
    Instrument("COPPER", "commodity", 0.001, _CMD_T),
)


def by_symbol(symbol: str) -> Instrument:
    for ins in UNIVERSE:
        if ins.symbol == symbol:
            return ins
    raise KeyError(symbol)
