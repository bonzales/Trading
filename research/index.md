# Index — Catalogo della ricerca

> Content-oriented. Catalogo di tutto ciò che c'è nella wiki. L'agente lo aggiorna a
> ogni ingest. Per cercare, parti da qui e poi entra nelle pagine.

## Strategie
| Pagina           | Status         | Sintesi                                       |
|------------------|----------------|-----------------------------------------------|
| [[donchian]]     | rejected       | Trend-following daily. Su paniere ampio (14 mkt, param fisso) è PIATTO. Edge-confirmed iniziale ritrattato. |
| [[pullback]]     | testing        | Kraken: pareggio. EUR_USD H1: no edge (PF 0.951). |
| [[dax_open_volume]] | rejected    | Scalping apertura indici (volume multi-day). Test fedele 4 indici: US500 perde su 356 trade → no edge meccanico dopo costi. |
| [[vol_levels]]      | rejected    | Livelli volume su TF alto. 24 test (rottura+rimbalzo × M15/H1/H4 × 4 indici) + walk-forward: no edge (3/4 overfitting). |
| [[breakout]]     | rejected       | Forte perdita su Kraken (12 mesi reali).      |
| [[meanrev]]      | rejected       | Perdita su Kraken.                             |
| [[ichimoku]]     | rejected       | Forte perdita su Kraken.                       |

## Strumenti
| Pagina       | Status   | Note                                              |
|--------------|----------|---------------------------------------------------|
| [[EUR_USD]]  | testing  | 23,17 anni reali (Dukascopy H1). 1 test: pullback H1 no edge. |
| [[DAX]]      | testing  | 14 anni M1 (Dukascopy). Studio apertura-volume fatto; backtest scalping da fare. |

## Esperimenti
| Pagina       | Data        | Esito                                            |
|--------------|-------------|--------------------------------------------------|
| [[exp_2026-07-06_pullback_EUR_USD_H1]] | 2026-07-06 | `rejected` — PF 0.951 in-sample, nessun edge. |
| [[exp_2026-07-06_dax_open_volume_study]] | 2026-07-06 | studio: effetto apertura DAX confermato (vol >5x nell'81% dei giorni). |
| [[exp_2026-07-06_dax_open_backtest]] | 2026-07-06 | `rejected`: PF 1,045 a 1,5pt spread, break-even a 2,5pt. |
| [[exp_2026-07-06_dax_levels_v3]] | 2026-07-06 | `rejected`: test fedele 4 indici; US500 (356 tr) perde, DAX instabile → no edge meccanico. |
| [[exp_2026-07-07_vol_levels_H1]] | 2026-07-07 | H1: costi non fatali; NAS +119% ma è beta (sottoperforma buy&hold), altri 3 pari/neg. |
| [[exp_2026-07-07_vol_levels_multiTF]] | 2026-07-07 | `rejected`: 24 test multi-TF + walk-forward; tutto ~pareggio, 3/4 overfitting. |
| [[exp_2026-07-07_donchian_daily]] | 2026-07-07 | `rejected` (era edge-confirmed, ritrattato): paniere 14mkt piatto, CAGR ~0%. |

---
**Stato del progetto:** nessun edge confermato al momento. `donchian` sembrava il
primo (walk-forward OK) ma il test onesto su paniere ampio l'ha **ritrattato** (piatto,
CAGR ~0% nel drought 2011-26). La saga scalping-volumi DAX è chiusa (rejected). Lezione
chiave conservata: diffidare di walk-forward con OOS trainato da outlier; validare col
**portafoglio intero a parametro fisso**. Broker dati = Dukascopy; esecuzione = IBKR.
Prossimo: nuova ipotesi (o costruzione TF vol-targeted / periodo più lungo).
