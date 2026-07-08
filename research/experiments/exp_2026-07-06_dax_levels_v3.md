---
type: experiment
status: rejected
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

## Conclusione + gate → poi RISOLTA (vedi sotto)
Difetto di fedeltà: questa v3 generava ~50 trade/anno (≈1/settimana) vs ≥1/giorno
reale. Verdetto sospeso e rifatto con la versione fedele multi-trade + multi-indice.

## Esito del test fedele (multi-trade, 4 indici, parametri normalizzati)
Fonte: `raw/exp_2026-07-06_dax_levels_v3_multi.json`. Frequenza reale (~1/gg).
- **US500** (356 trade, campione grande e INDIPENDENTE): **PF 0,92, perde in
  entrambe le metà.** Prova decisiva: il pattern vincente del DAX 2025-26 non si
  replica su un mercato diverso → fortuna di campione, non edge.
- **DAX**: aggregato 1,17 ma 1ª metà 0,94; positivo solo nei 69 trade recenti.
- **NAS100/US30**: 4-5 trade → setup non robusto lì.

**Verdetto finale: `rejected` come sistema meccanico.** Coerente su tutte le
meccanizzazioni. L'edge dell'utente era discrezionale. Ulteriore tuning verso il
campione DAX recente = overfitting: si chiude qui.
