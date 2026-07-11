# Paper trading sul VPS — guida

Obiettivo: far girare, sul tuo VPS Hetzner, **IB Gateway 24/7** (login automatico) +
il **bot mean-reversion** che ogni sera opera sul conto **paper**. Tutto automatico.

> Le credenziali le inserisci TU sul VPS, in due file locali. Non finiscono mai nella
> repo (sono git-ignored). Non incollarle in chat.

## 0. Prerequisiti
- Un VPS Ubuntu/Debian (Hetzner va benissimo), accesso `ssh`/`sudo`.
- Il conto **paper** IBKR attivo (username + password) e il numero conto `DU…`.

## 1. Porta il progetto sul VPS
```bash
ssh root@IL_TUO_VPS
git clone <URL_DELLA_REPO> Trading   # o il branch che stiamo usando
cd Trading
```

## 2. Lancia l'installazione (una volta)
```bash
sudo bash deploy/setup_vps.sh
```
Installa Java, IB Gateway (headless), IBC, l'ambiente Python e i servizi systemd.
Se una versione non combacia (IBC/Gateway cambiano spesso), me lo dici e la sistemo.

## 3. Inserisci le credenziali (due file, solo sul VPS)
**a) Login del Gateway** → `/opt/ibc/config/config.ini`:
```ini
IbLoginId=IL_TUO_UTENTE_PAPER
IbPassword=LA_TUA_PASSWORD_PAPER
TradingMode=paper
```
**b) Config del progetto** → `.env` (nella cartella Trading):
```bash
cp .env.example .env
nano .env      # IBKR_ACCOUNT_ID=DU...   IBKR_ENV=practice   IBKR_PORT=4002
```

## 4. Avvia il Gateway e verifica
```bash
sudo systemctl enable --now ib-gateway
journalctl -u ib-gateway -f          # deve loggarsi e restare su (Ctrl-C per uscire)
```

## 5. Prova a secco (nessun ordine)
```bash
./.venv/bin/python -m src.live.paper_bot --dry-run
```
Mostra le decisioni di oggi sui 5 indici. Se le vedi, la logica gira.

## 6. Primo test reale sul paper
```bash
./.venv/bin/python -m src.live.paper_bot       # opera sul conto paper
```
Controlla su IBKR (o con un dry-run il giorno dopo) che posizioni/ordini siano coerenti.
`raw/live_log.csv` tiene il registro di ogni decisione.

## 7. Attiva l'automazione giornaliera
```bash
sudo systemctl enable --now paper-bot.timer
systemctl list-timers paper-bot.timer          # verifica la prossima esecuzione (22:30 Berlin)
```

## Cose da verificare DAL VIVO (importante, è lo scopo del paper)
- **`point_value` dei CFD**: in `src/live/paper_bot.py` è un placeholder (1.0). Al primo
  ordine reale controlla la grandezza della posizione e me lo dici: taro il sizing giusto.
- **Simboli CFD**: `IBUS500/IBUST100/IBUS30/IBGB100/IBDE40` in `execution.py`. Se IBKR non
  li riconosce, dal log si vede e li correggo.
- **2FA**: i conti paper di solito non la chiedono. Se il tuo la chiede, il login headless
  non parte: scrivimi e troviamo l'alternativa.

## Se qualcosa non va
Mandami l'output di `journalctl -u ib-gateway -n 50` e del comando `--dry-run`: dai log
capisco e correggo. Niente credenziali negli incolla, solo l'output tecnico.
