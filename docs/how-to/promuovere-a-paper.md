# Come promuovere una strategia a paper trading

> Modalità: *how-to*. Prerequisito: la strategia è `edge-confirmed` (ha passato il
> walk-forward out-of-sample). Se non lo è, fermati: vedi
> `explanation/scala-o-scarta.md`.

1. Verifica lo status nella pagina `research/strategies/<strategia>.md`: deve essere
   `edge-confirmed`. Non promuovere una strategia solo in-sample.
2. Avvia il paper trading sul conto **demo** OANDA:
   `python -m src.main --mode paper --strategy <strategia> --instrument <strumento>`
3. Lascialo girare **settimane, non ore**. Il paper serve a vedere se il
   comportamento dal vivo (spread reali, slippage, gap weekend) replica il backtest.
4. Confronta i risultati paper col backtest. Se divergono in modo sostanziale, la
   strategia torna a `testing` o va `rejected`: il backtest aveva un'assunzione
   ottimistica (spesso i costi).
5. Ingest da Claude Code → status `paper`.

Solo se il paper è coerente col backtest si considera il live.
