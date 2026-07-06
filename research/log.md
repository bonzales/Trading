# Log — Registro cronologico

> Append-only. Ogni riga inizia con `## [YYYY-MM-DD] <tipo> | ...` così è greppabile:
> `grep "^## \[" research/log.md | tail -10`

## [2026-06-19] seed | Importate le conclusioni del progetto Kraken come baseline.
## [2026-06-19] seed | 7 strategie testate su Kraken: nessun edge reale. Pullback = pareggio. Walk-forward best params: in-sample +10€ → OOS −45€ (overfitting).
## [2026-07-06] setup | migrazione broker OANDA→IBKR (solo adapter). Dati di ricerca da Dukascopy (gratis, 23y su EUR_USD H1).
## [2026-07-06] ingest | pullback EUR_USD H1 3y → rejected (PF 0.951, no edge in-sample, no walk-forward)
