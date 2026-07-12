"""Job di ricerca notturno: sweepa l'universo su uno o più timeframe e deposita un
report ordinato in raw/, pronto per la revisione umana la mattina.

Uso:
    python -m src.research.nightly                 # timeframe daily (default)
    python -m src.research.nightly --tf D H4 H1    # più timeframe
    python -m src.research.nightly --out raw/research

Regola d'oro: il job RACCOGLIE EVIDENZA, non promuove strategie. Il gate finale
(scala o scarta) lo applica l'umano rivedendo il report. Il report è costruito per
RESISTERE al data-mining: mostra quante combinazioni sono state testate e segnala
come `suspect` tutto ciò che ha un bel PF pieno ma non regge metà/OOS.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from src.adapters.resample import load_tf
from src.research.engine import Result, run_sweep, summarize, to_rows

# Edge daily già noti/documentati (symbol, template): servono a calcolare le NOVITÀ,
# così il messaggio Telegram del mattino segnala solo ciò che non abbiamo già studiato.
# Da aggiornare quando un nuovo edge viene promosso nella wiki.
KNOWN_D: set[tuple[str, str]] = {
    ("US500", "mr_indices"), ("NAS100", "mr_indices"), ("US30", "mr_indices"), ("UK100", "mr_indices"),
    ("XAU_USD", "trend_long"), ("XAG_USD", "trend_long"), ("WTI", "trend_long"),
    ("BRENT", "trend_long"), ("COPPER", "trend_long"), ("NAS100", "trend_long"),
    ("DAX", "trend_long"), ("US500", "trend_long"), ("UK100", "trend_long"),
    ("XAU_USD", "trend_ls"), ("WTI", "trend_ls"), ("BRENT", "trend_ls"),
    ("EUR_USD", "mr_fx"), ("GBP_USD", "mr_fx"), ("USD_CHF", "mr_fx"),
    ("USD_CAD", "mr_fx"), ("NZD_USD", "mr_fx"), ("BRENT", "mr_fx"),
}


def is_novel(r: Result) -> bool:
    """Candidato genuinamente nuovo: (symbol, template base) non tra gli edge già noti.
    Le varianti di parametri di un edge noto NON sono novità (stesso template base)."""
    return not (r.timeframe == "D" and (r.symbol, r.template) in KNOWN_D)


def telegram_summary(all_results: dict[str, list[Result]], summary_all: dict,
                     watchlist=None, ledger=None, new_added: int = 0) -> str:
    """Messaggio Telegram CORTO (plain-text): conteggi + stato watchlist. Niente markdown.

    L'azione per te scatta SOLO quando compaiono candidati ⭐ GRADUATI: hanno retto sul
    forward (dati post-scoperta) → meritano che me li porti per la revisione/wiki.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    tot = sum(s["n_combos"] for s in summary_all.values())
    conf = sum(s["confirmed"] for s in summary_all.values())
    tfs = ",".join(all_results.keys())
    lines = [f"🔬 Ricerca notturna {today}",
             f"TF {tfs} · {tot} combo testate · {conf} candidati (gate ok)"]
    if watchlist is not None:
        grad = watchlist.by_status("graduated")
        hold = watchlist.by_status("holding")
        watch = watchlist.by_status("watching")
        fail = watchlist.by_status("failing")
        lines.append(f"📋 Watchlist: {len(watch)} in osservazione · {len(hold)} reggono "
                     f"· {len(fail)} fallite")
        if new_added:
            lines.append(f"🆕 {new_added} nuovi candidati messi in osservazione")
        if grad:
            lines.append(f"⭐ GRADUATI ({len(grad)}) — reggono sul FORWARD, da rivedere:")
            for w in grad[:6]:
                p = f"[{','.join(f'{k}={v}' for k,v in w.params.items())}]" if w.params else ""
                lines.append(f"• {w.symbol} {w.template}{p} {w.timeframe} "
                             f"(fwd PF {w.fwd_pf:.2f}/{w.fwd_trades} tr)")
        else:
            lines.append("✅ Nessun graduato: niente che richieda la tua attenzione oggi.")
    if ledger is not None:
        lines.append(f"(frugate {ledger.n_distinct} ipotesi in totale; "
                     f"~{ledger.expected_false_positives():.0f} falsi positivi attesi per caso)")
    return "\n".join(lines)


