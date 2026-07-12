---
type: experiment
status: edge-confirmed
tags: [multi-edge, risk-parity, portfolio, allocazione, daily]
updated: 2026-07-12
links: ["[[rsi2_meanrev]]", "[[fx_meanrev]]", "[[exp_2026-07-11_fx_meanrev]]"]
raw: ["raw/exp_2026-07-12_riskparity.json"]
---
# Exp 2026-07-12 — risk-parity sul sistema multi-edge

## Setup
Sostituita la pesatura **equal-weight** con **risk-parity (inverse-vol)** sui 3 sleeve
decorrelati (idx_MR, fx_MR, oro_trend). Validazione return-based (posizione ±1, costi
spread). Le correlazioni tra sleeve sono ~0 → l'inverse-vol coincide di fatto con
l'equal-risk-contribution. Versione **senza look-ahead**: pesi calcolati sulla vol
realizzata a 60 giorni e applicati il giorno dopo. **Fonte:** `raw/exp_2026-07-12_riskparity.json`.

## Sleeve singoli (senza leva)
| Sleeve | Sharpe | CAGR | maxDD | vol/anno |
|--------|--------|------|-------|----------|
| idx_MR | +0,48 | +1,9% | −13% | 4,0% |
| fx_MR | +0,33 | +0,9% | −9% | 2,9% |
| oro_trend | +0,40 | +4,9% | −35% | **15,0%** |

## Confronto pesature (senza leva)
| Pesatura | Sharpe | CAGR | maxDD |
|----------|--------|------|-------|
| equal-weight (baseline) | +0,55 | +2,8% | −12% |
| **risk-parity dinamica (60g, no-LA)** | **+0,74** | +1,9% | **−8%** |
| risk-parity statica (rif., look-ahead) | +0,67 | +1,8% | −7% |

**Pesi risk-parity** (medi): idx_MR 46%, fx_MR 44%, oro_trend **9%**.

## Perché funziona (meccanismo, non magia)
L'equal-weight **sovra-allocava rischio all'oro** (vol 15%/anno, DD −35%): un terzo del
capitale su uno sleeve 4-5× più volatile degli altri. La risk-parity taglia l'oro a ~9%
e carica i due mean-reversion a bassa vol. Risultato: **più Sharpe E meno drawdown**
(−12% → −8%) contemporaneamente. Non sto inseguendo il rendimento, sto bilanciando il
rischio.

## Test anti-overfitting
- **La finestra vol NON è un parametro fortunato**: 40g→0,72 · 60g→0,74 · 90g→0,66 ·
  120g→0,63 · 180g→0,65. **Tutte** sopra l'equal-weight 0,55 → miglioramento strutturale.
- **La versione no-look-ahead (0,74) batte quella statica full-sample (0,67)** → non sta
  barando col futuro; l'adattività aiuta.
- **OOS temporale**: 1ª metà Sharpe +0,38, 2ª metà +1,04. Entrambe positive (la 2ª più
  forte — da non sopravvalutare: è comunque return-based).

## A parità di rischio (vol-target 15%/anno)
| Pesatura | leva | CAGR | maxDD |
|----------|------|------|-------|
| equal-weight | ~2,8× | +7,4% | −32% |
| risk-parity dinamica | ~5,9× | +10,5% | **−41%** |

A parità di target di volatilità la risk-parity rende di più — è lo Sharpe migliore che
si monetizza. **Ma −41% di DD è inaccettabile su capitale vero**: il punto operativo
realistico è un vol-target più basso (8-10%), non questo.

## Conclusione + gate
Risk-parity dinamica **adottata come pesatura di default** del sistema multi-edge:
Sharpe **0,55 → 0,74** (robusto), drawdown ridotto. **NON promuove a live.** Il sistema
resta:
- **modesto** (0,74 = buon portafoglio diversificato, non una macchina da soldi);
- **return-based** (posizione ±1, nessuna esecuzione realistica oltre lo spread);
- dipendente da un **oro_trend ancora solo return-based** → il suo peso (9%) è "soft"
  finché non c'è un backtest trade-level. **È il prossimo passo.**
