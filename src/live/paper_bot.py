"""Bot GIORNALIERO paper trading della strategia mean-reversion (rsi2_meanrev).

Da lanciare una volta al giorno (dopo la chiusura cash degli indici). Per ogni
strumento del paniere: scarica lo storico daily (Dukascopy, fonte segnale), legge la
posizione sul conto IBKR, decide con src/live/decision.py, e piazza/chiude gli ordini
sul conto PAPER. Stato e log persistiti in raw/.

Uso:
    # prova a secco: mostra le decisioni di OGGI senza toccare il broker (no Gateway)
    python -m src.live.paper_bot --dry-run

    # esecuzione reale sul conto paper (serve IB Gateway acceso, vedi deploy/SETUP_VPS.md)
    python -m src.live.paper_bot

Sicurezza: long-only, un solo strumento per posizione, stop di protezione presso il
broker. Il sizing usa un `point_value` che DEVE essere verificato dal vivo (paper!).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone

import pandas as pd

from src.adapters.dukascopy.data import DukascopyDataClient
from src.config import RAW_DIR, ConfigError, load_settings
from src.live.decision import MRParams, Plan, decide, position_size
from src.live.notifier import TelegramNotifier, format_action, format_summary

BASKET = ["US500", "NAS100", "US30", "UK100", "DAX"]

# Valore di 1 punto indice per contratto CFD. PLACEHOLDER: da confermare col broker
# (paper). Un valore errato sbaglia solo la GRANDEZZA della posizione, non il segnale.
POINT_VALUE = {"US500": 1.0, "NAS100": 1.0, "US30": 1.0, "UK100": 1.0, "DAX": 1.0}

STATE_FILE = RAW_DIR / "live_state.json"
LOG_FILE = RAW_DIR / "live_log.csv"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def log_row(row: dict) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row])
    df.to_csv(LOG_FILE, mode="a", header=not LOG_FILE.exists(), index=False)


def bars_held(bars: pd.DataFrame, entry_date: str | None) -> int | None:
    if not entry_date:
        return None
    t = pd.to_datetime(bars["time"])
    return int((t > pd.to_datetime(entry_date)).sum())


def daily_bars(client: DukascopyDataClient, instrument: str, years: int = 3) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    frm = now.replace(year=now.year - years)
    recs = client.fetch_history(instrument, "D", frm, now, price="M")
    df = pd.DataFrame.from_records(recs)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df.drop_duplicates("time").sort_values("time").reset_index(drop=True)


def run(dry_run: bool, params: MRParams, instruments: list[str]) -> int:
    data = DukascopyDataClient()
    execu = None
    equity = 10_000.0
    if not dry_run:
        try:
            settings = load_settings(require_credentials=True)
        except ConfigError as err:
            print(f"[config] {err}", file=sys.stderr)
            return 2
        from src.adapters.ibkr.execution import IBKRExecution
        execu = IBKRExecution(settings)
        execu.connect()
        equity = execu.net_liquidation() or equity

    notifier = TelegramNotifier()
    state = load_state()
    today = datetime.now(timezone.utc).date().isoformat()
    actions: list[dict] = []
    print(f"=== paper_bot {today} {'(DRY-RUN)' if dry_run else '(LIVE paper)'} | equity {equity:,.0f} ===")

    for inst in instruments:
        bars = daily_bars(data, inst)
        if bars.empty or len(bars) < params.ma_long + 1:
            print(f"  {inst:7} dati insufficienti, salto")
            continue
        st = state.get(inst, {})
        has_pos = bool(st.get("open"))
        if not dry_run:  # la verità sulla posizione è il broker, non il file
            has_pos = execu.position(inst).qty > 0
        held = bars_held(bars, st.get("entry_date")) if has_pos else None

        plan: Plan = decide(bars, has_pos, held, params)
        print(f"  {inst:7} close {plan.close:,.1f} | {plan.action:5} | {plan.reason}")

        qty = None
        if plan.action == "BUY":
            qty = position_size(equity, plan.close, plan.stop_price, POINT_VALUE.get(inst, 1.0), params)
            if not dry_run:
                if qty > 0:
                    execu.buy_with_stop(inst, qty, plan.stop_price)
                    state[inst] = {"open": True, "entry_date": today, "qty": qty,
                                   "stop": plan.stop_price, "entry": plan.close}
                else:
                    print(f"  {inst:7} qty calcolata 0 → nessun ordine")
        elif plan.action == "CLOSE" and not dry_run:
            execu.close(inst)
            state.pop(inst, None)

        # notifica Telegram per ogni operazione (BUY/CLOSE), anche in prova (taggata)
        if plan.action in ("BUY", "CLOSE"):
            notifier.send(format_action(inst, plan.action, plan.reason, plan.close,
                                        plan.stop_price, qty, dry_run))

        actions.append({"instrument": inst, "action": plan.action, "close": plan.close})
        log_row({"date": today, "instrument": inst, "action": plan.action,
                 "reason": plan.reason, "close": plan.close, "atr": plan.atr,
                 "stop": plan.stop_price, "dry_run": dry_run})

    if not dry_run:
        save_state(state)
        execu.disconnect()

    notifier.send(format_summary(today, actions, equity, dry_run))
    if notifier.enabled:
        print("Riepilogo inviato su Telegram.")
    print("Fatto.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="paper_bot", description="Bot giornaliero mean-reversion (paper)")
    p.add_argument("--dry-run", action="store_true", help="mostra le decisioni senza toccare il broker")
    p.add_argument("--instruments", nargs="*", default=BASKET, help=f"default: {' '.join(BASKET)}")
    args = p.parse_args(argv)
    return run(args.dry_run, MRParams(), args.instruments)


if __name__ == "__main__":
    raise SystemExit(main())
