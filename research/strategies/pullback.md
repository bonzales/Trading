---
type: strategy
status: testing
tags: [trend-following, ereditata-kraken]
updated: 2026-07-06
links: ["[[EUR_USD]]", "[[exp_2026-07-06_pullback_EUR_USD_H1]]"]
---
# pullback

## Idea
Entrare nella direzione del trend (EMA20 > EMA50) durante un ritracciamento, con
conferma di momentum. È la strategia di default e l'unica che su Kraken non perdeva.

## Logica di ingresso
Trend EMA + RSI in banda + MACD (`state` o `cross`) + OBV. Numero di condizioni
richieste configurabile (`min_conditions`).

## Logica di uscita
Stop ATR + TP1 parziale con breakeven + trailing.

## Storia dei test
| Data       | Mercato        | Esito                          | Fonte           |
|------------|----------------|--------------------------------|-----------------|
| (Kraken)   | crypto         | pareggio: PF 0.91, ~−3€, 1x    | progetto Kraken |
| 2026-07-06 | forex EUR_USD H1| `rejected`: PF 0.951, −14.1%, 474 trade | [[exp_2026-07-06_pullback_EUR_USD_H1]] |

## Verdetto corrente
`testing`. Primo test su forex reale (EUR_USD H1, 3y, dati Dukascopy, spread 1,5
pip): **nessun edge in-sample** (PF 0.951) → combinazione scartata, come previsto.
Conferma la lezione: un edge assente su crypto non compare per magia sul forex.
Restano da provare, prima di rigettare la strategia in assoluto: **H4** (meno
rumore) e almeno **un indice**. Se anche lì PF ≤ 1 in-sample, la pullback va
archiviata come `rejected` a tutti gli effetti.

## Note
Allentare le condizioni per fare più trade ha PEGGIORATO i risultati su Kraken. Non
ripetere l'errore: non ottimizzare verso "più operazioni".
