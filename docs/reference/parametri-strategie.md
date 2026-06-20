# Reference — Parametri delle strategie

> Modalità: *reference*. Parametri configurabili. Le strategie sono portate dal
> progetto Kraken; ogni `Signal(side, price, atr, ...)` usa la stessa gestione di
> uscita (stop ATR + TP1 parziale + trailing) salvo dove indicato.

## pullback (default)
| Parametro        | Significato                                  |
|------------------|----------------------------------------------|
| `ema_fast/slow`  | trend filter (es. 20/50)                     |
| `rsi_band`       | banda RSI di ingresso                         |
| `macd_mode`      | `state` o `cross`                             |
| `min_conditions` | quante condizioni richieste per entrare       |

## breakout
Rottura del massimo/minimo degli ultimi N (Donchian) + filtro EMA.

## meanrev
RSI ipervenduto + momentum MACD + volume > media → rimbalzo.

## ichimoku
Prezzo sopra/sotto la nuvola + Tenkan/Kijun.

## Gestione del rischio (comune)
Sizing, stop ATR (mult configurabile), TP1 parziale + breakeven, trailing step,
limite di perdita giornaliera. **Adattare a forex**: lot size, pip value, leva ESMA.
