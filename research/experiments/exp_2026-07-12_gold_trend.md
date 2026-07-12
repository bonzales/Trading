---
type: experiment
status: edge-confirmed
tags: [oro, argento, trend-following, donchian, trade-level, daily]
updated: 2026-07-12
links: ["[[gold_trend]]", "[[fx_meanrev]]", "[[exp_2026-07-11_fx_meanrev]]", "[[XAU_USD]]"]
raw: ["raw/exp_2026-07-12_gold_trend.json"]
---
# Exp 2026-07-12 — oro trend-following trade-level

## Perché
Il lead "l'oro vuole trend, non mean-reversion" era emerso return-based da
[[exp_2026-07-11_fx_meanrev]]. Qui il **gate trade-level**: motore reale (stop ATR +
TP1 + trailing, costi), Donchian breakout su XAU_USD (~20y), con XAG_USD come **conferma
indipendente**. **Fonte:** `raw/exp_2026-07-12_gold_trend.json`.

## Scoperta chiave: solo-long ≫ long/short
| Oro, canale | versione | PF | Sharpe | maxDD | ret |
|-------------|----------|-----|--------|-------|-----|
| ch20 | long/short | 1,29 | +0,35 | −10% | +42% |
| ch20 | **solo-long** | **1,76** | **+0,63** | −8% | +67% |
| ch55 | long/short | 1,43 | +0,35 | −8% | +33% |
| ch55 | **solo-long** | **2,14** | **+0,63** | −8% | +55% |

Gli short remano contro il drift rialzista secolare dell'oro. Stessa lezione degli indici
([[rsi2_meanrev]] è long-only): **asset con drift → long-only**.

## Gate solo-long — passa tutto
- **Sensibilità canale**: ch10→70 PF **1,47 / 1,76 / 1,96 / 2,32 / 2,14 / 2,45** — tutti
  >1,4 (Sharpe 0,52–0,71). Robusto sull'intero vicinato.
- **Due metà (ch55)**: PF 1,67 / 2,72, Sharpe +0,47 / +0,80 — entrambe forti.
- **OOS temporale**: ch20 train 1,52 → OOS 2,06; ch55 train 1,51 → OOS **3,60**. OOS
  **migliora** → contrario dell'overfitting.

## Buy&hold: il confronto onesto
B&H oro: Sharpe 0,61, CAGR +8,8%, **maxDD −45%**. Il solo-long eguaglia lo Sharpe (0,63)
con **maxDD −8%** (5,6× più piccolo). Il valore non è più rendimento del tenere l'oro, è
lo **stesso risk-adjusted con un drawdown enormemente minore**, sistematico e decorrelato.

## Argento: NON conferma (caution)
XAG_USD: PF 0,86, Sharpe −0,15, due metà 0,77/0,83, sensibilità instabile, OOS 0,92.
Il trend **non regge** sull'argento (metà industriale, più whippy). Conseguenza:
l'edge è **gold-specifico**, non "metalli preziosi". È single-instrument → il rischio
principale è un cambio di regime strutturale dell'oro.

## Verdetto + gate
**`edge-confirmed`** per [[gold_trend]] (solo-long, canale ~40-55). Secondo edge robusto
del progetto, su asset+stile diversi → decorrelato. Nettamente più solido di
[[fx_meanrev]] (che il trade-level aveva declassato). Strategia registrata: `donchian_long`.
Prossimo gate: **paper**, candidato come 2° modulo del bot.
