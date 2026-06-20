# Come aggiungere uno strumento

> Modalità: *how-to*. Passi per testare un nuovo strumento (es. XAU/USD, US500).

1. Verifica la profondità storica reale su OANDA per quello strumento/timeframe:
   `python -m src.backtest.data_fetcher --instrument XAU_USD --tf H1 --check-coverage`
2. Registra i parametri per-strumento: pip value, contract size, spread tipico, swap.
   Mettili nella config per-strumento in `src/` e nella pagina
   `research/instruments/XAU_USD.md`.
3. Scarica e cache i dati: `--years N`.
4. Lancia backtest + walk-forward come nel tutorial 01.
5. Ingest da Claude Code → la pagina strumento viene aggiornata.

Nota: oro e indici hanno volatilità e orari diversi dal forex major. Non riusare gli
stessi stop/sizing senza ri-testare.
