---
type: strategy
status: rejected
tags: [breakout, ereditata-kraken]
updated: 2026-06-19
links: []
---
# breakout

## Idea
Rottura del massimo/minimo degli ultimi N (Donchian) + filtro EMA.

## Storia dei test
| Data     | Mercato | Esito          | Fonte           |
|----------|---------|----------------|-----------------|
| (Kraken) | crypto  | forte perdita  | progetto Kraken |

## Verdetto corrente
`rejected` su crypto. Potrebbe comportarsi diversamente sugli indici (mercati più
trending) — se la si vuole riconsiderare su OANDA, si riparte da `untested` con
backtest profondo + walk-forward, senza dare per scontato nulla.
