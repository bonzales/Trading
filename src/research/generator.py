"""Generatore di strategie candidate: esplora uno spazio CURATO di varianti.

NON è ricerca casuale (quella fabbrica falsi vincitori). Combina mattoncini con senso
economico — i template validati del progetto — variandone i parametri entro griglie
piccole e sensate (TEMPLATE_PARAMS). Ogni candidato ha un ID stabile, così il registro
cumulativo (ledger) e la watchlist forward sanno riconoscerlo nel tempo.

Ogni notte il motore genera queste specifiche e le valuta col gate di robustezza; le
novità che passano finiscono in watchlist e vengono confermate SOLO se reggono sui
giorni successivi alla scoperta (difesa vera contro il data-mining).
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass, field

from src.research.templates import TEMPLATE_PARAMS
from src.research.universe import UNIVERSE, Instrument


@dataclass(frozen=True)
class Spec:
    symbol: str
    asset_class: str
    spread: float
    template: str
    timeframe: str
    params: dict = field(default_factory=dict)

    @property
    def label(self) -> str:
        if not self.params:
            return f"{self.template}"
        kv = ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return f"{self.template}[{kv}]"

    @property
    def id(self) -> str:
        raw = json.dumps({"s": self.symbol, "t": self.template, "tf": self.timeframe,
                          "p": self.params}, sort_keys=True)
        return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _param_combos(template: str, explore: bool) -> list[dict]:
    """Il set canonico ({}) più — se explore — la griglia curata di varianti."""
    combos = [{}]  # canonico (parametri di default)
    if explore and template in TEMPLATE_PARAMS:
        grid = TEMPLATE_PARAMS[template]
        keys = list(grid)
        for values in itertools.product(*(grid[k] for k in keys)):
            p = dict(zip(keys, values))
            if p not in combos:
                combos.append(p)
    return combos


def generate(timeframe: str, universe: tuple[Instrument, ...] = UNIVERSE,
             explore: bool = True) -> list[Spec]:
    """Elenca le specifiche candidate per un timeframe."""
    specs: list[Spec] = []
    for ins in universe:
        for tmpl in ins.templates:
            for params in _param_combos(tmpl, explore):
                specs.append(Spec(ins.symbol, ins.asset_class, ins.spread, tmpl, timeframe, params))
    return specs
