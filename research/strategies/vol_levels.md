---
type: strategy
status: testing
tags: [indici, volume, h1, swing, breakout, mean-reversion]
updated: 2026-07-07
links: ["[[dax_open_volume]]", "[[exp_2026-07-07_vol_levels_H1]]", "[[NAS100]]"]
---
# vol_levels (livelli di volume su timeframe alto)

## Idea
Erede di [[dax_open_volume]] portata su **H1/H4**: una barra a volume anomalo lascia
un livello S/R che il prezzo "ricorda" per giorni. Su timeframe alto i movimenti sono
di centinaia di punti → lo spread (1–3 pt) pesa <1%, non ammazza più la strategia come
nello scalping M1. Si aggancia al motore (`VolumeLevelStrategy` in `src/core/strategy.py`),
quindi eredita gestione rischio (stop/TP/trailing ATR), costi e **walk-forward**.

## Varianti
- **Rottura (breakout):** long se il prezzo supera un livello al rialzo, short al
  ribasso. **Testata** (vedi sotto).
- **Rimbalzo (mean-reversion):** entrare quando il prezzo TORNA sul livello e lo
  rispetta. **Da testare** — sarebbe market-neutral, non trend-following.

## Storia dei test
| Data       | Variante | Mercati | Esito | Fonte |
|------------|----------|---------|-------|-------|
| 2026-07-07 | rottura H1 | DAX/US500/NAS/US30 (6y) | trend-following long-biased, non edge neutrale | [[exp_2026-07-07_vol_levels_H1]] |

## Verdetto corrente
`testing`. Su H1 il **regime dei costi è giusto** (quasi tutto vicino al pareggio, non
più perdite nette come su M1). Ma la **rottura** è trend-following: NAS100 +119% solo
perché il NASDAQ è salito (sottoperforma il buy&hold +178%; profitto quasi tutto sui
long); altri 3 indici pari/negativi. **Non un edge robusto.** Il filtro volume aggiunge
un po' (PF 1,13 vs 1,01 senza) → indizio che qualcosa c'è. Prossimo: provare il
**rimbalzo** (market-neutral) e H4.

## Note
Attenzione al bias di beta: su un mercato molto trendante un breakout long guadagna a
prescindere. Il test onesto di un edge sui livelli è che regga anche short e su mercati
non trendanti, e che batta il buy&hold a parità di rischio.
