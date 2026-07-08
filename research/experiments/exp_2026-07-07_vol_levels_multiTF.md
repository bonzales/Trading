---
type: experiment
status: rejected
tags: [indici, volume, m15, h1, h4, breakout, mean-reversion, walk-forward]
updated: 2026-07-07
links: ["[[vol_levels]]"]
raw: ["raw/exp_2026-07-07_vol_levels_multiTF.json"]
---
# Exp 2026-07-07 — vol_levels: matrice multi-TF + walk-forward

## Setup
[[vol_levels]] in due modalità (**rottura** e **rimbalzo**) × 3 timeframe
(M15, H1, H4) × 4 indici, spread realistici. Poi walk-forward vero sull'unico
angolo positivo (H4 rimbalzo). **Fonte:** `raw/exp_2026-07-07_vol_levels_multiTF.json`.

## Matrice PF (con costi)
| | M15 | H1 | H4 |
|---|---|---|---|
| rimbalzo (DAX/US500/NAS/US30) | .98/.97/1.01/1.00 | .98/.96/1.02/.97 | .95/1.05/1.05/1.11 |
| rottura | .89/.96/1.05/.96 | 1.00/.99/1.13/.91 | 1.00/.90/.94/.88 |

Tutto tra 0,88 e 1,13 → **appiccicato al pareggio**. Su H1/H4 i costi non sono più
fatali (a differenza dello scalping M1), ma non emerge edge. Il rimbalzo
(market-neutral) è **piatto ovunque**: i livelli non hanno potere S/R oltre il rumore.

## Walk-forward (H4 rimbalzo) — la prova decisiva
| Indice | IS PF | OOS PF | overfitting |
|--------|-------|--------|-------------|
| DAX    | 1,41 | 0,96 | ✗ sì |
| US500  | 1,63 | 0,83 | ✗ sì |
| NAS100 | 1,20 | 0,92 | ✗ sì |
| US30   | 1,20 | 1,36 | ✓ regge |

**3/4 overfitting**: i parametri belli in-sample crollano OOS. US30 regge, ma 1/4 è
compatibile col caso — non ci si costruisce sopra (sarebbe "scegli il vincente").

## Conclusione + gate
**`rejected`.** Linea "livelli di volume" esplorata a fondo su ogni fronte. Nessun
edge robusto dopo costi. Lezione utile conservata: **il regime giusto è H1/H4** (i
costi non ammazzano), non lo scalping M1. Prossimo passo: cambiare *famiglia* di
strategia, non ritoccare questa.
