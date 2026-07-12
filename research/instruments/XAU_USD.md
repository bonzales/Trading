---
type: instrument
status: edge-confirmed
tags: [oro, metalli, trend-following, daily]
updated: 2026-07-12
links: ["[[gold_trend]]", "[[exp_2026-07-12_gold_trend]]"]
---
# XAU/USD (oro)

## Dati
~20 anni daily (Dukascopy, `raw/cache/XAU_USD_D.csv`, ~7400 barre dal 2003).

## Cosa sappiamo
- **Vuole TREND, non mean-reversion.** Nello sweep return-based ([[exp_2026-07-11_fx_meanrev]])
  l'oro è positivo su momentum/ma-cross e **negativo** sul mean-reversion — l'opposto del
  forex. Confermato al trade-level ([[exp_2026-07-12_gold_trend]]).
- **Trend solo-long = edge-confirmed** ([[gold_trend]]): Donchian breakout canale ~40-55,
  PF ~2, Sharpe ~0,65, **maxDD −8%**, sensibilità robusta, OOS che migliora. Gli short
  remano contro il drift rialzista secolare → si tolgono.
- Drift rialzista di fondo (asset monetario: real rates, rifugio, acquisti banche
  centrali). Regimi persistenti → trend puliti (a differenza dell'argento).

## Caution
- **Single-instrument**: l'argento ([[XAG_USD]]) NON conferma il trend → l'edge è
  specifico dell'oro, non generalizzabile ai "metalli preziosi".
- Long-only ⇒ rende a scatti (concentrato nei tori, piatto nei bear come 2011-2015).

## Strategie testate qui
| Strategia | Esito |
|-----------|-------|
| [[gold_trend]] (Donchian solo-long) | **edge-confirmed** (PF ~2, maxDD −8%, OOS migliora) |
| mean-reversion (sweep) | negativo — l'oro non torna alla media |
