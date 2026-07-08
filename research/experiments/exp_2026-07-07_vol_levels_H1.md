---
type: experiment
status: testing
tags: [indici, volume, h1, swing, breakout, backtest]
updated: 2026-07-07
links: ["[[vol_levels]]", "[[NAS100]]"]
raw: ["raw/exp_2026-07-07_vol_levels_H1.json"]
---
# Exp 2026-07-07 — vol_levels rottura su H1 (4 indici, 6y)

## Setup
[[vol_levels]] variante **rottura**, agganciata al motore (stop/TP/trailing ATR,
costi, futuro walk-forward). H1, 6 anni, spread realistici per indice (DAX 1,5 ·
US500 0,6 · NAS100 2,5 · US30 3,5). **Fonte:** `raw/exp_2026-07-07_vol_levels_H1.json`.

## Risultati (in-sample + due metà)
| Indice | Trade | PF | ret | 1ª metà | 2ª metà |
|--------|-------|-----|-----|---------|---------|
| DAX    | 1306 | 0,999 | −1% | 0,93 | 1,07 |
| US500  | 1541 | 0,988 | −12% | 1,04 | 0,95 |
| NAS100 | 1058 | **1,134** | **+119%** | 1,07 | 1,17 |
| US30   | 1674 | 0,910 | −66% | 0,95 | 0,84 |

## Diagnostico NAS100 (è edge o beta?)
- **Buy&hold NASDAQ 6y: +178%** → la strategia (+119%) **sottoperforma** il tenere.
- Profitto **quasi tutto sui long** (long PF 1,26, +10.935; short PF 1,02, +941 ≈ 0).
- **Senza filtro volume** PF 1,01 (pareggio) → **col filtro** 1,13: il volume aggiunge
  un po'.

## Conclusione
Su H1 i costi **non sono più fatali** (regime giusto, ma non basta). La rottura sui
livelli-volume è **trend-following long-biased**: guadagna dove il mercato sale
(NASDAQ), sottoperforma il buy&hold, non regge sugli altri indici. **Non un edge
robusto/neutrale.** Il filtro volume dà un piccolo contributo reale → vale la pena
provare la variante **rimbalzo** (mean-reversion, market-neutral) e H4 prima di
qualsiasi verdetto. `testing`.
