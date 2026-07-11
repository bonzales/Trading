---
type: experiment
status: rejected
tags: [ichimoku, trend-following, indici, forex, daily, backtest]
updated: 2026-07-08
links: ["[[ichimoku]]", "[[donchian]]"]
raw: ["raw/exp_2026-07-08_ichimoku_daily.json"]
---
# Exp 2026-07-08 — Ichimoku regole canoniche (daily, 14 mercati)

## Setup
[[ichimoku]] con settaggi classici (Tenkan 9, Kijun 26, Senkou B 52, shift 26).
Ingresso a tre conferme (nuvola + incrocio TK + Chikou), uscita stop/trailing ATR
(come [[donchian]], per confronto equo). 14 mercati daily ~15y, spread per mercato.
**Fonte:** `raw/exp_2026-07-08_ichimoku_daily.json`.

## Risultati
- **5/14 positivi, PF mediano 0,94.** Due metà instabili (6/14 e 5/14 positivi).
- Vincitori: XAU 1,41 · NAS100 1,19 · US500 1,11 · JPY 1,10 (i soliti trenders).
- Perdenti: UK100 0,62 · DAX 0,72 · quasi tutto il forex 0,92-0,94.

## Conclusione + gate
**`rejected`.** Ichimoku è trend-following: **identica firma di donchian** su questi
dati (guadagna solo dove il mercato trenda, perde sul resto). Non aggiunge nulla al TF
già rigettato. L'articolo che l'ha ispirata (investire.biz) è divulgativo e promuove un
corso — non dà regole operative; il "funziona molto bene" era un'affermazione, smentita
dal backtest. L'edge del progetto resta il mean-reversion ([[rsi2_meanrev]]).
