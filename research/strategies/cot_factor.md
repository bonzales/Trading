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

## Cosa dice il test (onesto)
Fonte: `raw/exp_2026-07-12_cot_predictive.json`. Information coefficient (corr fattore →
rendimento forward) su 8 mercati:
- **A 20 giorni: rumore.** |IC| ~0,02 quasi ovunque. Nessun potere predittivo.
- **A 60 giorni: segnale debole ma sensato** solo su alcuni:
  - **WTI**: commercial net-long estremo → +5,2% vs −0,8% (IC 0,11). Segnale COT classico
    (produttori = smart money sulle commodity).
  - **EUR/USD** IC 0,18 (posizionamento speculativo), **S&P500** IC 0,08 (commercial-long
    → rialzo). Oro/argento/rame/GBP: **~zero**.

## Verdetto: NON è una strategia, al massimo un filtro
`testing`. Il COT **non è un edge standalone**: debole, lento (60gg), e con cautele pesanti —
rendimenti sovrapposti (significatività gonfiata), multiple testing (32 test, qualcuno
brilla per caso), nessun OOS. **Uso corretto:** *filtro di contesto / tilt di size* sugli
edge già confermati, sui mercati dove ha senso economico (commodity, commercial = veri
produttori) — **non** un segnale d'ingresso a sé. E va dimostrato che aggiunga valore
prima di inserirlo.

Il valore di questo lavoro: aver **evitato** di bullonare un fattore-folklore sul sistema
convincendoci che funzionasse. L'infrastruttura (downloader, fattori) resta riutilizzabile.

## Prossimo passo (gate §5)
Se si vuole procedere: testare se **filtrare/tiltare il [[commodity_trend]]** (WTI, oro)
col COT dei commercial **migliora** le metriche del sleeve. Tenerlo SOLO se supera; altrimenti
resta uno strumento di lettura, non un ingranaggio del sistema.
