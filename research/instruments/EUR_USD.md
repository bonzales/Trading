---
type: instrument
status: testing
tags: [forex, majors]
updated: 2026-07-06
links: ["[[pullback]]", "[[exp_2026-07-06_pullback_EUR_USD_H1]]"]
---
# EUR_USD

## Parametri
- Coppia major, la più liquida. Spread tipico modellato: ~1,5 pip (0.00015).
- Pip value / contract size / swap / leva ESMA: **da compilare** con i valori del
  conto IBKR quando il Gateway sarà attivo (sezione esecuzione).

## Profondità storica (Dukascopy)
Verificata via `--check-coverage` il 2026-07-06:
- **H1:** dal 2003-05-04 → **23,17 anni reali** (~203k candele teoriche 24/7).

Nota: usiamo Dukascopy come fonte dati di ricerca (gratuita, profonda). Quando il
Gateway IBKR sarà attivo, confronteremo la profondità storica IBKR per lo stesso
strumento (di solito più corta e con pacing limit).

## Storia dei test
| Data       | Strategia   | tf | Esito                        | Fonte |
|------------|-------------|----|------------------------------|-------|
| 2026-07-06 | [[pullback]]| H1 | `rejected` — PF 0.951, −14.1%| [[exp_2026-07-06_pullback_EUR_USD_H1]] |

## Note
Comportamento (volatilità per sessione, gap del weekend) da annotare man mano che
accumuliamo esperimenti. Primo test (pullback H1) senza edge in-sample.
