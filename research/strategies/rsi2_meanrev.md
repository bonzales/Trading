---
type: strategy
status: paper
tags: [mean-reversion, indici, daily, rsi2, connors]
updated: 2026-07-11
links: ["[[exp_2026-07-08_rsi2_meanrev]]", "[[donchian]]", "[[meanrev]]", "[[US500]]"]
---
# rsi2_meanrev (compra il ribasso sugli indici)

## Idea
Mean-reversion di breve stile Connors RSI-2: gli indici azionari hanno **drift
rialzista + rientri di breve**. Si compra quando il prezzo è ipervenduto ma **sopra
il trend di fondo**, si esce quando rimbalza. È l'edge **complementare** al
trend-following, e proprio quello che ha funzionato nel regime 2011-2026 dove il TF
è stato piatto. Codice: `src/backtest/meanrev.py` (backtester dedicato: le uscite MR
sono diverse dal trailing dell'engine).

## Regole (canoniche, poche → poco overfitting)
- Filtro trend: `close > SMA(200)` (solo in uptrend di fondo → sta fuori dai crash).
- Ingresso long: `RSI(2) < oversold` (~10).
- Uscita: `RSI(2) > exit_rsi` (~50) **o** `close > SMA(5)` **o** `max_hold` barre.
- Stop di protezione: 3×ATR sotto l'ingresso. Long-only. Costi: spread modellato.

## Perché è `edge-confirmed` (passa i test che donchian aveva fallito)
Fonte: `raw/exp_2026-07-08_rsi2_meanrev.json`.
- **5/5 indici** positivi (PF 1,08–2,57; US500 2,57), win rate 67–80%.
- **Due metà stabili** per mercato (US500 2,59/2,55).
- **Portafoglio** 5 indici: +50% in 14y, **CAGR +3%, maxDD −8,3%**, 10/15 anni positivi.
- **Regge i crash**: 2020 −2%, 2022 −1% (il filtro 200MA sta fuori dai ribassi).
- **Sensibilità parametri: 27/27 combinazioni positive** (PF 1,38–1,65) → non è un
  parametro fortunato, è tutto il vicinato. Questo è il test anti-overfitting decisivo.
- **OOS temporale**: train (primi 60%) PF 1,43 → OOS (ultimi 40%, mai visti) **1,77**
  (migliora fuori campione).

## Verdetto corrente
`edge-confirmed`. Primo edge **vero e robusto** del progetto — etichetta guadagnata con
la validazione completa (a differenza di [[donchian]], ritrattato). **Cautele
load-bearing:**
- **Modesto**: CAGR ~3% a 0,7% rischio/trade. Scalabile alzando il rischio, ma sale
  anche il drawdown. Non è un bancomat.
- **Strategia pubblicata** (Connors RSI2): possibile **affollamento** → la performance
  live può essere più debole del backtest. Il paper trading dirà la verità.
- **Tail risk**: un ribasso che parte da sopra la 200MA e non rimbalza fa male; il DD
  futuro può superare −8%. Mitigato (filtro + stop) ma non azzerato.

## Stato: IN PAPER (dal 2026-07-11)
Bot in esecuzione automatica sul VPS (`src/live/paper_bot.py`), timer giornaliero 22:30
Europe/Berlin, conto **paper IBKR**, notifiche Telegram a ogni operazione + riepilogo.
Fase di validazione: confrontare i trade REALI con le attese del backtest (win ~70%,
PF portafoglio ~1.5, ~4-5 trade/mese, drawdown atteso 10-25% secondo il rischio).
Promozione a `live` SOLO se il paper replica il backtest per settimane. Registro
operazioni in `raw/live_log.csv`.

### Da verificare durante il paper
- **Fill vs prezzo atteso** (slippage nel comprare la debolezza).
- **Sizing** corretto (point_value CFD calibrato dai contratti IBKR).
- Il **riepilogo Telegram arriva ogni sera** (se manca → Gateway giù, va controllato).

## Note
Diverso dalla [[meanrev]] ereditata da Kraken (crypto, rigettata): altro mercato, altro
meccanismo. Qui l'edge vive sugli **indici azionari** per via del drift + rientri brevi.
