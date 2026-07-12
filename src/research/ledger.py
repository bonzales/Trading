"""Registro cumulativo delle ipotesi testate — memoria anti-multiple-testing.

Più combinazioni si provano nel tempo, più è probabile trovarne una "vincente" per
puro caso. Il registro tiene il conto di TUTTE le specifiche mai testate (per id) e di
quante valutazioni totali. Serve a due cose:
  - non ri-testare all'infinito la stessa cosa (accumula, come la wiki);
  - ricordare quanto abbiamo frugato, così sappiamo quanto scettici essere su una
    "scoperta" (falsi positivi attesi ≈ n_test × soglia).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class Ledger:
    def __init__(self, path: str | Path = "raw/research/ledger.json"):
        self.path = Path(path)
        self._data = {"seen_ids": {}, "total_evaluations": 0}
        if self.path.exists():
            self._data = json.loads(self.path.read_text())

    @property
    def n_distinct(self) -> int:
        return len(self._data["seen_ids"])

    @property
    def total_evaluations(self) -> int:
        return self._data["total_evaluations"]

    def record(self, spec_ids: list[str]) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        for sid in spec_ids:
            self._data["seen_ids"].setdefault(sid, today)
        self._data["total_evaluations"] += len(spec_ids)

    def expected_false_positives(self, alpha: float = 0.05) -> float:
        """Quante 'conferme' ci aspetteremmo per puro caso, dato quanto abbiamo cercato."""
        return self.n_distinct * alpha

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))
