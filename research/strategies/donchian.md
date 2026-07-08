---
type: strategy
status: edge-confirmed
tags: [trend-following, daily, breakout, multi-mercato, donchian]
updated: 2026-07-07
links: ["[[exp_2026-07-07_donchian_daily]]", "[[XAU_USD]]", "[[USD_JPY]]"]
---
# donchian (trend-following diversificato, daily)

## Idea
Trend-following classico stile Turtle: **long** quando il prezzo chiude sopra il
massimo degli ultimi `channel` giorni, **short** sotto il minimo. Niente target:
stop e trailing ATR fanno **correre i trend**. È lo stile con più evidenza storica
di un edge reale (modesto), e vive di **diversificazione** su molti mercati.
Codice: `DonchianStrategy` in `src/core/strategy.py`, agganciata al motore.

## Assetto
Daily. Rischio 1%/trade. Stop 2,5×ATR; a +1R → breakeven + trailing 3×ATR (nessun
target che tagli i runner). Paniere: indici (DAX, US500, NAS100, US30), forex majors
(EUR_USD, GBP_USD, USD_JPY), oro (XAU_USD). Costi: spread realistico per mercato.

## Storia dei test
| Data       | Cosa | Esito | Fonte |
|------------|------|-------|-------|
| 2026-07-07 | in-sample canonico (ch 20/55) + due metà | portafoglio PF 1,07–1,21, 6/8 pos, stabile | [[exp_2026-07-07_donchian_daily]] |
| 2026-07-07 | **walk-forward** (ottimizza ch su train, valida OOS) | **regge: 5/8 OOS>1**, OOS medio 1,83 | [[exp_2026-07-07_donchian_daily]] |

## Verdetto corrente
`edge-confirmed` **a livello di paniere diversificato.** È la prima strategia del
progetto a superare il walk-forward senza crollare (i livelli di volume erano 3/4
overfitting; qui 5/8 reggono OOS, e i trenders forti — indici USA, yen, oro — tengono).

**Cautele (load-bearing):**
- Edge **modesto**: le medie OOS sono gonfiate da oro (6,07) e JPY (outlier di trend
  eccezionali 2022–24). Attesa realistica di portafoglio ~**1,1–1,2** di PF, con
  drawdown veri (−10/15%). Non è un bancomat.
- **Non tutti i mercati funzionano**: DAX, GBP, EUR sono deboli/negativi. È normale nel
  trend-following: si tiene il paniere, non il singolo. Valutare se escludere i
  perdenti cronici o tenerli per diversificazione (rischio di curve-fitting nella scelta).
- Va tradato **diversificato**, mai un mercato solo.

## Prossimo passo (gate §5)
**Paper trading su demo** (settimane, non ore) prima di qualsiasi live. È il motivo
per cui ora serve davvero attivare l'IB Gateway (finora rimandato): qui c'è un
candidato che merita il paper.

## Note
Trend-following = pochi trade (~8/anno/mercato), win rate ~40%, guadagno dai pochi
trend lunghi. Il walk-forward su singolo mercato è rumoroso per la bassa frequenza:
l'evidenza forte è la **combinazione** paniere + due metà + walk-forward, non il
singolo numero.
