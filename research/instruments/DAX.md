---
type: instrument
status: testing
tags: [indici, dax, germania]
updated: 2026-07-06
links: ["[[dax_open_volume]]", "[[exp_2026-07-06_dax_open_volume_study]]"]
---
# DAX (Germany 40)

Indice azionario tedesco. In Dukascopy: `INSTRUMENT_IDX_EUROPE_E_DAAX` (alias
progetto: `DAX`). Punto DAX = 1 punto indice.

## Parametri
- Apertura cash: **09:00 Europe/Berlin** (Xetra). Fenomeno chiave: picco di volume
  e volatilità in apertura (vedi studio).
- Spread / commissioni / leva ESMA: da compilare con i valori del conto IBKR
  (esecuzione). Su CFD indice lo spread tipico è pochi punti — rilevante per lo
  scalping da 40 pt: va modellato realisticamente.

## Profondità storica (Dukascopy)
- **M1:** dal 2012 → ~14 anni reali. **D1** idem. Verificato 2026-07-06.

## Storia dei test
| Data       | Strategia          | tf | Esito                    | Fonte |
|------------|--------------------|----|--------------------------|-------|
| 2026-07-06 | [[dax_open_volume]]| M1 | studio: effetto confermato, backtest da fare | [[exp_2026-07-06_dax_open_volume_study]] |

## Note
Volume Dukascopy = attività sulla loro liquidità (proxy relativo, non assoluto).
Le soglie di volume vanno definite in modo relativo, mai come numeri fissi.
Timestamp dati in UTC: 09:00 Berlino = 07:00 UTC (estate) / 08:00 UTC (inverno).
