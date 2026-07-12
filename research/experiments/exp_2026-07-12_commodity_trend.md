---
type: experiment
status: edge-confirmed
tags: [commodity, trend-following, paniere, energia, rame, argento, trade-level, regime]
updated: 2026-07-12
links: ["[[commodity_trend]]", "[[gold_trend]]", "[[donchian]]"]
raw: ["raw/exp_2026-07-12_commodity_trend.json"]
---
# Exp 2026-07-12 — paniere commodity-trend (gate completo)

## Perché
Il primo sweep aveva mostrato che le commodity, come l'oro, vogliono **trend long-only**
(Brent 1,90, silver 1,62, copper 1,51, WTI 1,46). Qui il **gate completo** sul paniere di
5 (gas escluso, stagionale). **Fonte:** `raw/exp_2026-07-12_commodity_trend.json`.

## Per mercato (Donchian long-only ch40, rischio 1%)
| Mercato | PF | Sharpe | maxDD | trade/anno |
|---------|-----|--------|-------|-----------|
| Oro | 2,32 | +0,71 | −8% | 4,1 |
| Brent | 1,90 | +0,47 | −8% | 3,0 |
| Argento | 1,62 | +0,42 | −7% | 4,0 |
| Rame | 1,51 | +0,30 | −8% | 3,6 |
| WTI | 1,46 | +0,32 | −7% | 4,0 |

**5/5 positivi**, PF mediano 1,62. **Portafoglio paniere: Sharpe 0,71, maxDD −4%.**

## Il test che impone prudenza: stabilità due-metà = 2/5
| Mercato | PF 1ª / 2ª metà | |
|---------|-----------------|--|
| Oro | 1,83 / 2,91 | ✅ |
| Argento | 1,18 / 1,57 | ✅ |
| WTI | 1,00 / 1,91 | ❌ (1ª piatta) |
| Brent | 0,90 / 3,48 | ❌ (1ª sotto 1) |
| Rame | 0,73 / 2,64 | ❌ (1ª sotto 1) |

Energia e rame hanno la **prima metà debole** (bear commodity 2012-2019) e la seconda
fortissima → l'edge non-oro è **concentrato nel decennio recente**, gonfiato dal
**supertrend inflazionistico 2020-22**. OOS migliora ovunque (train→OOS), ma l'OOS *è*
quel regime. Lezione donchian applicata: non sovrappesare energia/rame su questa base.

## Verdetto
`edge-confirmed` a livello **portafoglio** (5/5, Sharpe 0,71, maxDD −4%, due metà positive
+0,35/+0,95) — **diverso da [[donchian]]** che era piatto (qui long-only + le commodity
tendono davvero). **Nucleo robusto = oro + argento** (entrambe le metà); **energia/rame =
`testing`** standalone (regime-dipendenti). Il fix solo-long **generalizza** il trend oltre
l'oro → la cautela "oro single-instrument" è **superata**. Vedi [[commodity_trend]].
Prossimo: sostituire l'oro_trend grezzo nel sistema multi-edge col paniere trade-level;
testare se il **COT** (posizionamento commercials) filtra bene le commodity.
