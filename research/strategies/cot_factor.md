---
type: strategy
status: testing
tags: [cot, fattore, posizionamento, istituzionali, fondamentale, filtro]
updated: 2026-07-12
links: ["[[commodity_trend]]", "[[gold_trend]]", "[[exp_2026-07-12_cot_predictive]]"]
---
# cot_factor (posizionamento istituzionale COT come fattore)

## Idea
Il COT (Commitments of Traders, CFTC, settimanale) mostra come sono posizionati i grandi
operatori sui futures USA: **commercial** (hedgers/produttori = spesso "mani forti") e
**non-commercial** (speculatori/fondi = spesso trend-follower). Ipotesi dell'utente:
gli estremi di posizionamento anticipano i movimenti. Costruito come **COT index**
(posizione netta normalizzata 0-100 su finestra 3 anni) su commercial e speculatori.

Solo futures USA → **DAX e UK100 non ci sono** (europei). Codice:
`src/adapters/cot/` (downloader + fattori).

## IMPORTANTE: usare il report GIUSTO (correzione 2026-07-12)
Il primo test usava il report **Legacy** (commercial/non-commercial grezzo): per forex e
indici il "commercial" sono per lo più *dealer* → categoria priva di senso. I report
corretti sono:
- **Disaggregated** per le commodity → **Managed Money** (fondi trend) vs **Producer** (veri hedger).
- **TFF** per forex/indici → **Leveraged Funds** (hedge fund) vs **Asset Manager** (real money).
Il downloader ora instrada ogni strumento al report giusto (`SYMBOL_ROUTING`).

## Cosa dice il test (onesto, coi report corretti + OOS)
Fonte: `raw/exp_2026-07-12_cot_predictive.json`. IC = corr(COT index, rendimento forward 60gg).
- **A 20 giorni: rumore** (|IC|~0,02). Il COT è lento, non funziona a breve.
- **A 60 giorni, coi report corretti, e con check OOS (train 60% / test 40%)** — reggono
  fuori campione **3 mercati su 6 testati**, con segno economicamente sensato:
  - **Oro** — Managed Money, **momentum** (IC train +0,05 / test +0,15): si va CON i fondi.
  - **WTI** — Managed Money, **contrarian** agli estremi (−0,12 / −0,08): si va CONTRO i fondi carichi.
  - **GBP** — Leveraged Funds, **contrarian** (−0,08 / −0,27).
  - **Argento, S&P500, EUR**: l'IC pieno sembrava buono ma **cambia segno OOS** → illusioni.

## Verdetto: filtro credibile su ORO e WTI, non una strategia
`testing`. Col report giusto il COT è **debole ma reale** (IC ~0,1) e sopravvive all'OOS
proprio su **oro e WTI** — i due mercati dove abbiamo **già un trend edge confermato**
([[commodity_trend]]). Lì è un candidato credibile come **tilt di size** (rafforza il trend
sull'oro quando i fondi lo seguono; alleggerisci sul petrolio quando sono troppo carichi).
**Non** è un trigger d'ingresso a sé (IC troppo basso). Va dimostrato che aggiunga valore.

> La lezione: il primo verdetto ("COT ~rumore") era **sbagliato per colpa del report Legacy**.
> Coi dati giusti il segnale c'è, debole. Contraddizione conservata, non cancellata.

## Prossimo passo (gate §5)
Se si vuole procedere: testare se **filtrare/tiltare il [[commodity_trend]]** (WTI, oro)
col COT dei commercial **migliora** le metriche del sleeve. Tenerlo SOLO se supera; altrimenti
resta uno strumento di lettura, non un ingranaggio del sistema.
