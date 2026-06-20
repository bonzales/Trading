# CLAUDE.md — Schema operativo del progetto

> Questo file è la **schema** nel senso di Karpathy (LLM-Wiki): dice all'agente
> com'è strutturato il repository, quali sono le convenzioni e quali workflow
> seguire. Non è documentazione per l'umano (quella sta in `docs/`, organizzata
> secondo Diátaxis). Questo file rende l'agente un **manutentore disciplinato**
> della conoscenza di ricerca, non un assistente generico.
>
> Leggi questo file all'inizio di ogni sessione. Aggiornalo quando cambiano le
> convenzioni: tu e l'utente lo fate co-evolvere nel tempo.

---

## 0. In una frase

Sistema di **backtesting e trading semi-automatico su OANDA** (forex, indici,
materie prime) con un **livello di conoscenza che si accumula**: ogni strategia
testata, ogni risultato walk-forward, ogni decisione "scala o scarta" viene
archiviata e collegata in `research/`, così non si ri-testa mai la stessa idea
perdente due volte.

Erede del primo progetto (bot crypto su Kraken). Vedi `docs/explanation/` per le
lezioni apprese — sono il capitale più prezioso che porta avanti questo progetto.

---

## 1. I tre livelli (architettura della conoscenza)

```
raw/        →  Sorgenti IMMUTABILI. Output grezzi dei backtest (CSV, JSON,
               equity curve), dati storici scaricati, log di esecuzione.
               L'agente LEGGE da qui ma NON modifica mai questi file.
               Questa è la fonte di verità: i numeri non si toccano.

research/   →  LA WIKI. Markdown generato e mantenuto DALL'AGENTE.
               Pagine strategia, pagine strumento, pagine esperimento,
               un index e un log. L'agente possiede interamente questo livello.
               Tu lo leggi, l'agente lo scrive.

docs/       →  Documentazione per l'UMANO, struttura Diátaxis (vedi sezione 4).
               Stabile, curata, cambia raramente. Scritta insieme all'utente.

CLAUDE.md   →  Questo file. La schema che governa tutto.

src/        →  Il motore (engine, backtest, adapter OANDA, interfaccia).
               Codice eseguibile. Vedi src/README.md per i moduli da portare
               dal progetto Kraken.
```

**Regola d'oro tecnica (ereditata da Kraken):** separa nettamente il livello
dati/esecuzione (broker-specifico, in `src/adapters/`) dal cervello (strategie +
rischio + backtest, in `src/core/` e `src/backtest/`). Cambiare broker = riscrivere
solo gli adapter.

---

## 2. La wiki di ricerca — convenzioni

Ogni file in `research/` è una pagina markdown con **frontmatter YAML** e
**collegamenti interni** in stile `[[wikilink]]`.

### Tipi di pagina

| Cartella                 | Contiene                                              |
|--------------------------|------------------------------------------------------|
| `research/strategies/`   | Una pagina per strategia (pullback, breakout, …)     |
| `research/instruments/`  | Una pagina per strumento (EUR/USD, XAU/USD, US500, …)|
| `research/experiments/`  | Una pagina per ogni run di backtest significativo    |
| `research/index.md`      | Catalogo di tutto (content-oriented)                 |
| `research/log.md`        | Registro cronologico append-only                     |

I template vivono in `research/_templates/`. Usali quando crei una pagina nuova.

### Frontmatter obbligatorio

```yaml
---
type: strategy | instrument | experiment
status: untested | testing | edge-confirmed | rejected | paper | live
tags: [forex, trend-following, h1]
updated: 2026-06-19
links: ["[[pullback]]", "[[EUR_USD]]"]
---
```

Il campo `status` è **load-bearing**: guida il gate "scala o scarta" (sezione 5).

### Stato della verità

- I **numeri** stanno in `raw/` (immutabili). Le pagine wiki li **citano**, non li
  reinventano. Ogni claim numerico in una pagina deve puntare al file `raw/` che lo
  prova (es. `fonte: raw/exp_2026-06-19_pullback_EURUSD_H1.json`).
