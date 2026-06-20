---
type: strategy
status: testing
tags: [trend-following, ereditata-kraken]
updated: 2026-06-19
links: []
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
| Data       | Mercato | Esito                        | Fonte           |
|------------|---------|------------------------------|-----------------|
| (Kraken)   | crypto  | pareggio: PF 0.91, ~−3€, 1x  | progetto Kraken |

## Verdetto corrente
`testing`. Su crypto andava in pareggio — il candidato meno peggio, ma **non** un
edge confermato. Da ri-testare su forex/indici OANDA da zero: un comportamento su
crypto non si trasferisce automaticamente. Primo test consigliato: EUR_USD H1, 3y,
con walk-forward.

## Note
Allentare le condizioni per fare più trade ha PEGGIORATO i risultati su Kraken. Non
ripetere l'errore: non ottimizzare verso "più operazioni".
