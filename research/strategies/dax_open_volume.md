---
type: strategy
status: rejected
tags: [indici, dax, scalping, m1, volume, opening-range]
updated: 2026-07-06
links: ["[[DAX]]", "[[exp_2026-07-06_dax_open_volume_study]]", "[[exp_2026-07-06_dax_open_backtest]]"]
---
# dax_open_volume (scalping apertura DAX)

## Idea
All'apertura cash di Francoforte (09:00 Europe/Berlin) i grandi operatori entrano
e generano un picco di volume. La candela M1 a volume anomalo nella finestra
09:00–09:05 lascia un **livello** (chiusura + estremo) che poi funziona da
supporto/resistenza nella prima mezz'ora. Si opera il rimbalzo su quel livello,
long o short, stop dietro la candela segnale, lasciando correre i runner.

Strategia discrezionale dell'utente (anni di operatività su IG), da rendere
meccanica e validare da zero su dati veri. Motivazione forte: "funziona ma è
mentalmente pesante da gestire" → candidata ideale all'automazione.

## Regole meccaniche (v1, da calibrare col walk-forward)
- **Apertura:** 09:00 Europe/Berlin (DST-aware).
- **Candela segnale:** in 09:00–09:05, candela M1 col volume più alto che supera
  una soglia **relativa** (multiplo della media volume pre-apertura 08:30–09:00).
  Soglia di partenza dai dati: **≥5×** (presente nell'81% dei giorni).
- **Livello:** chiusura + estremo (max se rialzista, min se ribassista).
- **Ingresso con elasticità:** fascia di prossimità ±`tol` pt attorno al livello;
  si entra quando il prezzo entra nella fascia e una candela rimbalza (chiude
  ≥`conferma` pt nella direzione opposta). Cattura sia il tocco esatto sia il
  "ci va vicino e riparte".
- **Direzione:** long e short.
- **Stop:** dietro l'estremo della candela segnale (definisce R).
- **Uscite:** +20/30 pt → stop a pari; +40 pt → parziale + trailing +10/15/20;
  poi lascia correre col trailing.
- **Rischio:** ≤2–3% del capitale per trade.

## Perché è delicata (dai dati, vedi studio)
Candela segnale ampia in mediana **28 pt** = stop ~28 pt per un target di 40 →
R:R ~1,4:1. Stretto. L'edge, se c'è, vive nei **runner** (win rate anche <50%).
Il backtest deve modellare bene parziali+trailing, o la sottovaluta.

## Storia dei test
| Data       | Cosa                          | Esito                        | Fonte |
|------------|-------------------------------|------------------------------|-------|
| 2026-07-06 | studio esplorativo pre-backtest | effetto confermato; R:R stretto | [[exp_2026-07-06_dax_open_volume_study]] |
| 2026-07-06 | backtest v1 (chase, stop largo) | `rejected`: PF 1,045 a 1,5pt, muore a 2,5pt | [[exp_2026-07-06_dax_open_backtest]] |
| 2026-07-06 | backtest v2 (rettangolo, stop stretto, elastico) | `rejected`: PF 0,81 → peggiore | [[exp_2026-07-06_dax_open_backtest]] |

## Verdetto corrente
`rejected` **come strategia meccanica automatica.** L'effetto apertura esiste, ma il
rimbalzo sul livello di volume non produce un edge che sopravviva ai costi reali:
dopo spread 2,5 pt (realistico in apertura) il PF è ~break-even (0,96–1,02), incostante
per anno. Le candele "d'oro" non migliorano; l'unica variante positiva è rumore (1/5,
non OOS).

**Non è un giudizio sull'operatività manuale dell'utente:** l'edge reale vive
probabilmente nella parte discrezionale (timing/qualità d'ingresso, selezione giornate)
non catturata da questa v1. Riaprire solo con un'ipotesi *nuova e testabile* (es. un
filtro di contesto/momentum validato in walk-forward), non ritoccando i parametri.

## Note
Le soglie di volume di IG (500/1000) NON si trasferiscono: su Dukascopy lo stesso
evento vale ~1–3. Si usano soglie **relative**, ricalibrate per ogni fonte dati.
