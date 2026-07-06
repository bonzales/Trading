---
type: experiment
status: testing
tags: [indici, dax, scalping, m1, volume, studio]
updated: 2026-07-06
links: ["[[dax_open_volume]]", "[[DAX]]"]
---
# Exp 2026-07-06 — studio esplorativo apertura DAX (volume)

## Setup
Studio PRE-backtest (non una strategia eseguita): misura se l'effetto apertura su
cui si basa [[dax_open_volume]] esiste davvero nei dati e con che numeri, per
calibrare soglie e capire la geometria stop/target.
- **Strumento:** DAX (Dukascopy `IDX_EUROPE_E_DAAX`), M1, bid.
- **Periodo:** 2024-07-01 → 2026-01-01 (388 giorni di trading, 505.585 candele).
- **Ancora:** 09:00 Europe/Berlin (DST-aware). Baseline = volume medio 08:30–09:00.

## Profondità dati
DAX M1 su Dukascopy: dal 2012 (~14 anni reali disponibili). Studio su 1,5 anni.

## Risultati
**Fonte:** `raw/study_2026-07-06_dax_open_volume.json` (immutabile).

- **Rapporto volume candela-segnale / baseline:** mediana **6,6×** (p25 5,5 · p75
  7,9 · p90 9,2). Volume >5× nell'**81%** dei giorni; >10× solo nel 5%.
- **Range candela segnale:** mediana **28 pt** (p25 21 · p75 37) → ordine di
  grandezza dello STOP dietro la candela.
- **Escursione 09:06–09:30 dalla chiusura segnale:** miglior lato mediana **56 pt**;
  **≥40 pt disponibili nel 71%** dei giorni (34% su, 41% giù).

## Walk-forward
N/A (studio, non backtest).

## Conclusione + gate
Effetto **confermato e sistematico** → giustifica scrivere la strategia. Due
avvertenze portate avanti nel design: (1) le soglie vanno **relative** (i 500/1000
di IG non valgono qui); (2) stop ~28 pt vs target 40 pt = R:R **~1,4:1**, stretto:
l'edge dipende dai runner, il backtest dovrà modellare bene trailing e parziali.
La % "≥40 pt" è un **upper bound**, non il win rate.
