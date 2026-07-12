---
type: strategy
status: testing
tags: [macro, fattore, rischio, filtro, volatilita, nfp, fondamentale]
updated: 2026-07-12
links: ["[[cot_factor]]", "[[rsi2_meanrev]]", "[[commodity_trend]]"]
---
# macro_filter (eventi macro come filtro di rischio)

## Idea
Le notizie macro ad alto impatto (NFP, FOMC, CPI, BCE) muovono i mercati. La domanda
onesta: cosa possiamo **davvero** catturare? Due cose molto diverse:
- **Quando** esce il dato → la **volatilità sale**. Derivabile, robusto, gratis.
- **In che direzione** → serve il **consenso** (actual vs atteso), dato non disponibile gratis.

Codice: `src/adapters/macro/` (calendario derivabile + event-study + filtro size).

## Cosa dice il test (robusto)
Fonte: `raw/exp_2026-07-12_macro_nfp.json`. Effetto delle **buste paga USA (NFP** = primo
venerdì del mese, derivato senza dati esterni) sulla volatilità giornaliera:
- **14/14 strumenti** hanno volatilità più alta nei giorni NFP. Rapporto sempre **> 1,14×**,
  fino a **1,75×** (USD/JPY), 1,48× (rame), 1,41× (argento), 1,32× (EUR), 1,27× (oro).
- La **direzione** invece è **rumorosa**: il rendimento medio nei giorni NFP non è
  distinguibile → **non predicibile** senza il dato di consenso.

## Il test del valore aggiunto — NEGATIVO per i nostri edge
Ho testato se ridurre la size sui giorni NFP **migliora** gli edge confermati (return-based):
| damp NFP | MR indici Sharpe | Trend commodity Sharpe |
|----------|------------------|------------------------|
| 1,0 (nessun filtro) | **0,566** | **0,527** |
| 0,5 | 0,556 | 0,519 |
| 0,0 | 0,539 | 0,503 |

**Più si taglia, peggio va lo Sharpe** su entrambi. Il drawdown scende un filo
(−12,9%→−11,9%) ma non compensa la perdita di rendimento. **Ragione:** sono strategie
**daily** che tengono la posizione attraverso l'evento; la vol NFP è simmetrica e l'edge
ci guadagna anche in quei giorni. Tagliare la size rimuove esposizione dove c'è comunque
valore atteso positivo.

## Verdetto: effetto reale, ma filtro NON integrato (non aiuta il sistema attuale)
`testing`. L'effetto sulla **volatilità** è reale e universale (14/14), ma il filtro
"riduci size sugli eventi" **non migliora** gli edge daily confermati → **non lo
agganciamo** al sistema. Onestamente testato e scartato per ora. Avrebbe senso solo per:
- strategie **intraday** (che non abbiamo — sono fallite), dove lo spike conta *dentro* la giornata;
- un segnale **direzionale**, che richiederebbe dati di **consenso** (a pagamento/scraping).

Il calendario + event-study + `size_multiplier` restano **infrastruttura pronta** per
quando (e se) si aprirà uno di quei due scenari.

## Limiti onesti
- Solo **NFP** è derivabile senza dati esterni. **FOMC/CPI/BCE** richiedono un elenco date
  (CSV opzionale `raw/cache/macro_events.csv`) — da popolare.
- Il **valore aggiunto va dimostrato**: ridurre la size sugli eventi migliora davvero
  Sharpe/drawdown del sistema? È il prossimo test, non un dato di fede.

## Prossimo passo (gate §5)
Il value-add è stato testato e **scartato** per gli edge daily. Riprenderlo **solo** se:
1. emergono strategie **intraday** (lì lo spike macro conta davvero, dentro la giornata);
2. si procurano dati di **consenso** per il segnale direzionale (decisione costo/fragilità).
Fino ad allora, calendario ed event-study restano infrastruttura, non un ingranaggio attivo.