- Le **contraddizioni sono informazione**, non difetti da nascondere. Se un nuovo
  backtest contraddice una conclusione vecchia, NON cancellare la vecchia: aggiungi
  un collegamento `contraddice` e annota cosa è cambiato (timeframe? periodo? costi?).
  La conoscenza non decade, viene **superata** — si conserva cosa si credeva, quando,
  e cosa l'ha sostituita.

---

## 3. I tre workflow (ingest / query / lint)

### 3.1 INGEST — "ho lanciato un backtest, archivialo"

Quando l'utente lancia un backtest (da CLI, da Claude Code, o tramite il bot
Telegram che deposita l'output in `raw/`):

1. Leggi l'output grezzo in `raw/`. **Non fidarti mai di un numero che non hai letto
   dal file.**
2. Discuti i risultati chiave con l'utente (PF, Sharpe, max drawdown, n. trade,
   esito walk-forward).
3. Crea/aggiorna la pagina in `research/experiments/` (template `experiment.md`).
4. Aggiorna la pagina `research/strategies/<strategia>.md`: aggiungi questo run alla
   sua storia, aggiorna lo `status`, nota se rafforza o indebolisce l'edge.
5. Aggiorna la pagina `research/instruments/<strumento>.md` allo stesso modo.
6. Aggiorna `research/index.md` (nuova riga nel catalogo).
7. Appendi una riga a `research/log.md` (formato sotto).
8. **Applica il gate "scala o scarta"** (sezione 5) e scrivi il verdetto.

Un singolo backtest può toccare 5-8 pagine. Va bene: è il punto.

### 3.2 QUERY — "cosa sappiamo di…"

L'utente fa una domanda ("la pullback ha mai retto l'out-of-sample su un indice?").

1. Leggi prima `research/index.md` per trovare le pagine rilevanti.
2. Drill-down nelle pagine, leggi, sintetizza una risposta **con citazioni** alle
   pagine e ai file `raw/`.
3. **Insight prezioso = nuova pagina.** Se la risposta scopre una connessione o un
   confronto utile, archivialo in `research/` invece di lasciarlo sparire nella chat.
   Le esplorazioni devono compounding come gli esperimenti.

### 3.3 LINT — "controlla la salute della ricerca"

Periodicamente (o su richiesta):

- Contraddizioni tra pagine non collegate (due run sullo stesso strumento con esiti
  opposti senza un collegamento `contraddice`).
- Conclusioni stantie superate da run più recenti.
- Pagine orfane (nessun link in entrata).
- Strategie marcate `edge-confirmed` che però non hanno mai passato il paper trading.
- **Mancanza sospetta di contraddizioni**: una strategia con 10 run tutti positivi e
  zero tensioni è un campanello d'allarme di overfitting o di test troppo simili tra
  loro, non una buona notizia.
- Buchi: strumenti senza pagina, timeframe non ancora testati che varrebbe la pena
  esplorare.

Il lint **propone**, non esegue in autonomia decisioni irreversibili.

---

## 4. La documentazione umana (Diátaxis)

`docs/` segue le quattro modalità di Diátaxis. Non mescolarle: ogni file serve UN
bisogno.

| Cartella              | Bisogno              | Domanda dell'utente              |
|-----------------------|----------------------|----------------------------------|
| `docs/tutorials/`     | imparare facendo     | "fammi vedere come si parte"     |
| `docs/how-to/`        | risolvere un compito | "come faccio X?"                 |
| `docs/reference/`     | informazione precisa | "qual è il parametro esatto?"    |
| `docs/explanation/`   | capire perché        | "perché funziona così?"          |

Regola pratica quando scrivi in `docs/`: se stai spiegando *perché* in un how-to,
sposta la spiegazione in `explanation/`. Se stai insegnando in un reference, fermati.

---

## 5. Il gate "scala o scarta" (NON negoziabile)

La lezione madre del progetto Kraken: **il backtest serve a scoprire la verità, non
a confermare una speranza.** Se l'edge non c'è, è un risultato prezioso: ti fa
risparmiare denaro.

