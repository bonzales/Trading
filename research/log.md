# Log — Registro cronologico

> Append-only. Ogni riga inizia con `## [YYYY-MM-DD] <tipo> | ...` così è greppabile:
> `grep "^## \[" research/log.md | tail -10`

## [2026-06-19] seed | Importate le conclusioni del progetto Kraken come baseline.
## [2026-06-19] seed | 7 strategie testate su Kraken: nessun edge reale. Pullback = pareggio. Walk-forward best params: in-sample +10€ → OOS −45€ (overfitting).
## [2026-07-06] setup | migrazione broker OANDA→IBKR (solo adapter). Dati di ricerca da Dukascopy (gratis, 23y su EUR_USD H1).
## [2026-07-06] ingest | pullback EUR_USD H1 3y → rejected (PF 0.951, no edge in-sample, no walk-forward)
## [2026-07-06] query  | scalping apertura DAX (utente): studio 388 giorni → effetto volume confermato (>5x nell'81%), stop~28pt vs target 40pt. Strategia dax_open_volume creata (untested).
## [2026-07-06] ingest | dax_open_volume M1 3y → rejected. PF 1,045 a spread 1,5pt ma muore a 2,5pt (break-even). Incostante per anno; candele "oro" non aiutano. Edge probabilmente discrezionale, non meccanizzabile.
## [2026-07-06] ingest | dax_open_volume v2 "rettangolo" (stop stretto, ingresso elastico, come opera l'utente) → ancora rejected, PEGGIORE (PF 0,81→0,67). Stop stretto falciato dal rumore; nessuna uscita runner supera PF 0,90. Verdetto confermato su 2 meccanizzazioni.
## [2026-07-06] ingest | dax_open_volume v3 (livelli volume multi-day + rottura) → verdetto SOSPESO. Senza time-stop aggregato PF 1,11 (regge i costi) ma OOS sbilanciato. SCOPERTO difetto di fedelta': genera ~50 trade/anno (~1/sett) vs ~1/giorno reale dell'utente → cattura 1/5 dei setup. Rifare versione fedele (piu' setup/giorno) + estendere a S&P500/NASDAQ/DowJones (apertura 15:30) = 4 mercati come OOS naturale. Download USA in corso.
