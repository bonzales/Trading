# src/ — il motore

Codice eseguibile. Da costruire in Claude Code portando i moduli riusabili dal
progetto Kraken (`core/`, `backtest/`, `engine.py`, `logger.py`) e riscrivendo
l'adapter OANDA (`adapters/oanda/`). Mappa completa: `docs/reference/architettura-moduli.md`.

Ordine consigliato:
1. ✅ `adapters/oanda/data.py` + verifica profondità storica (lezione n.1 Kraken). **Fatto.**
2. Estendere il backtest a multi-strumento/multi-timeframe + costi spread/swap + orari.
3. 1-2 strategie validate con walk-forward su più strumenti.
4. Paper su demo → eventuale live.

## Stato attuale

| Modulo                          | Stato      | Note                                              |
|---------------------------------|------------|---------------------------------------------------|
| `config.py`                     | pronto     | carica `.env`, risolve host practice/live         |
| `adapters/oanda/data.py`        | pronto     | candele OHLCV, paginazione storica, `check_coverage` |
| `backtest/data_fetcher.py`      | pronto     | CLI `--check-coverage` / `--years` (vedi tutorial 01) |
| `backtest/backtest_engine.py`   | da fare    | event-driven, `optimize()`, `walk_forward()`      |
| `core/` (indicatori, strategie) | da fare    | porto/riscrittura dal progetto Kraken             |
| `adapters/oanda/execution.py`   | da fare    | ordini, spread, swap, orari mercato               |

## Come partire (dev)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # poi compila con le credenziali demo OANDA
pytest -q                     # test offline (no rete, no credenziali)

# Passo 1 del tutorial: verifica la profondità storica REALE
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --check-coverage
```
