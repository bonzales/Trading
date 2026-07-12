---
type: experiment
status: testing
tags: [forex, mean-reversion, trade-level, costi, daily, contraddice]
updated: 2026-07-12
links: ["[[fx_meanrev]]", "[[exp_2026-07-11_fx_meanrev]]", "[[rsi2_meanrev]]"]
raw: ["raw/exp_2026-07-12_fx_meanrev_tradelevel.json"]
---
# Exp 2026-07-12 — fx_meanrev TRADE-LEVEL (il gate mancante)

## Perché questo esperimento
[[exp_2026-07-11_fx_meanrev]] aveva promosso fx_meanrev a `edge-confirmed` ma **solo
return-based** (posizione ±1, nessuno stop, nessun sizing, solo spread). Questo è il
**gate trade-by-trade** che mancava: stop ATR, sizing sul rischio, costi realistici.
Codice nuovo: `src/backtest/fx_meanrev.py` (simmetrico long/short). **Fonte:**
`raw/exp_2026-07-12_fx_meanrev_tradelevel.json`.

## Risultato per mercato (canonico RSI2 10/90, exit 50, stop 3ATR, risk 1%)
| Mercato | PF | win | exp_R | n | maxDD |
|---------|-----|-----|-------|-----|-------|
| EUR_USD | 1,17 | 65% | +0,023 | 873 | −6% |
| USD_CHF | 1,17 | 67% | +0,023 | 881 | −7% |
| USD_JPY | 1,07 | 65% | +0,011 | 857 | −11% |
| USD_CAD | 1,07 | 66% | +0,010 | 856 | −8% |
| NZD_USD | 1,05 | 64% | +0,007 | 700 | −8% |
| GBP_USD | 1,01 | 65% | +0,001 | 888 | −12% |
| AUD_USD | 1,00 | 65% | −0,001 | 839 | −11% |

**6/7 positivi**, PF mediano **1,07**. Ma diversi sono **appena sopra 1,0** e l'expectancy
per trade è **minuscola** (+0,001…+0,023R).

## I test di robustezza: misti
- **Stabilità due metà: 5/7** (falliscono USD_JPY 2ª metà 0,97 e AUD_USD 1ª metà 0,97).
- **Sensibilità parametri: 27/27 combinazioni** con PF mediano >1 (peggiore 1,02) → **robusto ai parametri** (non è un valore fortunato).
- **OOS temporale: train 1,04 → OOS 1,07** → regge fuori campione.
- **Portafoglio**: CAGR +2,5%, **maxDD −27%**, Sharpe(daily) **0,31**. Le due metà:
  **0,46 / 0,17** → la seconda metà è **molto più debole**: edge in decadimento.

## Il test che lo affossa: fragilità ai costi
Hold medio **3,4 giorni** → sulle posizioni multi-day il **swap/rollover forex conta e
NON è modellato**. Testando frizioni crescenti (proxy di spread reale + slippage + swap):

| Frizioni | PF mediano | mercati >1 | exp_R mediano |
|----------|-----------|-----------|---------------|
| 1,0× (base) | 1,07 | 6/7 | +0,0098 |
| 1,5× | 1,04 | 5/7 | +0,0061 |
| 2,0× | **1,01** | 4/7 | +0,0021 |
| 3,0× | 0,97 | 3/7 | −0,0047 |

**A 2× le frizioni l'edge svanisce.** E 2× è del tutto plausibile per forex retail tenuto
3-4 giorni (spread + slippage + swap che qui manca).

## Verdetto — il gate DECLASSA fx_meanrev
Contraddice la lettura ottimistica di [[exp_2026-07-11_fx_meanrev]] (Sharpe 0,57 return-based
→ **0,31** trade-level). Edge **reale ma marginale e cost-fragile**: sopravvive ai
parametri e all'OOS, ma è razor-thin, muore a 2× costi, con swap non modellato e 2ª metà
debole. **Confronto con [[rsi2_meanrev]]** (PF 1,08–2,57, maxDD −8%): fx_meanrev è
**nettamente più debole**.

**Conseguenza operativa:** NON tradeable standalone. Resta utile **solo come sleeve
diversificante** (decorrelato dagli indici) nel sistema multi-edge, con sizing
conservativo. **NON va promosso a paper standalone** — la scelta di non spingerlo sul VPS
per lunedì è confermata dai dati, non era prudenza generica.
