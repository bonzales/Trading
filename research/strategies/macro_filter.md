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

## Verdetto: filtro di RISCHIO, non predittore di direzione
`testing`. L'effetto sulla **volatilità** è reale e universale → uso corretto: **filtro di
rischio**. Nei giorni ad alto impatto: ridurre la size / allargare gli stop / non aprire
nuove posizioni. È quello che fa un professionista: non "indovinare il dato", ma **non
farsi sorprendere**. Helper: `size_multiplier(is_event_day, damp=0.5)`.

**Non** è un segnale direzionale (quello richiederebbe un dataset di consenso, a pagamento/
scraping — non ancora disponibile).

## Limiti onesti
- Solo **NFP** è derivabile senza dati esterni. **FOMC/CPI/BCE** richiedono un elenco date
  (CSV opzionale `raw/cache/macro_events.csv`) — da popolare.
- Il **valore aggiunto va dimostrato**: ridurre la size sugli eventi migliora davvero
  Sharpe/drawdown del sistema? È il prossimo test, non un dato di fede.

## Prossimo passo (gate §5)
1. Testare se il filtro (size ridotta sugli eventi) **migliora** le metriche degli edge
   confermati ([[rsi2_meanrev]], [[commodity_trend]]).
2. Diventa un **mattoncino del generatore**: il motore notturno può testare varianti
   con/senza filtro macro e vedere se aggiunge valore, con la watchlist a fare da giudice.
3. Se si vuole la **direzione**: decidere se procurarsi i dati di consenso (costo/fragilità).
