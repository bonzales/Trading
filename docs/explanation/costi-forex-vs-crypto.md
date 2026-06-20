# Costi: forex/CFD vs crypto

> Modalità: *explanation*. Perché il modello di costo cambia rispetto a Kraken, e
> perché ignorarlo falsa i backtest.

## Crypto (Kraken): commissioni percentuali

Su Kraken il costo era una **commissione taker** in percentuale sul controvalore, più
costi di margine (apertura + rollover) per le posizioni a leva. Semplice da modellare.

## Forex/CFD (OANDA): spread + swap

Qui il costo ha due componenti diverse, ed entrambe vanno modellate o i risultati
mentono:

- **Spread** — la differenza bid/ask. È il costo che paghi *a ogni* apertura/chiusura.
  Variabile: si allarga su news, in apertura/chiusura sessione, sugli strumenti meno
  liquidi. Un backtest che assume spread fisso e stretto è ottimista in modo pericoloso.
- **Swap (rollover notturno)** — il costo/credito per tenere una posizione overnight,
  funzione del differenziale tassi delle due valute. Su posizioni tenute giorni conta
  parecchio. Può essere negativo *o* positivo a seconda della direzione.

## Le altre differenze che il motore deve sapere

- **Orari di mercato.** Il forex non è 24/7: chiude nel weekend, ha sessioni
  (Londra/NY/Tokyo) con liquidità e volatilità diverse, e ci sono i festivi. Il
  sistema deve sapere quando il mercato è aperto, e gestire i **gap del weekend**
  (il prezzo del lunedì può aprire lontano dalla chiusura del venerdì → uno stop può
  saltare oltre il livello).
- **Caratteristiche per-strumento.** Pip value, contract size, margine richiesto
  cambiano per ogni strumento. Vanno parametrizzati per asset, non assunti uguali.
- **Leva regolamentata UE (ESMA).** Retail: 30:1 sui major forex, 20:1 sugli indici
  principali. Tenerne conto nel sizing.

## Conseguenza pratica

Nel modello di backtest, sostituisci "commissione %" con "spread (variabile) + swap
(per notte) + eventuale commissione OANDA". Ogni pagina in `research/instruments/`
dovrebbe registrare i parametri di costo reali osservati per quello strumento.
