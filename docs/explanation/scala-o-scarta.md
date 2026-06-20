# Il gate "scala o scarta"

> Modalità: *explanation*. Il perché della disciplina di promozione. La meccanica
> esatta degli stati è in `CLAUDE.md` §5.

## L'idea

Una strategia non passa da "interessante" a "soldi veri" in un salto. Attraversa
stadi, e a ogni stadio può solo **avanzare** (se supera la prova) o essere
**scartata**. Non si torna indietro ad ammorbidire i criteri per farla passare —
quello è esattamente il modo in cui ci si racconta una bugia.

```
untested → testing → edge-confirmed → paper → live
              │            │            │
              └─ scarta ───┴─ scarta ───┘
```

## Perché stadi rigidi

Il progetto Kraken ha prodotto una lista di tentazioni, tutte misurate come perdenti:

- **"Allento le condizioni così fa più trade."** Più operazioni ≠ più profitto. La
  qualità dei segnali è crollata e i risultati sono peggiorati.
- **"Alzo la leva così guadagno di più."** All-in a 10x → conto azzerato per
  liquidazione su 12 mesi. La leva amplifica soprattutto le perdite.
- **"Funziona benissimo sul passato."** Sì, e poi −45€ out-of-sample. Vedi
  [[perche-walk-forward]].

Ognuna di queste è una scorciatoia per saltare uno stadio. Il gate esiste per
renderle impossibili.

## Il verdetto onesto come prodotto

Su 7 strategie testate su 12 mesi di dati veri nel progetto Kraken, **nessuna** aveva
un edge reale. La migliore andava in pareggio. Questo non è un fallimento del lavoro:
è il lavoro. Sapere che un'idea non regge *prima* di rischiarci sopra dei soldi vale
esattamente quei soldi non persi.

Per questo nella wiki una strategia marcata `rejected` è una pagina di valore quanto
una `edge-confirmed`: impedisce di ri-testare la stessa idea tra sei mesi avendola
dimenticata.

## Dove vive lo stato

Nel frontmatter di ogni pagina `research/strategies/`, campo `status`. Il lint
controlla le incoerenze (es. una `edge-confirmed` che non è mai passata dal paper).
