"""Il motore di ricerca: valuta le specifiche generate col GATE DI ROBUSTEZZA.

Filosofia (la lezione madre del progetto): testare tante combinazioni PRODUCE per
caso dei falsi vincenti. Quindi NON classifichiamo per il PF più alto, ma per la
ROBUSTEZZA: `confirmed` solo se positiva su intero campione + ENTRAMBE le metà
temporali + out-of-sample (train 60% → test 40%), con abbastanza trade. Chi ha un bel
PF pieno ma fallisce un gate è `suspect` (probabile fortuna campione). Il punteggio è
il PEGGIORE dei PF: premia la coerenza, non il picco.

La conferma DEFINITIVA non avviene qui: un `confirmed` è solo un CANDIDATO, che va poi
retto sul forward (vedi watchlist.py).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from src.adapters.resample import load_tf
from src.research.generator import Spec, generate
from src.research.templates import run_template
from src.research.universe import UNIVERSE, Instrument


@dataclass
class Result:
    symbol: str
    asset_class: str
    spread: float
    timeframe: str
    template: str          # nome base del template
    label: str             # template + parametri (per display)
    spec_id: str
    params: dict
    verdict: str           # confirmed | suspect | rejected | thin
    robust_score: float    # min(pf pieno, pf 1ª metà, pf 2ª metà, pf OOS)
    pf_full: float
    pf_h1: float
    pf_h2: float
    pf_train: float
    pf_oos: float
    sharpe: float | None
    maxdd: float
    n_trades: int

    def to_spec(self) -> Spec:
        return Spec(self.symbol, self.asset_class, self.spread, self.template,
                    self.timeframe, dict(self.params))


def _slice(df: pd.DataFrame, a: float, b: float) -> pd.DataFrame:
    n = len(df)
    return df.iloc[int(n * a):int(n * b)].reset_index(drop=True)


def _pf(x: dict) -> float:
    v = x["pf"]
    return 0.0 if v == float("inf") else float(v)


def evaluate(df: pd.DataFrame, template: str, spread: float, min_trades: int = 20,
             params: dict | None = None) -> dict:
    """Valuta un template (con parametri) su un df applicando il gate di robustezza."""
    full = run_template(template, df, spread, params)
    h1 = run_template(template, _slice(df, 0.0, 0.5), spread, params)
    h2 = run_template(template, _slice(df, 0.5, 1.0), spread, params)
    tr = run_template(template, _slice(df, 0.0, 0.6), spread, params)
    oo = run_template(template, _slice(df, 0.6, 1.0), spread, params)

    pfs = [_pf(full), _pf(h1), _pf(h2), _pf(oo)]
    if full["n"] < min_trades:
        verdict, score = "thin", 0.0
    elif _pf(full) <= 1.0:
        verdict, score = "rejected", min(pfs)
    elif _pf(h1) > 1 and _pf(h2) > 1 and _pf(oo) > 1:
        verdict, score = "confirmed", min(pfs)
    else:
        verdict, score = "suspect", min(pfs)
    return {"verdict": verdict, "robust_score": score, "pf_full": _pf(full),
            "pf_h1": _pf(h1), "pf_h2": _pf(h2), "pf_train": _pf(tr), "pf_oos": _pf(oo),
            "sharpe": full["sharpe"], "maxdd": full["maxdd"], "n_trades": full["n"]}


_ORDER = {"confirmed": 0, "suspect": 1, "rejected": 2, "thin": 3}


def run_sweep(timeframe: str = "D", universe: tuple[Instrument, ...] = UNIVERSE,
              cache_dir: str = "raw/cache", min_trades: int = 20,
              explore: bool = False) -> list[Result]:
    """Genera le specifiche (canoniche, o + varianti se explore) e le valuta.

    Salta gli strumenti/timeframe senza dati. explore=True esplora la griglia di
    parametri curata (il generatore "prova qualcosa di diverso").
    """
    specs = generate(timeframe, universe, explore=explore)
    # carica ogni df una sola volta
    cache: dict[str, pd.DataFrame | None] = {}
    results: list[Result] = []
    for spec in specs:
        if spec.symbol not in cache:
            try:
                df = load_tf(spec.symbol, timeframe, cache_dir)
                cache[spec.symbol] = df if len(df) >= 250 else None
            except FileNotFoundError:
                cache[spec.symbol] = None
        df = cache[spec.symbol]
        if df is None:
            continue
        ev = evaluate(df, spec.template, spec.spread, min_trades, spec.params)
        results.append(Result(spec.symbol, spec.asset_class, spec.spread, timeframe,
                              spec.template, spec.label, spec.id, dict(spec.params), **ev))
    results.sort(key=lambda r: (_ORDER[r.verdict], -r.robust_score))
    return results


def summarize(results: list[Result]) -> dict:
    from collections import Counter
    c = Counter(r.verdict for r in results)
    return {"n_combos": len(results), "confirmed": c["confirmed"], "suspect": c["suspect"],
            "rejected": c["rejected"], "thin": c["thin"]}


def to_rows(results: list[Result]) -> list[dict]:
    return [asdict(r) for r in results]
