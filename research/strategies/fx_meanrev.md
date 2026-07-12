---
type: strategy
status: edge-confirmed
tags: [mean-reversion, forex, daily, rsi2, market-neutral]
updated: 2026-07-11
links: ["[[rsi2_meanrev]]", "[[exp_2026-07-11_fx_meanrev]]", "[[EUR_USD]]"]
---
# fx_meanrev (mean-reversion sui forex major)

## Idea
Le valute non hanno drift direzionale come gli indici: oscillano, tornano verso la
media nel breve. Quindi un mean-reversion **simmetrico** (compra l'ipervenduto, vendi
l'ipercomprato, **senza** filtro di trend) coglie il rientro. È il "cugino FX" di
[[rsi2_meanrev]] (che invece è long-only sugli indici, sfruttandone il drift).

## Regole (canoniche, poche)
- **Long** se RSI(2) < oversold (~10); **short** se RSI(2) > (100−oversold) (~90).
- **Uscita** quando RSI(2) rientra oltre `exit_level` (~50).
- Daily, sui 7 major: EUR/GBP/AUD/NZD/USD-CHF/USD-CAD/USD-JPY. Simmetrico (no drift).

## Perché è `edge-confirmed` (stessa qualità di rsi2_meanrev)
Fonte: `raw/exp_2026-07-11_fx_meanrev.json`.
- Nello sweep, **7/7 major positivi** (Sharpe +0,09…+0,35). Oro/argento negativi sul
  MR (vogliono trend) → esclusi.
- **Portafoglio 7 major**: Sharpe **0,57**, maxDD −8,9%, **due metà positive** (0,73/0,39).
- **Sensibilità parametri: 12/12 combinazioni positive** (Sharpe 0,24–0,57) → robusto.
- **OOS temporale: 0,51 → 0,68** (migliora fuori campione).

## Verdetto corrente
`edge-confirmed`. **Secondo edge del progetto**, market-neutral, su una classe diversa
(valute) → **diversifica** rispetto agli indici. **Cautele:**
- **Modesto**: Sharpe 0,57, CAGR ~1,2% senza leva. Il FX si opera in leva → il
  rendimento scala (e con esso il rischio). Il valore vero è la **diversificazione** +
  bassa correlazione con l'edge sugli indici.
- Idea **nota** (mean-reversion FX di breve) → possibile affollamento.
- Validazione a livello di **serie di rendimenti** (posizione ±1). Prossimo passo:
  backtest **trade-by-trade** con l'engine (stop, sizing, costi realistici) come per
  [[rsi2_meanrev]], poi paper.

## Nota: l'oro va in un binario separato
[[XAU_USD]] è **negativo** sul mean-reversion e **positivo** su momentum/trend → l'oro
vuole **trend-following**, non MR. Lead separato da sviluppare (strategia trend su oro).

## Prossimo passo (gate §5)
Backtest trade-level con l'engine + eventuale paper. Poi valutare se aggiungerlo al bot
come secondo modulo (portafoglio indici-MR + forex-MR, decorrelati).
