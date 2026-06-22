# src/ — il motore

Codice eseguibile. Broker: **Interactive Brokers** (via IB Gateway/TWS) — OANDA
abbandonato perché non concede l'API agli utenti retail europei. Cambiare broker
tocca SOLO `adapters/` (qui la promessa dell'architettura si è già avverata una
volta). Mappa completa: `docs/reference/architettura-moduli.md`.

Ordine consigliato:
1. ✅ `adapters/ibkr/data.py` + verifica profondità storica (lezione n.1 Kraken). **Fatto.**
2. ✅ Backtest engine multi-uso + `optimize()` + `walk_forward()` + costi spread. **Fatto.**
3. 1-2 strategie validate con walk-forward su dati IBKR reali (serve conto paper + Gateway acceso).
4. Paper su demo → eventuale live.

## Stato attuale

| Modulo                          | Stato      | Note                                              |
|---------------------------------|------------|---------------------------------------------------|
| `config.py`                     | pronto     | carica `.env`, host/porta Gateway practice/live   |
| `adapters/ibkr/data.py`         | da verificare live | candele OHLCV, paginazione storica, `check_coverage`; testato offline, manca prova col Gateway |
| `backtest/data_fetcher.py`      | pronto     | CLI `--check-coverage` / `--years` (vedi tutorial 01) |
| `core/indicators.py`            | pronto     | EMA, RSI, MACD, ATR, Donchian (nativi)            |
| `core/strategy.py`              | pronto     | `PullbackStrategy` + factory `make_strategy`      |
| `core/risk_manager.py`          | pronto     | sizing su rischio %, stop ATR, TP1+breakeven, trailing |
| `core/reporting.py`             | pronto     | PF, Sharpe, max DD, win rate, n. trade            |
| `backtest/backtest_engine.py`   | pronto     | event-driven, `optimize()`, `walk_forward()`      |
| `backtest/report.py`            | pronto     | CLI backtest/walk-forward, salva output in `raw/` |
| `adapters/ibkr/execution.py`    | da fare    | ordini, spread, swap, orari mercato (per il paper) |

## Come partire (dev)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # poi compila col conto paper IBKR (serve IB Gateway acceso)
pytest -q                     # test offline (no rete, no credenziali)

# Passo 1: verifica la profondità storica REALE
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --check-coverage
# Passo 2: scarica lo storico
python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --years 3
# Passo 3-4: backtest e walk-forward
python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1
python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1 --walkforward
```
