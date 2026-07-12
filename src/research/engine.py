"""Il motore di ricerca: sweep dell'universo con GATE DI ROBUSTEZZA anti-overfitting.

Filosofia (la lezione madre del progetto): testare tante combinazioni PRODUCE per
caso dei falsi vincenti. Quindi NON classifichiamo per il PF più alto, ma per la
ROBUSTEZZA: una combinazione conta come `confirmed` solo se è positiva
  - sull'intero campione,
  - in ENTRAMBE le metà temporali,
  - e out-of-sample (train 60% → test 40%),
con abbastanza trade. Chi ha un bel PF pieno ma fallisce un gate è `suspect`
(probabile fortuna campione), non una scoperta. Il punteggio di ranking è il
PEGGIORE dei PF (pieno/metà/OOS): premia la coerenza, non il picco.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from src.adapters.resample import load_tf
from src.research.templates import run_template
from src.research.universe import UNIVERSE, Instrument


@dataclass
class Result:
    symbol: str
    asset_class: str
    timeframe: str
    template: str
    verdict: str          # confirmed | suspect | rejected | thin
    robust_score: float   # min(pf pieno, pf 1ª metà, pf 2ª metà, pf OOS)
    pf_full: float
    pf_h1: float
    pf_h2: float
    pf_train: float
    pf_oos: float
    sharpe: float | None
    maxdd: float
    n_trades: int


def _slice(df: pd.DataFrame, a: float, b: float) -> pd.DataFrame:
    n = len(df)
    return df.iloc[int(n * a):int(n * b)].reset_index(drop=True)


def evaluate(df: pd.DataFrame, template: str, spread: float, min_trades: int = 20) -> dict:
    """Valuta un template su un df applicando il gate di robustezza."""
    full = run_template(template, df, spread)
    h1 = run_template(template, _slice(df, 0.0, 0.5), spread)
    h2 = run_template(template, _slice(df, 0.5, 1.0), spread)
    tr = run_template(template, _slice(df, 0.0, 0.6), spread)
    oo = run_template(template, _slice(df, 0.6, 1.0), spread)

    def pf(x):
        v = x["pf"]
        return 0.0 if v == float("inf") else float(v)

    pfs = [pf(full), pf(h1), pf(h2), pf(oo)]
    if full["n"] < min_trades:
        verdict, score = "thin", 0.0
    elif pf(full) <= 1.0:
        verdict, score = "rejected", min(pfs)
    elif pf(h1) > 1 and pf(h2) > 1 and pf(oo) > 1:
        verdict, score = "confirmed", min(pfs)
    else:
        verdict, score = "suspect", min(pfs)
    return {"verdict": verdict, "robust_score": score, "pf_full": pf(full),
            "pf_h1": pf(h1), "pf_h2": pf(h2), "pf_train": pf(tr), "pf_oos": pf(oo),
            "sharpe": full["sharpe"], "maxdd": full["maxdd"], "n_trades": full["n"]}


_ORDER = {"confirmed": 0, "suspect": 1, "rejected": 2, "thin": 3}


def run_sweep(timeframe: str = "D", universe: tuple[Instrument, ...] = UNIVERSE,
              cache_dir: str = "raw/cache", min_trades: int = 20) -> list[Result]:
    """Sweepa l'universo su un timeframe. Salta gli strumenti senza dati per quel TF."""
    results: list[Result] = []
    for ins in universe:
        try:
            df = load_tf(ins.symbol, timeframe, cache_dir)
        except FileNotFoundError:
            continue
        if len(df) < 250:
            continue
        for tmpl in ins.templates:
            ev = evaluate(df, tmpl, ins.spread, min_trades)
            results.append(Result(ins.symbol, ins.asset_class, timeframe, tmpl, **ev))
    results.sort(key=lambda r: (_ORDER[r.verdict], -r.robust_score))
    return results


def summarize(results: list[Result]) -> dict:
    from collections import Counter
    c = Counter(r.verdict for r in results)
    return {"n_combos": len(results), "confirmed": c["confirmed"], "suspect": c["suspect"],
            "rejected": c["rejected"], "thin": c["thin"]}


def to_rows(results: list[Result]) -> list[dict]:
    return [asdict(r) for r in results]
