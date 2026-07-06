---
type: experiment
status: rejected
tags: [forex, trend-following, h1, pullback, dukascopy]
updated: 2026-07-06
links: ["[[pullback]]", "[[EUR_USD]]"]
---
# Exp 2026-07-06 — pullback EUR_USD H1 3y

## Setup
- **Strategia:** [[pullback]] (parametri di default della `PullbackStrategy`).
- **Strumento / tf:** EUR_USD, H1.
- **Periodo:** 2023-07-06 → 2026-07-06 (~3 anni), 18.650 candele complete.
- **Prezzo:** mid = media OHLC di bid e ask (Dukascopy fornisce bid/ask separati).
- **Costi modellati:** `CostModel` di default, spread 0.00015 (1,5 pip), mezzo
  spread per fill → 1 spread per round-trip. Nessuno swap notturno modellato.
- **Sorgente dati:** Dukascopy (gratuita, senza conto). IBKR resta il broker di
  esecuzione; per la ricerca i dati vengono da qui.

## Profondità dati
Verificata, non assunta (lezione n.1 Kraken): EUR_USD H1 su Dukascopy parte dal
**2003-05-04** → **23,17 anni reali** disponibili. Per questo test ne abbiamo usati
3. Fonte coverage: `--check-coverage` via `src/backtest/data_fetcher.py`.

## Risultati (in-sample)
| Metrica        | Valore   |
|----------------|----------|
| n. trade       | 474      |
| profit factor  | **0.951**|
| win rate       | 40.7%    |
| sharpe         | −0.22    |
| max drawdown   | −32.1%   |
| rendimento     | −14.1%   |
| equity finale  | 8.594    |

**Fonte:** `raw/exp_2026-07-06_pullback_EUR_USD_H1_backtest.json` (immutabile).

## Walk-forward
Non eseguito **di proposito**: con PF ≤ 1 in-sample non c'è edge da validare fuori
campione. Il gate ferma qui (vedi CLAUDE.md §5).

## Conclusione + gate
**Verdetto: `rejected` per la combinazione pullback × EUR_USD × H1.** Nessun edge
in-sample su 3 anni di dati veri, con spread realistico. Coerente con Kraken, dove
la pullback andava al massimo in pareggio (PF 0.91): non si trasferisce un edge che
non c'era. Un risultato negativo onesto è prezioso: ci ha risparmiato di inseguire
un walk-forward inutile.

Non rigetta la strategia in assoluto: restano da provare altri timeframe/strumenti
(es. H4, o un indice) prima di conclusioni più larghe. Vedi [[pullback]].
