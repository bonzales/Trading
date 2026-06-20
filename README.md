# oanda-quant

> Nome di lavoro — rinominalo come preferisci (basta cambiare la cartella e questo
> titolo). Sistema di backtesting e trading semi-automatico su **OANDA** (forex,
> indici, materie prime), con un livello di conoscenza che si accumula nel tempo.

Erede del bot crypto su Kraken. Quello che cambia: broker (Kraken → OANDA), ambizione
del backtesting (molti più strumenti/timeframe, validazione rigorosa), e — la novità
vera — una **wiki di ricerca** che ricorda cosa è già stato testato.

## Le due idee che tiene insieme

- **[Diátaxis](https://diataxis.fr/)** struttura `docs/` per l'umano: tutorial,
  how-to, reference, explanation.
- **[LLM-Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**
  struttura `research/` per l'agente: una base di conoscenza che l'LLM mantiene da
  solo, dove ogni backtest viene archiviato, collegato e confrontato. Invece di
  ri-testare le stesse strategie perdenti, la wiki sa già cosa non ha edge.

## Struttura

```
CLAUDE.md      ← la schema: leggila per prima, governa tutto
raw/           ← output grezzi dei backtest (IMMUTABILI, fonte di verità)
research/      ← la wiki di ricerca (l'agente la scrive, tu la leggi)
docs/          ← documentazione umana (Diátaxis)
src/           ← il motore (engine, backtest, adapter OANDA, interfaccia)
```

## Il ciclo

```
messaggio in linguaggio naturale
        │
        ▼
   BACKTEST  ──────►  archiviato in research/ (ingest)
        │
        ▼
   gate "scala o scarta"  (vedi CLAUDE.md §5 e docs/explanation/scala-o-scarta.md)
        │
   ┌────┴─────┬──────────┐
   ▼          ▼          ▼
 scarta     PAPER  ───►  LIVE
            (demo)      (denaro che ci si può permettere di perdere)
```

## Da dove partire

1. Leggi `CLAUDE.md` (la schema).
2. Leggi `docs/explanation/` — le lezioni Kraken, sono il capitale del progetto.
3. Segui `docs/tutorials/01-primo-backtest.md`.
4. Apri un account **demo** OANDA → `account_id` + token → `src/`.

## Stack

Python 3.11 · pandas/numpy · `oandapyV20` · `python-telegram-bot` · matplotlib ·
deploy su VPS Hetzner via systemd (riuso dell'infrastruttura Kraken).
