---
type: strategy
status: edge-confirmed
tags: [trend-following, oro, daily, donchian, long-only]
updated: 2026-07-12
links: ["[[rsi2_meanrev]]", "[[fx_meanrev]]", "[[donchian]]", "[[exp_2026-07-12_gold_trend]]", "[[XAU_USD]]"]
---
# gold_trend (trend-following solo-long sull'oro)

## Idea
L'oro non oscilla attorno a una media come le valute: **tende**. È un asset monetario
(real rates, bene rifugio, acquisti delle banche centrali) con **drift rialzista
secolare** e regimi persistenti. Lo stile giusto è il **trend-following**, non il
mean-reversion — l'opposto del forex. E come per gli indici, il drift rende lo **short
controproducente**: la versione **solo-long** batte nettamente il long/short.

Codice: `src/core/strategy.py::DonchianLongStrategy` (registrata come `donchian_long`),
sul motore `run_backtest` (stop ATR + TP1 parziale + trailing).

## Regole (canoniche, poche → poco overfitting)
- **Long** quando il prezzo chiude sopra il massimo degli ultimi `channel` giorni
  (Donchian breakout, canale ~40-55).
- **Niente short** (il drift rialzista li penalizza).
- Uscita: stop ATR (2×), TP1 parziale a 1,5R con stop a breakeven, poi trailing 2×ATR.
- Daily. Rischio 1%/trade.

## Perché è `edge-confirmed` (passa i test che donchian e fx_meanrev fallirono)
Fonte: `raw/exp_2026-07-12_gold_trend.json`.
- **Solo-long, canonico**: PF **1,76** (ch20) → **2,32** (ch40), Sharpe **~0,65**,
  **maxDD −8%**, OOS positivo.
- **Sensibilità canale 10-70: PF 1,47…2,45, tutti >1,4** → non è un parametro fortunato,
  è tutto il vicinato (test anti-overfitting decisivo).
- **Due metà (ch55)**: PF 1,67 / 2,72, Sharpe +0,47 / +0,80 → entrambe forti.
- **OOS temporale**: train → OOS **migliora** (ch20 1,52→2,06; ch55 1,51→**3,60**). Il
  contrario dell'overfitting.

## Il confronto onesto con "compra e tieni"
Il buy&hold dell'oro (2003-2026) ha fatto Sharpe 0,61 / CAGR +8,8% ma con **maxDD −45%**
(il crollo 2011-2015). Il trend solo-long fa **lo stesso Sharpe (0,63)** con **maxDD −8%**
— cinque volte e mezzo più piccolo. **Questo è il valore**: non più rendimento del
tenere l'oro, ma lo stesso rendimento risk-adjusted con un drawdown enormemente minore,
in forma sistematica e **decorrelata** dagli altri sleeve.

## Verdetto corrente
`edge-confirmed`. **Secondo edge robusto del progetto** (dopo [[rsi2_meanrev]]), su un
asset e uno stile **diversi** (oro/trend vs indici/mean-reversion) → forte
diversificazione. **Cautele load-bearing:**
- **~~Single-instrument~~ → SUPERATO (2026-07-12):** la cautela "argento non conferma"
  valeva per il long/**short**. In **solo-long** l'argento (e WTI/Brent/rame) confermano →
  vedi [[commodity_trend]]: c'è un **paniere** trend, non un caso isolato. L'oro resta il
  membro più robusto (entrambe le metà forti). Rischio residuo: cambio strutturale di
  regime dell'oro (fine era debasement/acquisti CB).
- **Long-only ⇒ rende a scatti**: concentrato nei tori dell'oro, **piatto (fuori
  mercato) nei bear** tipo 2011-2015. Sidesteppa i crolli (per questo maxDD −8%) ma non
  guadagna quando l'oro scende.
- **Modesto senza leva** (~2,7% CAGR): come gli altri, il valore è risk-adjusted +
  decorrelazione; scala con la leva (e con essa il rischio).

## Ruolo nel sistema
Terzo sleeve del sistema multi-edge, decorrelato da indici-MR e forex-MR. Sostituisce
l'`oro_trend` grezzo (ma-cross return-based) usato finora nella combinazione: ora è
**trade-level e long-only**, quindi il suo peso nel portafoglio non è più "soft".

## Prossimo passo (gate §5)
`paper` su demo IBKR, come per [[rsi2_meanrev]]. È il candidato naturale come **secondo
modulo del bot** (indici-MR + oro-trend, decorrelati), molto più solido di [[fx_meanrev]].
