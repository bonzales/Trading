# Index — Catalogo della ricerca

> Content-oriented. Catalogo di tutto ciò che c'è nella wiki. L'agente lo aggiorna a
> ogni ingest. Per cercare, parti da qui e poi entra nelle pagine.

## Strategie
| Pagina           | Status         | Sintesi                                       |
|------------------|----------------|-----------------------------------------------|
| [[rsi2_meanrev]] | paper          | Compra-il-ribasso RSI2 sugli indici. IN PAPER dal 2026-07-11 (VPS, timer giornaliero, Telegram). |
| [[fx_meanrev]]   | testing        | Mean-reversion RSI2 sui 7 forex major. Return-based sembrava 2° edge, ma il **trade-level lo declassa**: marginale, cost-fragile (muore a 2× frizioni). Vale solo come sleeve diversificante. |
| [[donchian]]     | rejected       | Trend-following daily. Su paniere ampio (14 mkt, param fisso) è PIATTO. Edge-confirmed iniziale ritrattato. |
| [[pullback]]     | testing        | Kraken: pareggio. EUR_USD H1: no edge (PF 0.951). |
| [[dax_open_volume]] | rejected    | Scalping apertura indici (volume multi-day). Test fedele 4 indici: US500 perde su 356 trade → no edge meccanico dopo costi. |
| [[vol_levels]]      | rejected    | Livelli volume su TF alto. 24 test (rottura+rimbalzo × M15/H1/H4 × 4 indici) + walk-forward: no edge (3/4 overfitting). |
| [[breakout]]     | rejected       | Forte perdita su Kraken (12 mesi reali).      |
| [[meanrev]]      | rejected       | Perdita su Kraken.                             |
| [[ichimoku]]     | rejected       | Kraken: perdita. Daily 14 mkt: trend-following, 5/14 pos, PF mediano 0,94. |

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
| [[exp_2026-07-08_rsi2_meanrev]] | 2026-07-08 | **edge-confirmed**: compra-il-ribasso indici; 5/5, 27/27 param, OOS migliora. |
| [[exp_2026-07-08_ichimoku_daily]] | 2026-07-08 | `rejected`: trend-following travestito, 5/14 pos, PF mediano 0,94 (come donchian). |
| [[exp_2026-07-11_fx_meanrev]] | 2026-07-11 | **edge-confirmed**: mean-reversion 7 forex major; 7/7, 12/12 param, OOS migliora. Oro→trend (lead). |
| [[exp_2026-07-12_riskparity]] | 2026-07-12 | **risk-parity** sul multi-edge: Sharpe 0,55→0,74 e maxDD −12%→−8% insieme; robusto su finestre 40-180g. Pesatura di default. |
| [[exp_2026-07-12_fx_meanrev_tradelevel]] | 2026-07-12 | **trade-level fx_meanrev**: DECLASSA a `testing`. 6/7 ma marginale (PF med 1,07), Sharpe 0,31 (vs 0,57), muore a 2× costi, swap non modellato. Non standalone. |

---
**Stato del progetto:** **UN edge robusto e confermato**: [[rsi2_meanrev]] (indici, IN
PAPER sul VPS) — mean-reversion che passa tutti i test (5/5 positivi, param-insensibile,
OOS che migliora, maxDD −8%). [[fx_meanrev]] (forex) sembrava il secondo edge ma il
**backtest trade-level (2026-07-12) l'ha declassato a `testing`**: marginale e
cost-fragile (muore a 2× frizioni, swap non modellato) → vale **solo come sleeve
diversificante** nel sistema multi-edge, non standalone. Lead aperto: oro→trend-following.
Sistema multi-edge con **risk-parity** (Sharpe combinato 0,74). Rigettati con rigore:
scalping-volumi DAX ([[dax_open_volume]], [[vol_levels]]) e trend-following daily
([[donchian]], piatto nel drought 2011-26). Lezione chiave: validare col **portafoglio
intero a parametro fisso** + sensibilità + **trade-level con costi realistici** (è quello
che ha smascherato fx_meanrev). Broker dati = Dukascopy; esecuzione = IBKR. **Prossimo
passo: sviluppare l'oro-trend a livello trade** (3° sleeve candidato).
