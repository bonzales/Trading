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
## [2026-07-06] ingest | dax_open_volume TEST FEDELE (multi-trade ~1/gg, 4 indici, param normalizzati alla volatilita, OOS) → REJECTED. US500 356 trade PERDE entrambe le meta (PF 0,92): il pattern DAX 2025-26 non si replica su mercato indipendente = fortuna campione. DAX aggregato 1,17 ma 1a meta 0,94. NAS/Dow setup non scatta (4-5 trade). Chiuso: edge discrezionale, non meccanico. Domanda utente "replica i vincenti" = overfitting (risposta data coi dati US500).
## [2026-07-07] ingest | vol_levels ROTTURA su H1 (idea volumi su TF alto, 4 indici 6y). Costi non piu' fatali (regime giusto). Ma e' trend-following long-biased: NAS +119% (sottoperforma buy&hold +178%, profitto tutto sui long), altri 3 pari/neg. Filtro volume aggiunge poco (1,13 vs 1,01). Non edge robusto. Prossimo: variante RIMBALZO (market-neutral) + H4.
