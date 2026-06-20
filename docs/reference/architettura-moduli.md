# Reference — Architettura dei moduli

> Modalità: *reference*. Mappa dei moduli. Riuso vs riscrittura rispetto a Kraken.

```
src/
  config.py              # singola fonte di verità dei parametri
  main.py                # entry point (--mode paper|live)
  core/                  # IL CERVELLO (riusabile quasi as-is da Kraken)
    indicators.py        # EMA, RSI, MACD, ATR, OBV, Donchian, Ichimoku (nativi)
    strategy.py          # strategie + factory make_strategy(cfg)
    risk_manager.py      # sizing, stop ATR, 3 fasi, liquidazione, PnL
    reporting.py         # metriche condivise
  adapters/
    oanda/               # DA RISCRIVERE: dati + esecuzione OANDA
      data.py            # storico profondo, multi-tf, multi-strumento
      execution.py       # ordini forex/CFD, spread, swap, orari mercato
  backtest/
    data_fetcher.py      # download/cache storico (verifica copertura!)
    backtest_engine.py   # event-driven, optimize(), walk_forward()
    report.py            # CLI report
  interface/
    telegram_bot.py      # notifiche + comandi owner-only
    cli.py
  engine.py              # loop, stato persistente (crash-safe)
  logger.py
```

**Riusabile da Kraken:** `core/`, `backtest/`, `engine.py`, `logger.py`.
**Da riscrivere:** `adapters/oanda/` (dati + esecuzione + costi spread/swap + orari).
