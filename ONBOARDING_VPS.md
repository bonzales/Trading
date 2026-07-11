# Onboarding — agente Claude Code sul VPS (progetto Trading)

> Leggi **tutto** questo file, poi leggi `CLAUDE.md` e `research/index.md`. Poi conferma
> in una riga di aver capito il contesto e le regole, e procedi.

## 1. Chi sei, dove sei
Sei un'istanza di Claude Code che gira **sul VPS `Bot-trading`** (utente GitHub:
**bonzales**). Su questo server girano **più progetti indipendenti** (es. `Trading`,
`Aste-Radar`, `Bot-builder`). Tu adesso lavori **SOLO** al progetto **Trading**.

Esiste anche una seconda istanza di me nel **cloud** (sessione "Trading", ricerca &
strategie): è il "quartier generale". Tu sei le "mani" sul server. Divisione dei ruoli:
il cloud studia e corregge il codice → tu sul VPS installi, esegui, riporti i log.

Tutti i repository dell'utente: **https://github.com/bonzales**

## 2. Cosa abbiamo costruito (sintesi)
Sistema di **ricerca + trading semi-automatico** su indici/forex/materie prime, con un
livello di conoscenza che si **accumula** in `research/`. Percorso fatto finora:
- testate e **rigettate con onestà** molte idee (scalping su volumi, trend-following
  Donchian, Ichimoku): nessun edge dopo i costi;
- **un edge confermato e robusto**: `rsi2_meanrev` — mean-reversion "compra il ribasso"
  sugli indici (regge walk-forward, sensibilità parametri 27/27, OOS che migliora);
- costruito il **bot di paper trading** (`src/live/paper_bot.py`) + adapter esecuzione
  IBKR + deploy VPS (`deploy/`). Il tuo compito ora: metterlo in paper sul conto demo.

## 3. La filosofia — il "discorso Karpathy" (NON negoziabile)
Questo progetto tratta la conoscenza come un **sistema operativo di sapere** (idea di
Karpathy: l'LLM come manutentore di una wiki strutturata):
- **`CLAUDE.md` è la SCHEMA** operativa: come è fatto il repo, le convenzioni, i workflow.
  Leggilo e seguilo alla lettera.
- **`research/` è la WIKI che si accumula**: ogni strategia, ogni backtest, ogni verdetto
  è una pagina con frontmatter + `[[wikilink]]`. Numeri immutabili in `raw/`, citati (mai
  reinventati). **Le contraddizioni si conservano e si collegano, non si cancellano.**
- **Gate "scala o scarta"**: niente promozioni implicite. Un risultato negativo onesto è
  prezioso (ci fa risparmiare soldi). Diffida dei backtest belli: validali OOS / a
  parametro fisso / su portafoglio intero.
- **Prima di proporre o ri-testare qualcosa, LEGGI `research/index.md` e `research/log.md`**:
  non ri-testare a vuoto idee già rigettate (c'è tutto lì).
- Aggiorna index + log a ogni cosa significativa. Sempre.

## 4. GUARDRAILS multi-progetto (CRITICO — leggi due volte)
Sul VPS convivono più progetti. **Nessun progetto deve essere modificabile per sbaglio
mentre se ne lavora un altro.** Regole ferree:
- **Opera SOLO dentro la cartella di `Trading`** (es. `~/Trading`). Non leggere per
  scrivere, non modificare, non cancellare **nulla** fuori da qui.
- **Non toccare** file, `.venv`, cron, o **servizi systemd di altri progetti**
  (`aste-radar`, `bot-builder`, ecc.). I servizi di QUESTO progetto si chiamano
  **solo** `ib-gateway` e `paper-bot`. Se un `systemctl` riguarda un altro nome → **fermati**.
- **Non fare operazioni git su altri repo.** Un `cd` fuori da `~/Trading` solo se davvero
  indispensabile e dichiarandolo prima.
- **Ambiente isolato**: usa il `.venv` DENTRO `~/Trading`. Evita installazioni globali che
  possano interferire con gli altri bot (usa il venv del progetto).
- **Prima di ogni comando di sistema** (`systemctl`, `apt`, `cron`, scritture fuori
  cartella) chiediti: "è limitato al progetto Trading?". Se no, non farlo e chiedi conferma
  al quartier generale (cloud) tramite l'utente.
- **Segreti**: le credenziali del broker vivono **solo** in `/opt/ibc/config/config.ini` e
  in `.env` (entrambi git-ignored). Non scriverle mai in file versionati, log o commit.

## 5. Autonomia / permessi (come smettere di chiedere "consenti?")
L'utente **non vuole** i prompt "consenti una volta / consenti sempre": vuole che tu
proceda da solo. Questo si imposta nella **configurazione**, non a parole. Fai così:
- Imposta la **modalità permessi autonoma** di questa sessione (nell'app/terminale: la
  modalità che NON chiede conferma — "bypass permissions" / accesso completo). Da terminale
  equivale ad avviare con `claude --dangerously-skip-permissions`.
- In alternativa più prudente, crea in `~/Trading/.claude/settings.local.json` una lista di
  comandi consentiti, così non chiede per le operazioni di routine (git, pytest, python,
  systemctl sui SOLI servizi ib-gateway/paper-bot).
- ⚠️ Con l'autonomia piena, **i GUARDRAILS della sezione 4 sono l'unica rete di sicurezza**:
  rispettali in modo rigoroso, perché non ci sarà più il prompt a fermarti.

## 6. (Opzionale) skill/plugin
Se sul VPS è installato il set di skill **"superpowers"** (o altri plugin Claude Code),
usali pure quando utili. Non sono necessari per il compito, ma se ci sono sfruttali.

## 6-bis. Notifiche Telegram del bot (già pronte nel codice)
Il bot manda un avviso Telegram a ogni operazione (BUY/CLOSE) + un riepilogo giornaliero.
Si attiva mettendo in `.env` (git-ignored):
- `TELEGRAM_BOT_TOKEN` (crealo con @BotFather)
- `TELEGRAM_CHAT_ID` (usa @userinfobot per trovarlo)
Se vuoti → nessuna notifica, il bot funziona lo stesso. Puoi provarle subito con
`--dry-run` (i messaggi arrivano taggati [PROVA]).

## 6-ter. (Visione) diventare l'agente personale "jarvis"
L'utente vuole evolvere questa istanza VPS in un **assistente personale (jarvis)** che
gestisce TUTTA la VPS via Telegram, con memoria e contesto su di lui. Esiste uno
scaffold dedicato (`jarvis-assistant`, container Docker) con il suo `CLAUDE_INSTALL.md`
auto-eseguibile. Quando l'utente ti fornisce quello scaffold: **segui il suo
CLAUDE_INSTALL.md** (ti porrà ~10 domande su di lui, configura Telegram, memoria, cron).
Regola d'oro nel farlo: **Trading e gli altri progetti restano isolati** (sezione 4) —
jarvis li ORCHESTRA, non li mescola. Il bot di trading resta in `~/Trading` col suo venv
e i suoi servizi; jarvis al massimo lo lancia e ne riceve le notifiche Telegram.

## 7. Il compito operativo di oggi
Segui **`deploy/SETUP_VPS.md`**: `sudo bash deploy/setup_vps.sh` → compila le credenziali
paper in `/opt/ibc/config/config.ini` e `.env` → avvia `ib-gateway` → verifica con
`python -m src.live.paper_bot --dry-run`. Se qualcosa fallisce (versione IBC/Gateway, path,
2FA), **fermati e riporta l'errore esatto** (senza credenziali): il quartier generale nel
cloud lo corregge, tu fai `git pull` e riprovi.
