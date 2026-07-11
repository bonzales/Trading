"""Adapter di ESECUZIONE Interactive Brokers (paper/live) via ib_async.

Responsabilità: parlare col conto (saldo, posizioni) e piazzare/chiudere ordini.
Nessuna strategia qui — le decisioni stanno in src/live/decision.py.

Richiede un IB Gateway/TWS acceso e loggato (vedi deploy/SETUP_VPS.md). Gli indici
si tradano come CFD IBKR (simboli 'IBxxx'). ATTENZIONE: il moltiplicatore/point value
del CFD dipende dal contratto del broker — va verificato dal vivo prima di fidarsi
del sizing (per questo il paper trading esiste).
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import Settings

# Strumento nostro -> (simbolo CFD indice IBKR, valuta). Da confermare col Gateway.
IBKR_CFD = {
    "US500":  ("IBUS500", "USD"),
    "NAS100": ("IBUST100", "USD"),
    "US30":   ("IBUS30", "USD"),
    "UK100":  ("IBGB100", "GBP"),
    "DAX":    ("IBDE40", "EUR"),
}


@dataclass
class PositionInfo:
    symbol: str
    qty: float
    avg_cost: float


class IBKRExecution:
    """Wrapper minimale su ib_async per esecuzione. `ib` iniettabile per i test."""

    def __init__(self, settings: Settings, *, ib=None, read_only: bool = False):
        self._settings = settings
        self._ib = ib
        self._read_only = read_only

    # --- connessione ----------------------------------------------------------

    def connect(self):
        if self._ib is None:
            from ib_async import IB
            self._ib = IB()
        if not self._ib.isConnected():
            self._ib.connect(self._settings.host, self._settings.port,
                             clientId=self._settings.client_id, readonly=self._read_only)
        return self._ib

    def disconnect(self):
        if self._ib is not None and self._ib.isConnected():
            self._ib.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.disconnect()

    # --- contratti ------------------------------------------------------------

    def contract(self, instrument: str):
        from ib_async import CFD
        try:
            symbol, ccy = IBKR_CFD[instrument]
        except KeyError:
            raise ValueError(f"Nessun CFD IBKR mappato per '{instrument}'. Note: {list(IBKR_CFD)}.")
        c = CFD(symbol, exchange="SMART", currency=ccy)
        self.connect().qualifyContracts(c)
        return c

    # --- conto ----------------------------------------------------------------

    def net_liquidation(self) -> float:
        """Valore netto del conto (NetLiquidation) nella valuta base."""
        ib = self.connect()
        for v in ib.accountValues():
            if v.tag == "NetLiquidation" and v.currency in ("BASE", ib.wrapper.accounts and ""):
                try:
                    return float(v.value)
                except ValueError:
                    pass
        # fallback: primo NetLiquidation trovato
        for v in ib.accountValues():
            if v.tag == "NetLiquidation":
                try:
                    return float(v.value)
                except ValueError:
                    pass
        return 0.0

    def position(self, instrument: str) -> PositionInfo:
        ib = self.connect()
        symbol, _ = IBKR_CFD.get(instrument, (instrument, ""))
        for p in ib.positions():
            if getattr(p.contract, "symbol", None) == symbol:
                return PositionInfo(symbol, float(p.position), float(p.avgCost))
        return PositionInfo(symbol, 0.0, 0.0)

    # --- ordini ---------------------------------------------------------------

    def buy_with_stop(self, instrument: str, qty: int, stop_price: float):
        """Ordine di acquisto a mercato + stop di protezione collegato."""
        from ib_async import MarketOrder, StopOrder
        if qty <= 0:
            raise ValueError("qty deve essere > 0")
        ib = self.connect()
        c = self.contract(instrument)
        parent = MarketOrder("BUY", qty)
        parent.transmit = False
        pt = ib.placeOrder(c, parent)
        stop = StopOrder("SELL", qty, stop_price)
        stop.parentId = pt.order.orderId
        stop.transmit = True  # trasmette padre+figlio insieme
        st = ib.placeOrder(c, stop)
        return pt, st

    def close(self, instrument: str):
        """Chiude la posizione a mercato e cancella gli ordini pendenti (stop)."""
        from ib_async import MarketOrder
        ib = self.connect()
        pos = self.position(instrument)
        if pos.qty == 0:
            return None
        # cancella eventuali stop pendenti sullo strumento
        symbol, _ = IBKR_CFD.get(instrument, (instrument, ""))
        for o in ib.openOrders():
            if getattr(o.contract, "symbol", None) == symbol:
                ib.cancelOrder(o.order)
        side = "SELL" if pos.qty > 0 else "BUY"
        return ib.placeOrder(self.contract(instrument), MarketOrder(side, abs(pos.qty)))
