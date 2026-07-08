---
type: strategy
status: rejected
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
`rejected` su questo paniere/periodo. **CORREZIONE di un "edge-confirmed" emesso
troppo in fretta** (2026-07-07): l'entusiasmo iniziale si reggeva su un sottoinsieme
favorevole (8 mercati) e su un walk-forward la cui media OOS (1,83) era **gonfiata da
2 outlier** (oro 6,07, JPY 2,43) e dall'ottimizzazione del canale per-mercato.

Test più onesto — **paniere ampliato a 14 mercati, parametro fisso, equal-weight,
curva equity intera** (fonte aggiornata `raw/exp_2026-07-07_donchian_daily.json`):
- **portafoglio PIATTO**: CAGR −0,2%…+0,1%, Sharpe ~0, su TUTTI i canali (20/55/100/150).
- ~metà mercati positivi (oro, indici USA, CAD, JPY), ~metà negativi (UK100 −32%, NZD
  −24%, CHF −18%, GBP, DAX): i perdenti pareggiano i vincenti. Netto ≈ zero.

Contesto (non una scusa): il 2011–2026 è un **drought documentato per il trend-following**
(CTA in sofferenza). Non prova che il TF sia morto in assoluto, ma **su questi dati non
c'è edge**. Riaprire solo con costruzione diversa (vol-targeting, più mercati, storia
pre-2011) e sempre validato OOS — non selezionando i mercati vincenti col senno di poi.

## Lezione METODOLOGICA (importante)
Un walk-forward con media OOS alta ma **trainata da 1-2 outlier** non è un edge. La
prova pulita è il **portafoglio intero a parametro fisso**. Applicare la stessa severità
ai risultati che si spera siano veri.

## Note
Trend-following = pochi trade (~8/anno/mercato), win rate ~40%, guadagno dai pochi
trend lunghi. Il walk-forward su singolo mercato è rumoroso per la bassa frequenza:
l'evidenza forte è la **combinazione** paniere + due metà + walk-forward, non il
singolo numero.
