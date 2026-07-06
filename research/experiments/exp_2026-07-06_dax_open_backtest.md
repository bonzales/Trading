---
type: experiment
status: rejected
tags: [indici, dax, scalping, m1, volume, backtest]
updated: 2026-07-06
links: ["[[dax_open_volume]]", "[[DAX]]"]
---
# Exp 2026-07-06 — backtest dax_open_volume (M1, 3y)

## Setup
- **Strategia:** [[dax_open_volume]] resa meccanica (vedi `src/backtest/dax_open.py`).
- **Strumento/tf:** DAX (Dukascopy mid), M1. **Periodo:** 2023-07-06 → 2026-07-06.
- **Parametri default:** vol_mult 5×, fascia prossimità (tol) 4 pt, conferma
  rimbalzo 3 pt, stop 2 pt oltre l'estremo, BE +25, parziale 50%@+40, trailing 15,
  rischio 2%/trade.
- **Costi:** spread in punti su ogni fill. Spread misurato in apertura: mediana
  **1,46 pt** (p90 2,66) → testato a 1,5 (ottimistico) e 2,5 (realistico con slippage).

## Profondità dati
DAX M1 Dukascopy dal 2012 (~14 anni). Backtest su 3 anni, 507 setup.

## Risultati
**Fonte:** `raw/exp_2026-07-06_dax_open_backtest.json` (immutabile).

In-sample, spread 1,5 pt: **PF 1,045**, win 39%, +481 pt, DD −22,6%, +9,3% in 3y
(long 270 / short 237). Un edge **tenue**.

**Tenuta per anno (spread 1,5):** 2023 PF 0,82 (−401 pt) · 2024 1,15 · 2025 1,08 ·
2026 1,02. **Incostante**, con un periodo in perdita.

**Sensibilità allo spread (decisiva):** PF 1,153 (0 pt) → **1,045 (1,5)** →
**0,976 (2,5)** → 0,933 (3,5). L'edge **muore a 2,5 pt**, cioè al costo realistico
in apertura (spread allargato + slippage).

**Contro-prova candele "d'oro":** alzando vol_mult (7/9/12×) il PF **peggiora**
(0,91 → 0,87), non migliora: l'alta convinzione non aiuta.

**Varianti d'uscita a 2,5 pt:** 4 su 5 negative; solo "parziale@60 + trail 25" a
PF 1,018 — ma è 1 su 5, per un pelo, non validata OOS → **rumore**.

## Walk-forward
Non eseguito: il risultato in-sample è già sul filo e crolla allo stress dei costi.
Ottimizzare per rifar salire il PF sarebbe overfitting (CLAUDE.md §5).

## Conclusione + gate
**Verdetto: `rejected` come strategia meccanica automatica.** Dopo costi realistici
il PF hovera 0,96–1,02: **break-even, indistinguibile da zero.** L'effetto apertura
esiste (vedi [[exp_2026-07-06_dax_open_volume_study]]), ma il semplice "rimbalzo sul
livello di volume" non ne estrae un edge che sopravviva allo spread.

**Nota importante (non è un giudizio sull'operatività manuale dell'utente):**
probabilmente l'edge reale dell'utente vive nella parte **discrezionale** — qualità
e timing dell'ingresso ("se si entra in modo corretto"), selezione delle giornate,
lettura del momentum — che questa v1 meccanica non cattura. Il valore era nell'abilità,
non in una regola fissa replicabile a basso costo. Automatizzarla così renderebbe
meno del trader stesso.
