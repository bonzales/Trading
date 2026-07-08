---
type: strategy
status: rejected
tags: [indici, dax, scalping, m1, volume, opening-range, multi-strumento]
updated: 2026-07-06
links: ["[[DAX]]", "[[exp_2026-07-06_dax_open_volume_study]]", "[[exp_2026-07-06_dax_open_backtest]]", "[[exp_2026-07-06_dax_levels_v3]]"]
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
| 2026-07-06 | backtest v3 (livelli volume multi-day + rottura) | sospeso: sotto-genera (~1/sett vs ~1/gg reale); da rifare fedele + multi-indice | [[exp_2026-07-06_dax_levels_v3]] |

## Verdetto corrente
`rejected` **come sistema meccanico automatico** (dopo test fedele e severo). NON è
un giudizio sull'operatività manuale dell'utente.

Test finale (fonte: `raw/exp_2026-07-06_dax_levels_v3_multi.json`): frequenza reale
(~1/giorno), 4 indici, parametri **normalizzati alla volatilità**, spread realistici,
out-of-sample su due metà:
- **US500** (356 trade, campione grande e indipendente): **PF 0,92 → perde**, in
  entrambe le metà. È la prova decisiva: il "pattern vincente" del DAX 2025-26 **non
  si replica** su un mercato diverso → fortuna di campione (69 trade), non edge.
- **DAX**: aggregato PF 1,17 ma 1ª metà (162 trade) 0,94; positivo concentrato in 69
  trade recenti. Instabile.
- **NAS100 / US30**: il setup non scatta (4-5 trade in 3 anni) → non è nemmeno un
  fenomeno ben definito lì.

**Perché non "studiamo i vincenti 2025-26 e li replichiamo":** è la definizione di
overfitting (CLAUDE.md §5). Un pattern nei vincenti passati si trova sempre, ma
descrive il rumore di quel periodo. La prova: su US500 (dati mai usati per tarare)
quel pattern perde. L'edge reale dell'utente era **discrezionale** (timing/selezione/
gestione adattiva), non una regola fissa.

## Storico meccanizzazioni respinte (per non riprovarle)
v1 rimbalzo stop-largo (PF 1,04, muore a 2,5pt) · v2 rettangolo stop-stretto (0,81) ·
v3 livelli multi-day sotto-generante (miraggio) · v3-fedele multi-indice (US500 perde
su 356 trade). Riaprire SOLO con un *meccanismo* nuovo e pre-registrato, testato su
dati non usati per costruirlo — mai ritoccando i parametri per far salire il backtest.

## Note
Le soglie di volume di IG (500/1000) NON si trasferiscono: su Dukascopy lo stesso
evento vale ~1–3. Si usano soglie **relative**, ricalibrate per ogni fonte dati.
