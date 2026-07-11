---
type: experiment
status: edge-confirmed
tags: [mean-reversion, indici, daily, rsi2, walk-forward]
updated: 2026-07-08
links: ["[[rsi2_meanrev]]"]
raw: ["raw/exp_2026-07-08_rsi2_meanrev.json"]
---
# Exp 2026-07-08 — RSI2 mean-reversion sugli indici (daily)

## Setup
[[rsi2_meanrev]] su 5 indici (DAX, US500, NAS100, US30, UK100), daily ~14y, parametri
canonici (RSI2<10, filtro SMA200, esci RSI>50 / SMA5 / max_hold, stop 3×ATR, long-only).
Costi: spread per indice. **Fonte:** `raw/exp_2026-07-08_rsi2_meanrev.json`.

## Risultati per mercato (in-sample + due metà)
| Indice | Trade | PF | win | metà |
|--------|-------|-----|-----|------|
| US500  | 160 | 2,57 | 80% | 2,59/2,55 |
| NAS100 | 158 | 1,78 | 72% | 1,72/2,36 |
| US30   | 161 | 1,62 | 74% | 1,99/1,57 |
| DAX    | 139 | 1,19 | 70% | 1,17/1,18 |
| UK100  | 123 | 1,08 | 67% | 1,00/1,28 |

Tutti positivi, win rate alto (firma MR), metà stabili.

## Portafoglio 5 indici
+50% in 14y · **CAGR +3,0% · maxDD −8,3%** · 10/15 anni positivi. Crash contenuti
(2020 −2%, 2022 −1%): il filtro SMA200 tiene fuori dai ribassi.

## Validazione anti-overfitting
- **Sensibilità parametri: 27/27 combinazioni positive** (oversold 5/10/15 × exit
  50/60/70 × ma 100/150/200), PF 1,38–1,65. Non un parametro fortunato.
- **OOS temporale**: train (primi 60%) PF 1,43 → OOS (ultimi 40%) **1,77**.

## Conclusione + gate
**`edge-confirmed`.** Passa tutti i test che [[donchian]] aveva fallito. Primo edge
robusto del progetto. Cautele: modesto, pubblicato (affollamento), tail-risk residuo.
**Prossimo: paper trading su demo** (serve IB Gateway).
