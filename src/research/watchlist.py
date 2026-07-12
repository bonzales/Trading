"""Watchlist forward — la difesa VERA contro il data-mining.

Un candidato che passa il gate sul backtest NON viene creduto: viene messo in
osservazione con la sua data di scoperta. Ogni notte se ne misura la performance SOLO
sui dati SUCCESSIVI alla scoperta — barre che non poteva aver "adattato". Un candidato
diventa credibile solo se continua a funzionare su questo out-of-sample reale (il
futuro), esattamente come il paper trading.

Stati:
  watching  → scoperto da poco, non abbastanza dati/trade forward per giudicare
  holding   → sta reggendo sul forward (PF forward > 1 con abbastanza trade)
  failing   → sul forward non regge (PF forward <= 1)
  graduated → ha retto abbastanza a lungo sul forward → merita revisione umana per la wiki
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.research.generator import Spec
from src.research.templates import run_template

MIN_FWD_TRADES = 15        # trade forward minimi per dare un giudizio
GRADUATE_TRADES = 40       # trade forward per "graduato" (promuovibile a revisione)


@dataclass
class Watched:
    spec_id: str
    symbol: str
    template: str
    timeframe: str
    params: dict
    spread: float
    discovered: str            # data di scoperta (ISO)
    discovery_pf: float
    status: str = "watching"
    fwd_pf: float = 0.0
    fwd_trades: int = 0
    last_checked: str = ""
    note: str = ""


def _fwd_slice(df: pd.DataFrame, since_iso: str) -> pd.DataFrame:
    ts = pd.to_datetime(since_iso, utc=True)
    return df[pd.to_datetime(df["time"], utc=True) > ts].reset_index(drop=True)


class Watchlist:
    def __init__(self, path: str | Path = "raw/research/watchlist.json"):
        self.path = Path(path)
        self.items: dict[str, Watched] = {}
        if self.path.exists():
            for row in json.loads(self.path.read_text()):
                self.items[row["spec_id"]] = Watched(**row)

    def add_if_new(self, spec: Spec, discovery_pf: float, today: str) -> bool:
        """Registra un nuovo candidato scoperto oggi. True se era davvero nuovo."""
        if spec.id in self.items:
            return False
        self.items[spec.id] = Watched(
            spec_id=spec.id, symbol=spec.symbol, template=spec.template,
            timeframe=spec.timeframe, params=dict(spec.params), spread=spec.spread,
            discovered=today, discovery_pf=float(discovery_pf))
        return True

    def update_forward(self, load_df, today: str) -> None:
        """Ricalcola la performance forward di ogni candidato (solo dati post-scoperta).

        `load_df(symbol, timeframe) -> DataFrame OHLC` fornisce i prezzi.
        """
        for w in self.items.values():
            try:
                df = load_df(w.symbol, w.timeframe)
            except Exception:
                continue
            fwd = _fwd_slice(df, w.discovered)
            w.last_checked = today
            if len(fwd) < 60:
                w.status, w.note = "watching", "pochi dati forward"
                continue
            res = run_template(w.template, fwd, w.spread, w.params)
            w.fwd_pf = float(res["pf"]) if res["pf"] != float("inf") else 0.0
            w.fwd_trades = int(res["n"])
            if w.fwd_trades < MIN_FWD_TRADES:
                w.status, w.note = "watching", f"solo {w.fwd_trades} trade forward"
            elif w.fwd_pf <= 1.0:
                w.status, w.note = "failing", f"forward PF {w.fwd_pf:.2f} (non regge)"
            elif w.fwd_trades >= GRADUATE_TRADES:
                w.status, w.note = "graduated", f"forward PF {w.fwd_pf:.2f} su {w.fwd_trades} trade"
            else:
                w.status, w.note = "holding", f"forward PF {w.fwd_pf:.2f} su {w.fwd_trades} trade"

    def by_status(self, status: str) -> list[Watched]:
        return [w for w in self.items.values() if w.status == status]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(w) for w in self.items.values()], indent=2))
