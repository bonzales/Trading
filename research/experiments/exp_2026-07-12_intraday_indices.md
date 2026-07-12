---
type: experiment
status: rejected
tags: [intraday, indici, H1, mean-reversion, breakout, costi, no-edge]
updated: 2026-07-12
links: ["[[rsi2_meanrev]]", "[[dax_open_volume]]", "[[vol_levels]]"]
raw: ["raw/exp_2026-07-12_intraday_indices.json"]
---
# Exp 2026-07-12 — intraday indici H1: cerco edge ad alto turnover

## Perché
Il muro di ogni strategia daily è: pochi trade → pochi euro su capitale piccolo. Ipotesi:
**alzare la dose col turnover** — molti trade intraday. Test rigoroso sui 4 indici in H1
(6 anni), due ipotesi opposte + griglia parametri + costi. **Fonte:**
`raw/exp_2026-07-12_intraday_indices.json`.

## Ipotesi A — mean-reversion RSI2 (il nostro edge daily, portato in H1)
| | US500 | NAS100 | US30 | DAX | mediano |
|-|-------|--------|------|-----|---------|
| PF | 0,99 | 1,08 | 0,88 | 0,88 | **0,94** |

- **1/4** positivo, ~161 trade/anno, **0/4** stabile nelle due metà.
- **Sensibilità: 0/27 combinazioni** (ma_long × oversold × max_hold) con PF mediano >1;
  il massimo è **0,98**. → l'edge **non c'è**, non è un problema di taratura.
- **Costi**: ×1 → 0,94, ×2 → 0,83, ×3 → 0,74. Muore subito.

## Ipotesi B — breakout Donchian (e se intraday gli indici *tendono*?)
PF mediano **0,99**, 2/4, con **disastri** (US500 PF 0,84 / maxDD **−72%**). Nessun edge;
intraday gli indici non tendono in modo tradabile.

## Verdetto — linea CHIUSA
**Nessun edge intraday sugli indici in H1**, né mean-reversion né breakout. Il turnover
c'è (~160-200 trade/anno) ma senza edge **moltiplica solo i costi**. Stesso muro dello
scalping DAX ([[dax_open_volume]]) e dei [[vol_levels]].

**Ragione strutturale:** intraday il movimento degli indici è dominato da rumore + costi;
l'edge mean-reversion vive sull'orizzonte **daily/overnight**, non intraday. TF più corti
(M15/M1) hanno un rapporto costo/movimento peggiore → ancora meno probabili.

**Implicazione:** l'intraday retail su CFD è un cimitero per i costi. Conferma che la leva
per "più euro" non è il turnover intraday, ma il **capitale nel tempo** + dose via **leva
controllata sugli edge daily confermati** ([[rsi2_meanrev]], [[gold_trend]]).
