---
type: strategy
status: rejected
tags: [indici, volume, h1, swing, breakout, mean-reversion]
updated: 2026-07-07
links: ["[[dax_open_volume]]", "[[exp_2026-07-07_vol_levels_H1]]", "[[exp_2026-07-07_vol_levels_multiTF]]", "[[NAS100]]"]
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
`rejected` come edge meccanico, dopo esplorazione **esaustiva** (fonte:
`raw/exp_2026-07-07_vol_levels_multiTF.json`):
- **24 test** (rottura + rimbalzo × M15/H1/H4 × 4 indici): tutti appiccicati al
  pareggio (PF 0,88–1,13).
- Su H1/H4 i **costi non sono più fatali** (regime giusto) — ma non emerge edge.
- Il **breakout** positivo (NAS H1 1,13) è **beta** (long in uptrend, sottoperforma
  il buy&hold). Il **rimbalzo** (market-neutral) è **piatto ovunque** → i livelli di
  volume non hanno potere S/R predittivo oltre il rumore.
- **Walk-forward vero** (H4 rimbalzo, ottimizza su train / valida OOS): **3/4
  overfitting** (IS buono → OOS <1). Solo US30 regge (1/4 = caso).

Conclusione: la linea "livelli di volume" è stata esplorata a fondo (scalping M1 →
M15/H1/H4, rottura + rimbalzo, 4 mercati, walk-forward). **Nessun edge robusto.**
Chiusa. Riaprire solo con un meccanismo nuovo e diverso, non con altri ritocchi.

## Note
Attenzione al bias di beta: su un mercato molto trendante un breakout long guadagna a
prescindere. Il test onesto di un edge sui livelli è che regga anche short e su mercati
non trendanti, e che batta il buy&hold a parità di rischio.
