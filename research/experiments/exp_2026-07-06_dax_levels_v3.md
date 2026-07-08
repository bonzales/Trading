---
type: experiment
status: testing
tags: [indici, dax, scalping, m1, volume, multi-day, backtest]
updated: 2026-07-06
links: ["[[dax_open_volume]]", "[[DAX]]"]
raw: ["raw/exp_2026-07-06_dax_levels_v3.json"]
---
# Exp 2026-07-06 — v3 livelli-volume multi-day DAX

## Setup
Terza meccanizzazione, la più fedele al metodo completo dell'utente (vedi
[[dax_open_volume]]): **mappa di livelli** lasciati dalle candele ad alto volume
(apertura, chiusura 17:30, spike), **memoria multi-day** (normali 5gg, "oro" a
lungo), **ingresso sulla rottura** netta di un livello in gioco (finestra
09:06–11:00), **stop al livello di volume opposto**, uscite proxy della gestione
discrezionale (time-stop, pari 1R, parziale, trailing). Codice: `src/backtest/dax_levels.py`.
DAX M1 Dukascopy, 3 anni. **Fonte:** `raw/exp_2026-07-06_dax_levels_v3.json`.

## Risultati
- **Con time-stop:** PF 0,75 (1,5) / 0,69 (2,5) → perde. 120/149 uscite sono
  time-stop: l'ingresso genera molti "falsi" che stallano.
- **Senza time-stop** (diagnostico): aggregato **PF 1,15 (1,5) / 1,11 (2,5)**,
  win 51–52%, +12–19%. Sembrava il primo edge a reggere i costi.

## Stress out-of-sample (il test decisivo)
Il positivo aggregato è un **miraggio da piccolo campione**:
- **1ª metà 2023-24: 109 trade → PF 0,81, −20%** (perde, ed è la maggioranza dei dati);
- 2ª metà 2025-26: 39 trade → PF 2,34, +45%.
- Per anno: 2024 (68 trade) PF 0,70; gli anni "buoni" (2025/2026) hanno 15 e 20 trade.

Il guadagno è concentrato in ~39 operazioni recenti. Non è stabilità, è fortuna
di campione.

## Conclusione + gate
**Verdetto SOSPESO — non rejected.** Difetto di fedeltà scoperto dopo il test:
questa v3 genera ~50 trade/anno (≈1/settimana), ma l'utente ne faceva **≥1 al
giorno** (~4/settimana per strumento). Quindi cattura ~1/5 dei setup reali → il
risultato (e la sua instabilità OOS) riflette un'implementazione **azzoppata**, non
la strategia. Rigettarla ora sarebbe scorretto.

**Prossimo passo:** versione fedele alla frequenza reale (più setup/giorno) +
estensione ai 3 indici USA (apertura 15:30) → 4 mercati indipendenti come OOS
naturale. Il verdetto si emette dopo quel test. Nota metodologica utile comunque:
senza time-stop l'aggregato saliva (PF 1,11 a 2,5pt) ma per il momento su base
piccola e sbilanciata nel tempo — da riconfermare con frequenza e strumenti veri.
