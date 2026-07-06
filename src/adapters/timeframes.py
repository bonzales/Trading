"""Definizioni condivise tra adapter dati: timeframe e profondità storica.

Vivono qui, non dentro un singolo adapter, perché sono verità del DOMINIO (un'ora
è un'ora a prescindere dal broker). Ogni adapter (IBKR, Dukascopy, …) le importa.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

# Durata di una candela in secondi, per i codici timeframe stile OANDA che tutto
# il sistema (CLI, engine) continua a usare. 'M' (mese) è calendario-dipendente e
# non ha durata fissa: non lo gestiamo qui.
_GRANULARITY_SECONDS = {
    "S5": 5, "S15": 15, "S30": 30,
    "M1": 60, "M2": 120, "M5": 300, "M10": 600, "M15": 900, "M30": 1800,
    "H1": 3600, "H2": 7200, "H3": 10800, "H4": 14400, "H8": 28800,
    "D": 86400, "W": 604800,
}


def granularity_to_seconds(granularity: str) -> int:
    """Durata di una candela in secondi. Solleva ValueError se sconosciuta."""
    try:
        return _GRANULARITY_SECONDS[granularity]
    except KeyError:
        raise ValueError(
            f"Granularità '{granularity}' non supportata. "
            f"Valide: {', '.join(_GRANULARITY_SECONDS)}."
        )


@dataclass
class Coverage:
    """Profondità storica REALE per (strumento, timeframe)."""

    instrument: str
    granularity: str
    earliest: datetime
    latest: datetime

    @property
    def span(self) -> timedelta:
        return self.latest - self.earliest

    @property
    def years(self) -> float:
        return self.span.total_seconds() / (365.25 * 86400)

    @property
    def theoretical_candles(self) -> int:
        """Candele teoriche se il mercato fosse aperto 24/7 (limite SUPERIORE).

        Il conteggio reale è minore: forex chiude nel weekend e fuori orario.
        Serve solo come sanity-check d'ordine di grandezza, non come verità.
        """
        return int(self.span.total_seconds() // granularity_to_seconds(self.granularity))
