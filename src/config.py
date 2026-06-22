"""Singola fonte di verità della configurazione.

Carica i parametri di connessione a Interactive Brokers da `.env` e definisce i
percorsi del progetto. Ogni altro modulo importa da qui: niente credenziali
sparse nel codice, niente path hardcoded.

NB su IBKR: non esiste un "token" come in OANDA. L'API parla con un processo
ponte (IB Gateway o TWS) che fa il login e apre una porta locale. Il nostro
codice si connette a quella porta. Quindi qui non c'è un segreto, ma host/porta
del Gateway + il numero di conto (paper o reale).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv è comodo ma non indispensabile
    load_dotenv = None

# Radice del progetto = cartella che contiene questo file -> .. (src) -> .. (root)
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "raw"
CACHE_DIR = RAW_DIR / "cache"

# Porte di default del ponte IBKR per ambiente.
#   IB Gateway: paper 4002, live 4001
#   TWS:        paper 7497, live 7496
# Usiamo IB Gateway (headless sul VPS) come default. Override via IBKR_PORT.
IBKR_DEFAULT_PORTS = {
    "practice": 4002,
    "live": 4001,
}


class ConfigError(RuntimeError):
    """Configurazione mancante o incoerente (es. ambiente non valido)."""


@dataclass(frozen=True)
class Settings:
    account_id: str
    host: str
    port: int
    client_id: int
    environment: str  # "practice" | "live"

    @property
    def is_live(self) -> bool:
        return self.environment == "live"


def load_settings(require_credentials: bool = True) -> Settings:
    """Legge `.env` (se presente) e l'ambiente, restituisce le impostazioni.

    Con `require_credentials=True` solleva `ConfigError` se manca il numero di
    conto: meglio un errore chiaro subito che una connessione che fallisce dopo.
    L'host/porta hanno default sensati (Gateway locale), quindi sono opzionali.
    """
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    environment = os.environ.get("IBKR_ENV", "practice").strip().lower()
    if environment not in IBKR_DEFAULT_PORTS:
        raise ConfigError(
            f"IBKR_ENV='{environment}' non valido. Usa: {', '.join(IBKR_DEFAULT_PORTS)}."
        )

    account_id = os.environ.get("IBKR_ACCOUNT_ID", "").strip()
    host = os.environ.get("IBKR_HOST", "127.0.0.1").strip()
    port = int(os.environ.get("IBKR_PORT", IBKR_DEFAULT_PORTS[environment]))
    client_id = int(os.environ.get("IBKR_CLIENT_ID", "1"))

    if require_credentials and not account_id:
        raise ConfigError(
            "IBKR_ACCOUNT_ID mancante. Copia .env.example in .env e compila il "
            "numero del conto paper (lo trovi in IB Gateway / Account Window; i "
            "conti demo iniziano di solito con 'DU')."
        )

    return Settings(
        account_id=account_id,
        host=host,
        port=port,
        client_id=client_id,
        environment=environment,
    )
