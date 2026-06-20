# src/ — il motore

Codice eseguibile. Da costruire in Claude Code portando i moduli riusabili dal
progetto Kraken (`core/`, `backtest/`, `engine.py`, `logger.py`) e riscrivendo
l'adapter OANDA (`adapters/oanda/`). Mappa completa: `docs/reference/architettura-moduli.md`.

Ordine consigliato:
1. ✅ `adapters/oanda/data.py` + verifica profondità storica (lezione n.1 Kraken). **Fatto.**
2. ✅ Backtest engine multi-uso + `optimize()` + `walk_forward()` + costi spread. **Fatto.**
3. 1-2 strategie validate con walk-forward su dati OANDA reali (serve account demo).
4. Paper su demo → eventuale live.

## Stato attuale

| Modulo                          | Stato      | Note                                              |
|---------------------------------|------------|---------------------------------------------------|
| `config.py`                     | pronto     | carica `.env`, risolve host practice/live         |
| `adapters/oanda/data.py`        | pronto     | candele OHLCV, paginazione storica, `check_coverage` |
| `backtest/data_fetcher.py`      | pronto     | CLI `--check-coverage` / `--years` (vedi tutorial 01) |
| `core/indicators.py`            | pronto     | EMA, RSI, MACD, ATR, Donchian (nativi)            |
| `core/strategy.py`              | pronto     | `PullbackStrategy` + factory `make_strategy`      |
| `core/risk_manager.py`          | pronto     | sizing su rischio %, stop ATR, TP1+breakeven, trailing |
| `core/reporting.py`             | pronto     | PF, Sharpe, max DD, win rate, n. trade            |
| `backtest/backtest_engine.py`   | pronto     | event-driven, `optimize()`, `walk_forward()`      |
| `backtest/report.py`            | pronto     | CLI backtest/walk-forward, salva output in `raw/` |
| `adapters/oanda/execution.py`   | da fare    | ordini, spread, swap, orari mercato (per il paper) |

## Come partire (dev)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # poi compila con le credenziali demo OANDA
pytest -q                     # test offline (no rete, no credenziali)

# Passo 1: verifica la profondità storica REALE
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --check-coverage
# Passo 2: scarica lo storico
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --years 3
# Passo 3-4: backtest e walk-forward
python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1
python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1 --walkforward
```
