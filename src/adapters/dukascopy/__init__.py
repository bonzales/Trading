"""Adapter dati Dukascopy — storico gratuito e profondo per la RICERCA.

IBKR resta il broker di esecuzione (ordini, paper, live). Per i dati storici di
backtest usiamo Dukascopy: gratis, senza conto, profondo ~20+ anni, scaricabile
da qualsiasi macchina (anche da questo ambiente cloud, senza Gateway acceso).
L'architettura del progetto separa apposta il livello DATI da quello ESECUZIONE.
"""
