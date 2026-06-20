# Tutorial 01 — Il tuo primo backtest

> Modalità: *tutorial*. Impari facendo, su un esempio guidato. Non spieghiamo qui
> ogni perché (quello sta in `explanation/`) né copriamo ogni opzione (quello sta in
> `reference/`). Seguiamo un percorso che funziona, dall'inizio alla fine.

Alla fine di questo tutorial avrai: scaricato dati storici da OANDA demo, lanciato un
backtest su EUR/USD, e archiviato il risultato nella wiki di ricerca.

## Prima di iniziare

Ti serve un account **demo** OANDA (gratuito). Da lì ottieni due cose:
- un `account_id`
- un `API token`

Mettili in un file `.env` (mai committato):

```
OANDA_ACCOUNT_ID=...
OANDA_API_TOKEN=...
OANDA_ENV=practice
```

## Passo 1 — Verifica la profondità storica

Questa è la prima cosa, sempre. Nel progetto Kraken i backtest "12 mesi" giravano in
realtà su 30 giorni perché l'API dava solo ~720 candele, e tutti i risultati erano
inaffidabili. Non dare per scontato di avere i dati che pensi di avere.

```
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --check-coverage
```

Leggi quante candele/anni hai *davvero* per questo strumento e timeframe. Annotalo.

## Passo 2 — Scarica e cache i dati

```
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --years 3
```

I dati grezzi finiscono in `raw/`. Sono immutabili: non li modificherai mai a mano.

## Passo 3 — Lancia il backtest

```
python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1
```

Guarda l'output: profit factor, Sharpe, max drawdown, numero di trade, curva equity.
L'output completo viene salvato in `raw/`.

## Passo 4 — NON fermarti qui: walk-forward

Un backtest in-sample positivo non significa niente da solo. Validalo su dati mai
visti:

```
python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1 --walkforward
```

Confronta in-sample vs out-of-sample. Se l'out-of-sample crolla, è overfitting e la
strategia si scarta. (Perché: [perche-walk-forward](../explanation/perche-walk-forward.md).)

## Passo 5 — Archivia nella wiki (ingest)

Apri Claude Code nella repo e di':

> "Ingest dell'ultimo backtest in raw/."

L'agente leggerà l'output grezzo, creerà la pagina in `research/experiments/`,
aggiornerà la pagina della strategia e dello strumento, aggiornerà `index.md` e
`log.md`, e applicherà il gate "scala o scarta" scrivendo il verdetto. Vedi
`CLAUDE.md` §3.1 per cosa fa esattamente.

## Fatto

Hai un primo risultato archiviato e collegato. Da qui:
- per lanciare backtest da telefono: [how-to/lanciare-backtest-da-telegram](../how-to/lanciare-backtest-da-telegram.md)
- per promuovere una strategia che regge: [how-to/promuovere-a-paper](../how-to/promuovere-a-paper.md)