def _markdown(all_results: dict[str, list[Result]], summary_all: dict) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    lines = [f"# Report ricerca notturna — {today}", ""]
    tot = sum(s["n_combos"] for s in summary_all.values())
    conf = sum(s["confirmed"] for s in summary_all.values())
    lines += [
        f"**{tot} combinazioni testate** su {len(all_results)} timeframe. "
        f"Confermate: {conf}. ",
        "",
        "> ⚠️ **Multiple testing**: con molte combinazioni, alcune sembrano vincenti per "
        "caso. Fidati solo di ciò che è `confirmed` (positivo su intero + due metà + OOS) "
        "e conferma sempre con un test indipendente prima di crederci. Un PF pieno alto "
        "ma `suspect` è probabile fortuna campione.",
        "",
    ]
    for tf, results in all_results.items():
        s = summary_all[tf]
        lines += [f"## Timeframe {tf}  ·  {s['confirmed']} confermate / {s['n_combos']} combo", ""]
        conf_rows = [r for r in results if r.verdict == "confirmed"]
        susp_rows = [r for r in results if r.verdict == "suspect"]
        if conf_rows:
            lines += ["**Confermate** (positive su tutto):", "",
                      "| strumento | template | PF pieno | 1ª/2ª metà | OOS | maxDD | n |",
                      "|-----------|----------|----------|-----------|-----|-------|---|"]
            for r in conf_rows:
                lines.append(f"| {r.symbol} | {r.template} | {r.pf_full:.2f} | "
                             f"{r.pf_h1:.2f}/{r.pf_h2:.2f} | {r.pf_oos:.2f} | {r.maxdd:.0%} | {r.n_trades} |")
            lines.append("")
        if susp_rows:
            lines += [f"**Sospette** ({len(susp_rows)}, PF pieno >1 ma falliscono metà/OOS — NON fidarsi):", ""]
            for r in susp_rows[:10]:
                lines.append(f"- {r.symbol} {r.template}: PF pieno {r.pf_full:.2f}, "
                             f"metà {r.pf_h1:.2f}/{r.pf_h2:.2f}, OOS {r.pf_oos:.2f}")
            lines.append("")
    return "\n".join(lines)


def _load_env() -> None:
    """Carica il .env del repo in os.environ (per TELEGRAM_*), se python-dotenv c'è."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def run(timeframes: list[str], out_dir: str, cache_dir: str = "raw/cache",
        no_telegram: bool = False) -> Path:
    today = datetime.now(timezone.utc).date().isoformat()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[Result]] = {}
    summary_all: dict[str, dict] = {}
    all_spec_ids: list[str] = []
    for tf in timeframes:
        res = run_sweep(timeframe=tf, cache_dir=cache_dir, explore=True)
        all_results[tf] = res
        summary_all[tf] = summarize(res)
        all_spec_ids += [r.spec_id for r in res]

    # registro cumulativo (memoria anti-multiple-testing)
    from src.research.ledger import Ledger
    ledger = Ledger(out / "ledger.json")
    ledger.record(all_spec_ids)
    ledger.save()

    # watchlist forward: registra i nuovi candidati confermati e aggiorna la performance
    # sui dati POST-scoperta (la difesa vera contro il data-mining)
    from src.research.watchlist import Watchlist
    wl = Watchlist(out / "watchlist.json")
    new_added = 0
    for tf, res in all_results.items():
        for r in res:
            if r.verdict == "confirmed" and is_novel(r):
                if wl.add_if_new(r.to_spec(), r.pf_full, today):
                    new_added += 1
    wl.update_forward(lambda s, t: load_tf(s, t, cache_dir), today)
    wl.save()

    payload = {"date": today, "timeframes": timeframes,
               "summary": summary_all,
               "results": {tf: to_rows(r) for tf, r in all_results.items()}}
    json_path = out / f"research_{today}.json"
    json_path.write_text(json.dumps(payload, indent=2, default=float))
    md_path = out / f"research_{today}.md"
    md_path.write_text(_markdown(all_results, summary_all))

    # stub cronologico per research/log.md (la consolidazione la fa l'umano con l'ingest)
    conf = sum(s["confirmed"] for s in summary_all.values())
    tot = sum(s["n_combos"] for s in summary_all.values())
    grad = len(wl.by_status("graduated"))
    log_line = (f"## [{today}] nightly | sweep {'/'.join(timeframes)}: {tot} combo, "
                f"{conf} candidati, {new_added} nuovi in watchlist, {grad} graduati. "
                f"Report: {md_path}\n")
    log_stub = out / "nightly_log_stub.txt"
    with log_stub.open("a") as fh:
        fh.write(log_line)

    # riepilogo Telegram corto — no-op se Telegram non configurato
    if not no_telegram:
        _load_env()  # porta TELEGRAM_* in os.environ (come fa load_settings del bot)
        from src.live.notifier import TelegramNotifier
        notifier = TelegramNotifier()
        if notifier.enabled:
            notifier.send(telegram_summary(all_results, summary_all, wl, ledger, new_added))
            print("Riepilogo inviato su Telegram.")

    print(f"Report scritto: {md_path}")
    print(f"  {tot} combinazioni, {conf} confermate.")
    return md_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="nightly", description="Sweep di ricerca notturno")
    p.add_argument("--tf", nargs="+", default=["D"], help="timeframe (default: D)")
    p.add_argument("--out", default="raw/research", help="cartella output report")
    p.add_argument("--cache", default="raw/cache", help="cartella dati")
    p.add_argument("--no-telegram", action="store_true", help="non inviare il riepilogo Telegram")
    args = p.parse_args(argv)
    run(args.tf, args.out, args.cache, no_telegram=args.no_telegram)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
