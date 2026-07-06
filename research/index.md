# Index — Catalogo della ricerca

> Content-oriented. Catalogo di tutto ciò che c'è nella wiki. L'agente lo aggiorna a
> ogni ingest. Per cercare, parti da qui e poi entra nelle pagine.

## Strategie
| Pagina           | Status         | Sintesi                                       |
|------------------|----------------|-----------------------------------------------|
| [[pullback]]     | testing        | Kraken: pareggio. EUR_USD H1: no edge (PF 0.951). |
| [[breakout]]     | rejected       | Forte perdita su Kraken (12 mesi reali).      |
| [[meanrev]]      | rejected       | Perdita su Kraken.                             |
| [[ichimoku]]     | rejected       | Forte perdita su Kraken.                       |

## Strumenti
| Pagina       | Status   | Note                                              |
|--------------|----------|---------------------------------------------------|
| [[EUR_USD]]  | testing  | 23,17 anni reali (Dukascopy H1). 1 test: pullback H1 no edge. |

## Esperimenti
| Pagina       | Data        | Esito                                            |
|--------------|-------------|--------------------------------------------------|
| [[exp_2026-07-06_pullback_EUR_USD_H1]] | 2026-07-06 | `rejected` — PF 0.951 in-sample, nessun edge. |

---
**Stato del progetto:** primo backtest reale eseguito su dati Dukascopy (EUR_USD H1,
3y): pullback senza edge in-sample → scartata su questa combinazione. Broker dati
di ricerca = Dukascopy; broker esecuzione (paper/live) = IBKR (Gateway da attivare).
Prossimi passi: pullback su H4 e su un indice.
