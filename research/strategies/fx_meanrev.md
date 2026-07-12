---
type: strategy
status: testing
tags: [mean-reversion, forex, daily, rsi2, market-neutral, cost-fragile]
updated: 2026-07-12
links: ["[[rsi2_meanrev]]", "[[exp_2026-07-11_fx_meanrev]]", "[[exp_2026-07-12_fx_meanrev_tradelevel]]", "[[EUR_USD]]"]
---
# fx_meanrev (mean-reversion sui forex major)

> **AGGIORNAMENTO 2026-07-12 — DECLASSATO da `edge-confirmed` a `testing`.** Il backtest
> trade-level ([[exp_2026-07-12_fx_meanrev_tradelevel]]) ha rivelato che l'edge è
> **marginale e fragile ai costi**: muore a 2× le frizioni, con lo swap ancora non
> modellato. Vale solo come sleeve diversificante, non standalone. Dettagli in fondo.

## Idea
Le valute non hanno drift direzionale come gli indici: oscillano, tornano verso la
media nel breve. Quindi un mean-reversion **simmetrico** (compra l'ipervenduto, vendi
l'ipercomprato, **senza** filtro di trend) coglie il rientro. È il "cugino FX" di
[[rsi2_meanrev]] (che invece è long-only sugli indici, sfruttandone il drift).

## Regole (canoniche, poche)
- **Long** se RSI(2) < oversold (~10); **short** se RSI(2) > (100−oversold) (~90).
- **Uscita** quando RSI(2) rientra oltre `exit_level` (~50).
- Daily, sui 7 major: EUR/GBP/AUD/NZD/USD-CHF/USD-CAD/USD-JPY. Simmetrico (no drift).

## La validazione return-based (2026-07-11) — poi ridimensionata dal trade-level
> Questa sezione documenta perché era sembrato `edge-confirmed`. Il backtest trade-level
> (in fondo) l'ha poi **declassato**: leggila alla luce di quello.
Fonte: `raw/exp_2026-07-11_fx_meanrev.json`.
- Nello sweep, **7/7 major positivi** (Sharpe +0,09…+0,35). Oro/argento negativi sul
  MR (vogliono trend) → esclusi.
- **Portafoglio 7 major**: Sharpe **0,57**, maxDD −8,9%, **due metà positive** (0,73/0,39).
- **Sensibilità parametri: 12/12 combinazioni positive** (Sharpe 0,24–0,57) → robusto.
- **OOS temporale: 0,51 → 0,68** (migliora fuori campione).

## Verdetto corrente: `testing` (era edge-confirmed, declassato — vedi trade-level in fondo)
Market-neutral, su una classe diversa (valute) → **diversifica** rispetto agli indici.
Questo valore di diversificazione **regge** (return-based, decorrelato). Ma come edge
**a sé** è marginale. **Cautele:**
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

## Backtest trade-level (2026-07-12) — CONTRADDICE la lettura return-based
Fonte: `raw/exp_2026-07-12_fx_meanrev_tradelevel.json`. Codice: `src/backtest/fx_meanrev.py`.
Passando dalla serie di rendimenti (±1) a trade veri (stop ATR, sizing 1%, spread per coppia):
- **6/7 positivi** ma PF mediano solo **1,07**, diversi appena sopra 1,0, exp_R **minuscolo**
  (+0,001…+0,023R). GBP 1,01, AUD 1,00 (break-even).
- **Sharpe portafoglio 0,31** (vs 0,57 return-based: costi+stop lo **dimezzano**),
  **maxDD −27%**, due metà **0,46 / 0,17** (edge in **decadimento** recente).
- ✅ Robusto ai parametri (27/27) e all'OOS (1,04→1,07). ❌ Solo 5/7 stabile nelle due metà.
- **Fragilità ai costi (decisiva):** hold medio 3,4 gg → lo **swap non è modellato**.
  A **2× le frizioni l'edge svanisce** (PF 1,01). 2× è plausibile su forex retail multi-day.

**Verdetto:** edge **reale ma marginale e cost-fragile**. Nettamente più debole di
[[rsi2_meanrev]] (PF 1,08–2,57, maxDD −8%). **NON standalone, NON paper standalone.**

## Prossimo passo (gate §5)
- Resta come **sleeve diversificante** nel sistema multi-edge (return-based, decorrelato),
  sizing **conservativo** — è lì che dà valore, non da solo.
- Se un giorno lo si volesse tradare: prima **modellare lo swap** e ripetere il trade-level;
  solo se regge con swap incluso ha senso il paper. Oggi **non** è quel caso.
