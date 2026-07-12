---
type: experiment
status: edge-confirmed
tags: [forex, oro, mean-reversion, trend, sweep, daily]
updated: 2026-07-11
links: ["[[fx_meanrev]]", "[[donchian]]"]
raw: ["raw/exp_2026-07-11_fx_meanrev.json"]
---
# Exp 2026-07-11 — sweep strategie su forex major + metalli

## Setup
Sweep uniforme (metriche su serie di rendimenti daily, costi spread inclusi) di 4
strategie canoniche su 7 forex major + oro + argento, ~23 anni. Obiettivo: capire
QUALE stile funziona su QUALE asset. **Fonte:** `raw/exp_2026-07-11_fx_meanrev.json`.

## Sweep — Sharpe portafoglio e mercati positivi
| Strategia | Sharpe portaf. | mercati >0 | metà |
|-----------|----------------|-----------|------|
| tsmom100 (momentum) | +0,19 | 4/9 | +0,33/+0,00 |
| ma50_200 (trend) | +0,17 | 6/9 | +0,26/+0,06 |
| **rsi2_mr (mean-rev)** | −0,01* | **7/9** | −0,07/+0,08 |
| boll_mr (mean-rev) | +0,01 | 6/9 | −0,15/+0,22 |

*Il portafoglio rsi2_mr sembra piatto solo perché **oro/argento** (−0,29/−0,61) lo
trascinano: i **7 FX sono tutti positivi**. Momentum/trend invece è debole (drought) e
tira su solo l'oro.

## Lettura: asset diversi, edge diversi
- **Forex → mean-reversion** (niente drift, oscilla). Vedi [[fx_meanrev]].
- **Oro → trend/momentum** (positivo su tsmom/ma-cross, negativo su MR). Lead separato.

## Validazione fx_meanrev (7 major, RSI2 10/90, exit 50)
- Portafoglio: **Sharpe 0,57**, maxDD −8,9%, metà +0,73/+0,39.
- **Sensibilità: 12/12 combinazioni positive**. **OOS: 0,51 → 0,68** (migliora).

## Conclusione + gate
**`edge-confirmed`** per [[fx_meanrev]] (return-based): secondo edge robusto, market-neutral,
decorrelato dagli indici. Modesto (Sharpe 0,57) ma diversificante. Prossimo: backtest
trade-level + paper. Oro-trend: lead aperto da sviluppare.