La sequenza di promozione di una strategia è rigida. Si avanza solo se si supera lo
stadio precedente:

```
untested
   │  backtest profondo su dati VERI (verificare profondità storica reale!)
   ▼
testing  ──(PF ≤ 1 o perdente)──────────────► rejected
   │  PF > 1 in-sample
   ▼
walk-forward out-of-sample
   │  ┌─ regge OOS ──────────► edge-confirmed
   │  └─ crolla OOS ─────────► rejected (OVERFITTING)
   ▼
edge-confirmed
   │  paper trading su demo OANDA (settimane, non ore)
   ▼
paper  ──(non replica il backtest)──────────► rejected / torna a testing
   │  paper coerente col backtest
   ▼
live   (solo con denaro che ci si può permettere di perdere)
```

**Criteri di rigetto automatico (dalle lezioni Kraken):**
- Storia dati insufficiente → il risultato è inaffidabile, NON un edge (Kraken dava
  ~720 candele e i "12 mesi" erano in realtà 30 giorni). Per OGNI strumento/timeframe
  su OANDA, **verifica la profondità storica reale** prima di concludere qualcosa.
- "Più trade" o "più leva" come unica leva di miglioramento → quasi sempre peggiora.
- In-sample positivo ma out-of-sample negativo → overfitting, si scarta. Sempre.

Quando applichi il gate in un ingest, scrivi esplicitamente nello `status` della
pagina e una riga di motivazione. Niente promozioni implicite.

---

## 6. Interfaccia: telefono + PC

L'utente deve poter lavorare da entrambi. Due canali, ruoli diversi:

**PC / mobile via Claude Code (ricerca profonda)**
Claude Code aperto nella repo è l'interprete naturale del linguaggio libero. Qui
giri i workflow ingest/query/lint, mantieni `research/`, fai analisi multi-strumento.
Claude Code è raggiungibile anche dall'app mobile → la "ricerca da telefono" passa
di qui, senza costruire un parser custom.

**Telegram (trigger rapidi + monitoraggio)**
Comandi strutturati e deterministici eseguiti sul VPS Hetzner (eredita il pattern
Kraken). Esempi: `/backtest pullback EUR_USD H1 3y`, `/status`, `/paper_start`,
`/report`. Il bot deposita l'output in `raw/` e appende uno stub a `research/log.md`;
il consolidamento nella wiki lo fai poi da Claude Code con l'ingest.

> Decisione di design aperta (da confermare con l'utente): se si vuole linguaggio
> *libero* anche su Telegram ("prova la pullback sull'oro vedi se regge"), serve un
> parse LLM al runtime sul VPS (es. una chiamata Haiku che traduce il messaggio in
> un comando strutturato). Ha un costo per messaggio. Alternativa a costo zero:
> comandi strutturati su Telegram + linguaggio libero solo via Claude Code. Default
> consigliato col budget attuale: la seconda.

---

## 7. log.md — formato

Append-only. Ogni riga inizia con un prefisso consistente, così è greppabile:

```
## [2026-06-19] ingest | pullback EUR_USD H1 3y → testing (PF 0.94)
## [2026-06-19] query  | edge su indici? → nessuno confermato OOS
## [2026-06-20] lint   | 2 contraddizioni, 1 orfana
```

`grep "^## \[" research/log.md | tail -10` dà gli ultimi 10 eventi.

---

## 8. Disciplina (riassunto operativo)

1. I numeri vivono in `raw/` e sono immutabili. Le pagine li citano.
2. Validare prima, costruire poi. Niente live senza backtest profondo + walk-forward
   positivo + paper coerente.
3. Le contraddizioni si conservano e si collegano, non si cancellano.
4. Un risultato negativo onesto è un risultato prezioso.
5. Aggiorna index e log a ogni ingest. Sempre.
6. Diátaxis in `docs/`: una modalità per file.
7. Questo file (CLAUDE.md) si co-evolve: se trovi una convenzione migliore, proponila
   e aggiornalo.
