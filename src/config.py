"""Singola fonte di verità della configurazione.

Carica le credenziali OANDA da `.env` e definisce i percorsi del progetto. Ogni
altro modulo importa da qui: niente credenziali sparse nel codice, niente path
hardcoded.
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

# Host REST OANDA v20 per ambiente.
OANDA_HOSTS = {
    "practice": "https://api-fxpractice.oanda.com",
    "live": "https://api-fxtrade.oanda.com",
}


class ConfigError(RuntimeError):
    """Configurazione mancante o incoerente (es. credenziali assenti)."""


@dataclass(frozen=True)
class Settings:
    account_id: str
    api_token: str
    environment: str  # "practice" | "live"

    @property
    def host(self) -> str:
        return OANDA_HOSTS[self.environment]

    @property
    def is_live(self) -> bool:
        return self.environment == "live"


def load_settings(require_credentials: bool = True) -> Settings:
    """Legge `.env` (se presente) e l'ambiente, restituisce le impostazioni.

    Con `require_credentials=True` solleva `ConfigError` se mancano account o
    token: meglio un errore chiaro subito che una chiamata API che fallisce dopo.
    """
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    account_id = os.environ.get("OANDA_ACCOUNT_ID", "").strip()
    api_token = os.environ.get("OANDA_API_TOKEN", "").strip()
    environment = os.environ.get("OANDA_ENV", "practice").strip().lower()

    if environment not in OANDA_HOSTS:
        raise ConfigError(
            f"OANDA_ENV='{environment}' non valido. Usa: {', '.join(OANDA_HOSTS)}."
        )

    if require_credentials and not (account_id and api_token):
        raise ConfigError(
            "Credenziali OANDA mancanti. Copia .env.example in .env e compila "
            "OANDA_ACCOUNT_ID e OANDA_API_TOKEN (account demo gratuito su oanda.com)."
        )

    return Settings(account_id=account_id, api_token=api_token, environment=environment)
