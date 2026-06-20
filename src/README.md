# src/ — il motore

Codice eseguibile. Da costruire in Claude Code portando i moduli riusabili dal
progetto Kraken (`core/`, `backtest/`, `engine.py`, `logger.py`) e riscrivendo
l'adapter OANDA (`adapters/oanda/`). Mappa completa: `docs/reference/architettura-moduli.md`.

Ordine consigliato:
1. `adapters/oanda/data.py` + verifica profondità storica (lezione n.1 Kraken).
2. Estendere il backtest a multi-strumento/multi-timeframe + costi spread/swap + orari.
3. 1-2 strategie validate con walk-forward su più strumenti.
4. Paper su demo → eventuale live.
