# Come andare live

> Modalità: *how-to*. Prerequisiti NON negoziabili: backtest profondo su dati veri +
> walk-forward positivo + paper trading coerente. Se manca anche uno solo, non sei
> pronto. Vedi `explanation/scala-o-scarta.md`.

1. Conferma lo status `paper` con risultati coerenti nella pagina della strategia.
2. Usa **solo denaro che ti puoi permettere di perdere**. Con 100-500€ e leva ESMA
   sei al limite del rischio di ruin: il sizing dev'essere conservativo.
3. Crea un `.env` live separato con le credenziali del conto reale OANDA (mai
   committato, `chmod 600`).
4. Nuovo service file systemd sul VPS Hetzner (riuso dell'infrastruttura Kraken,
   cambi `ExecStart` e le credenziali).
5. Parti con sizing ridotto rispetto al backtest. Monitora da Telegram (`/status`,
   `/report`).
6. Il limite di perdita giornaliera deve essere attivo e mettere in pausa il bot.

Ricorda: aumentare il capitale non sistema una strategia debole, moltiplica le
perdite. Il live non è il momento per "spingere".
