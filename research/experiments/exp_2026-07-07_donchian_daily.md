---
type: experiment
status: edge-confirmed
tags: [trend-following, daily, breakout, walk-forward, multi-mercato]
updated: 2026-07-07
links: ["[[donchian]]"]
raw: ["raw/exp_2026-07-07_donchian_daily.json"]
---
# Exp 2026-07-07 — Donchian trend-following daily (paniere 8 mercati)

## Setup
[[donchian]] su DAILY, ~15 anni, 8 mercati (indici + forex + oro). Rischio 1%/trade,
stop 2,5×ATR, breakeven+trailing 3×ATR dopo +1R, niente target. Spread realistico
per mercato. **Fonte:** `raw/exp_2026-07-07_donchian_daily.json`.

## In-sample con parametri canonici (NON ottimizzati → niente overfitting)
- **channel 20:** 6/8 profittevoli, PF medio 1,077, **portafoglio PF 1,072** (1024
  trade); 5/8 positivi in 1ª metà, 5/8 in 2ª metà.
- **channel 55:** 5/8 profittevoli, PF medio 1,266, **portafoglio PF 1,207** (651
  trade). Anche il canale peggiore dà portafoglio positivo → non sensibile alla taratura.

## Walk-forward (ottimizza channel ∈ {10,20,55,100} su train, valida OOS)
| Mercato | IS | OOS | overfit |
|---------|-----|-----|---------|
| XAU_USD | 2,33 | 6,07 | no (outlier) |
| USD_JPY | 2,54 | 2,43 | no |
| US30    | 2,30 | 1,44 | no |
| US500   | 3,01 | 1,24 | no |
| NAS100  | 2,31 | 1,15 | no |
| GBP_USD | 0,98 | 0,95 | no (perde in entrambi) |
| EUR_USD | 1,03 | 0,84 | sì |
| DAX     | 1,07 | 0,55 | sì |

**5/8 mercati OOS>1**, OOS medio 1,83. I trenders forti reggono; non crolla come i
livelli di volume (che erano 3/4 overfitting).

## Conclusione + gate
**`edge-confirmed`** a livello di paniere. Primo edge del progetto a superare il
walk-forward. Cautele: modesto (medie OOS gonfiate da oro/JPY), alcuni mercati
falliscono (DAX/GBP/EUR), va tradato diversificato. **Prossimo: paper trading su
demo** prima del live (serve attivare l'IB Gateway).
