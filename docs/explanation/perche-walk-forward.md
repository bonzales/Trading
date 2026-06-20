# Perché il walk-forward è obbligatorio

> Modalità: *explanation*. Qui spieghiamo il ragionamento. Per il "come si lancia"
> vedi `how-to/`; per i parametri esatti vedi `reference/`.

## Il problema: l'overfitting è il nemico numero uno

Cercare "la strategia che funziona sul passato" è facile e ingannevole. Con
abbastanza parametri da girare, trovi *sempre* una combinazione che sul periodo
storico sembra oro. Poi la metti dal vivo e perde. Quella combinazione non aveva
scoperto una regolarità del mercato: aveva memorizzato il rumore di quei dati
specifici.

Questo non è un rischio teorico. Nel progetto Kraken è successo, misurato:

> best params: in-sample **+10€** → out-of-sample **−45€** → OVERFITTING.

La stessa strategia, stessi parametri. La differenza era solo che il secondo
spezzone di dati il modello non l'aveva "visto" durante l'ottimizzazione. Ed è
crollato.

## La soluzione: separare ottimizzazione e validazione

Il walk-forward divide i dati in due (o più) blocchi temporali:

```
│◄──── training ────►│◄── test ──►│
│  qui ottimizzi i    │  qui validi │
│  parametri          │  e basta    │
```

- Sul **training** cerchi i parametri migliori (grid search, ecc.).
- Sul **test** — dati mai visti durante l'ottimizzazione — applichi quei parametri
  così come sono e guardi se reggono.

Se l'edge è reale, sopravvive al passaggio sui dati nuovi. Se era illusione, muore.
Non c'è scappatoia: o regge out-of-sample, o si scarta.

La versione più robusta è il **walk-forward rolling**: più finestre training/test
che scorrono nel tempo, così non dipendi da come è caduto un singolo split.

## Perché è non negoziabile

Senza questo passo, "ho fatto il backtest e guadagna" non significa niente. Con
questo passo, hai l'unica evidenza che distingue un edge da una coincidenza. È la
ragione per cui nel gate "scala o scarta" il walk-forward sta *prima* del paper
trading e *molto* prima del denaro vero.

## Lezione collegata

Aumentare il capitale non sistema una strategia che non regge l'out-of-sample: ne
moltiplica solo le perdite. La validazione viene prima del sizing, sempre.

Vedi anche: [[scala-o-scarta]], `research/log.md` (cerca gli eventi `walk-forward`).
