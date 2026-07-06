"""CLI di download e verifica dello storico IBKR.

Comandi (vedi docs/tutorials/01-primo-backtest.md):

    # Passo 1 — verifica la profondità storica REALE (sempre per primo)
    python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --check-coverage

    # Passo 2 — scarica e mette in cache N anni di storico
    python -m src.backtest.data_fetcher --instrument EUR_USD --tf H1 --years 3

Richiede un IB Gateway/TWS acceso e loggato (vedi .env.example). La cache finisce
in `raw/cache/` (ignorata da git). I dati grezzi sono fonte di verità: una volta
scritti non si modificano a mano.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import pandas as pd

from src.adapters.ibkr.data import IBKRDataClient
from src.config import CACHE_DIR, ConfigError, load_settings


def cache_path(instrument: str, granularity: str):
    return CACHE_DIR / f"{instrument}_{granularity}.csv"


def cmd_check_coverage(client: IBKRDataClient, instrument: str, granularity: str) -> int:
    cov = client.check_coverage(instrument, granularity)
    if cov is None:
        print(f"[!] Nessun dato disponibile per {instrument} {granularity}.")
        return 1
    print(f"Profondità storica REALE — {instrument} {granularity}")
    print(f"  prima candela : {cov.earliest.isoformat()}")
    print(f"  ultima candela: {cov.latest.isoformat()}")
    print(f"  intervallo    : {cov.years:.2f} anni ({cov.span.days} giorni)")
    print(f"  candele teoriche (24/7, limite SUP.): ~{cov.theoretical_candles:,}")
    print("  nota: il conteggio reale è minore (forex chiuso nei weekend/fuori orario).")
    print("  --> confronta questo numero con gli anni che CREDI di testare.")
    return 0


def cmd_fetch(client: IBKRDataClient, instrument: str, granularity: str, years: float, price: str) -> int:
    now = datetime.now(timezone.utc)
    from_time = now.replace(year=now.year - int(years)) if years == int(years) else now - pd.Timedelta(days=365.25 * years).to_pytimedelta()

    cov = client.check_coverage(instrument, granularity)
    if cov is not None and cov.earliest > from_time:
        print(
            f"[!] Richiesti {years}y ma IBKR parte dal {cov.earliest.date()} "
            f"({cov.years:.2f}y disponibili). Scarico ciò che esiste."
        )
        from_time = cov.earliest

    print(f"Scarico {instrument} {granularity} da {from_time.date()} a {now.date()} ...")
    records = client.fetch_history(instrument, granularity, from_time, now, price=price)
    if not records:
        print("[!] Nessuna candela scaricata.")
        return 1

    df = pd.DataFrame.from_records(records)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates(subset="time").sort_values("time").reset_index(drop=True)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = cache_path(instrument, granularity)
    df.to_csv(out, index=False)
    print(f"OK — {len(df):,} candele complete -> {out}")
    print(f"   periodo reale: {df['time'].iloc[0]} … {df['time'].iloc[-1]}")
    return 0


def build_client(source: str):
    """Costruisce il client dati per la sorgente scelta.

    - dukascopy: storico gratuito per la RICERCA (nessuna credenziale, default).
    - ibkr:      storico dal broker di esecuzione (serve Gateway acceso + .env).
    Entrambi espongono la stessa interfaccia (check_coverage, fetch_history).
    """
    if source == "dukascopy":
        from src.adapters.dukascopy.data import DukascopyDataClient
        return DukascopyDataClient()
    if source == "ibkr":
        from src.adapters.ibkr.data import IBKRDataClient
        return IBKRDataClient(load_settings(require_credentials=True))
    raise ValueError(f"Sorgente '{source}' sconosciuta. Usa: dukascopy | ibkr.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="data_fetcher", description="Download/verifica storico (Dukascopy/IBKR)")
    p.add_argument("--instrument", required=True, help="es. EUR_USD, XAU_USD (formato BASE_QUOTE)")
    p.add_argument("--tf", required=True, help="timeframe: M1 M5 M15 H1 H4 D W …")
    p.add_argument("--source", default="dukascopy", choices=["dukascopy", "ibkr"],
                   help="sorgente dati (default dukascopy: gratis, per la ricerca)")
    p.add_argument("--check-coverage", action="store_true", help="verifica la profondità storica, non scarica")
    p.add_argument("--years", type=float, default=None, help="anni di storico da scaricare")
    p.add_argument("--price", default="M", choices=["M", "B", "A"], help="mid/bid/ask (default M)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = build_client(args.source)
    except ConfigError as err:
        print(f"[config] {err}", file=sys.stderr)
        return 2

    close = getattr(client, "close", lambda: None)
    try:
        if args.check_coverage:
            return cmd_check_coverage(client, args.instrument, args.tf)
        if args.years is not None:
            return cmd_fetch(client, args.instrument, args.tf, args.years, args.price)
    finally:
        close()

    print("Niente da fare: usa --check-coverage oppure --years N.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
