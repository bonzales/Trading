---
type: strategy
status: rejected
tags: [ichimoku, trend-following, indici, forex, ereditata-kraken]
updated: 2026-07-08
links: ["[[donchian]]", "[[exp_2026-07-08_ichimoku_daily]]"]
---
# ichimoku

## Idea
Ichimoku Kinko Hyo (Hosoda, ~1930). 5 linee: Tenkan (9), Kijun (26), Senkou A/B
(nuvola proiettata +26, SSB su 52), Chikou (close −26). Ingresso canonico "a tre
conferme": prezzo dal lato giusto della nuvola + incrocio Tenkan/Kijun + conferma
Chikou. È **trend-following** nella sostanza. Codice: `IchimokuStrategy` in
`src/core/strategy.py`.

## Storia dei test
| Data       | Mercato | Esito | Fonte |
|------------|---------|-------|-------|
| (Kraken)   | crypto  | forte perdita | progetto Kraken |
| 2026-07-08 | 14 mercati daily (indici+forex+metalli) | no edge: 5/14 positivi, PF mediano 0,94 | [[exp_2026-07-08_ichimoku_daily]] |

## Verdetto corrente
`rejected`. Regole canoniche testate sul paniere daily: **5/14 positivi, PF mediano
0,94**, due metà instabili. È la **stessa firma di [[donchian]]** (trend-following):
guadagna solo dove il mercato trenda forte (oro 1,41, NASDAQ 1,19, yen), perde sul
resto (DAX 0,72, UK100 0,62, quasi tutto il forex 0,92-0,94). Non aggiunge nulla al
trend-following già rigettato.

Origine della richiesta: un articolo divulgativo (investire.biz) che presenta le linee
ma **non dà regole operative** — è la promozione di un corso a pagamento. Il "funziona
molto bene" era un'affermazione, smentita dal backtest. Su questi dati l'edge resta il
mean-reversion ([[rsi2_meanrev]]), non i sistemi trend-following.

## Nota
Non testate le uscite Ichimoku-native (incrocio TK inverso, rientro nella nuvola): qui
usiamo stop/trailing ATR come per donchian, per confronto equo. Improbabile che uscite
diverse ribaltino un ingresso trend-following già strutturalmente debole su questi dati.
