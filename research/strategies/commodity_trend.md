---
type: strategy
status: edge-confirmed
tags: [trend-following, commodity, oro, argento, energia, rame, long-only, regime-dipendente]
updated: 2026-07-12
links: ["[[gold_trend]]", "[[rsi2_meanrev]]", "[[donchian]]", "[[exp_2026-07-12_commodity_trend]]", "[[XAU_USD]]"]
---
# commodity_trend (trend-following solo-long su un paniere di materie prime)

## Idea
Le materie prime **tendono** (offerta/domanda rigide, cicli, shock geopolitici) e hanno
drift di lungo periodo → come l'oro, vogliono **trend-following solo-long** (gli short
remano contro; il MR è negativo). Generalizzazione di [[gold_trend]] da un solo strumento
a un **paniere diversificato**: oro, argento, WTI, Brent, rame. Il gas è escluso (stagionale,
non tende: PF 0,61). Strategia: `donchian_long` (canale ~40-55) sul motore trade-level.

## Perché è `edge-confirmed` (a livello di PORTAFOGLIO) — ma con un caveat load-bearing
Fonte: `raw/exp_2026-07-12_commodity_trend.json`.
- **5/5 mercati positivi** (PF 1,46–2,32, mediano 1,62), ~3-4 trade/anno ciascuno.
- **Portafoglio paniere**: **Sharpe 0,71, maxDD −4%** (diversificazione ottima), CAGR
  modesto, **entrambe le metà positive** (+0,35 / +0,95).
- OOS temporale: **tutti migliorano** (train→OOS, es. Brent 1,10→3,41).
- **Diverso da [[donchian]]** (che era PIATTO e fu ritrattato): qui è **long-only** + le
  commodity tendono davvero → non è lo stesso errore.

## Il caveat che NON nascondo: è REGIME-DIPENDENTE
- **Stabilità due-metà: solo 2/5.** Oro e argento reggono entrambe le metà (nucleo solido).
  **WTI, Brent, rame** hanno la **prima metà debole/piatta** (bear commodity 2012-2019) e
  la seconda fortissima → l'edge non-oro è **concentrato nel decennio recente**.
- Buona parte della forza OOS coincide col **supertrend inflazionistico 2020-22**
  (COVID, guerra): regime reale, ma scommettere che si ripeta è la trappola di donchian.
  **Non sovrappesare energia/rame** su questa base.
- Long-only trend = **feast-or-famine**: guadagna nei tori commodity, tratta acqua (piccole
  perdite) nei bear/range. Rendimento **a scatti**, dipende dall'esistenza di trend.

## Verdetto corrente
`edge-confirmed` a livello di **paniere/portafoglio** (Sharpe 0,71, maxDD −4%, due metà
positive), con il **nucleo robusto = oro+argento** e **energia/rame = più deboli/recenti**
(`testing` se presi standalone). Il valore vero è la **diversificazione** e il **drawdown
minuscolo**, non il rendimento assoluto. Terzo sleeve del sistema multi-edge, decorrelato
da indici-MR e forex-MR.

## Rapporto con [[gold_trend]]
[[gold_trend]] resta la pagina dell'oro standalone (il membro più robusto, entrambe le metà
forti). Questa pagina è il **paniere**. La scoperta che unisce le due: il fix **solo-long**
(trovato sull'oro) fa **generalizzare** il trend anche all'argento e all'energia — quindi
la vecchia cautela "oro single-instrument" è **superata**: c'è un paniere, non un caso isolato.

## Prossimo passo (gate §5)
- Sostituire nel sistema multi-edge l'`oro_trend` grezzo con questo **paniere trade-level**.
- Eventuale `paper` come modulo commodity del bot, sizing **conservativo** su energia/rame
  (regime-dipendenti). Prima però: il fattore **COT** potrebbe filtrare bene proprio le
  commodity (posizionamento commercials) → testare se aggiunge potere.
