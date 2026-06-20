"""Gestione del rischio: sizing, stop ATR, TP1 parziale + breakeven, trailing.

Regola madre ereditata da Kraken: il rischio si decide PRIMA del sizing, e il
sizing si basa sulla distanza dello stop, non sulla speranza. Aumentare leva o
numero di trade non sistema una strategia che non regge: ne moltiplica le perdite.

Modello (semplice ma onesto):
  - si rischia una frazione fissa dell'equity per trade (`risk_per_trade`);
  - lo stop è a `atr_mult` * ATR dal prezzo d'ingresso;
  - la size deriva da rischio_in_valuta / distanza_stop;
  - TP1 a `tp1_r` volte il rischio (R): si chiude `tp1_fraction` della posizione
    e si sposta lo stop a breakeven;
  - dopo TP1 lo stop traila di `trail_atr_mult` * ATR.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskParams:
    risk_per_trade: float = 0.01  # 1% dell'equity per trade
    atr_mult: float = 2.0  # distanza stop in multipli di ATR
    tp1_r: float = 1.5  # primo target in multipli di R
    tp1_fraction: float = 0.5  # frazione chiusa al TP1
    trail_atr_mult: float = 2.0  # trailing in multipli di ATR dopo il TP1


def stop_distance(atr: float, params: RiskParams) -> float:
    """Distanza (in prezzo) tra ingresso e stop iniziale."""
    return params.atr_mult * atr


def position_size(equity: float, atr: float, params: RiskParams) -> float:
    """Unità da comprare/vendere perché la perdita allo stop = risk_per_trade.

    perdita_allo_stop = size * distanza_stop = equity * risk_per_trade
    """
    dist = stop_distance(atr, params)
    if dist <= 0:
        return 0.0
    return (equity * params.risk_per_trade) / dist
