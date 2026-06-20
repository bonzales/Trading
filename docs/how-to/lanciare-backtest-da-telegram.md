# Come lanciare un backtest da Telegram

> Modalità: *how-to*. Trigger rapido dal telefono, output sul VPS.

Comando strutturato (eredita il pattern Kraken):

```
/backtest <strategia> <strumento> <timeframe> <periodo>
```

Esempio: `/backtest pullback EUR_USD H1 3y`

Cosa succede:
1. Il bot sul VPS esegue il backtest.
2. Deposita l'output grezzo in `raw/`.
3. Appende uno stub a `research/log.md`.
4. Ti rimanda un riassunto (PF, Sharpe, max DD, n. trade).

Il **consolidamento nella wiki** (pagine strategia/strumento/esperimento) lo fai poi
da Claude Code con l'ingest — vedi `CLAUDE.md` §3.1. Il telefono serve a far partire
il calcolo e a leggere il verdetto, non a mantenere la ricerca.

Per il linguaggio libero ("prova la pullback sull'oro") vedi la decisione di design
aperta in `CLAUDE.md` §6.
