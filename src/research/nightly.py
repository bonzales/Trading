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

from src.research.engine import Result, run_sweep, summarize, to_rows


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


def run(timeframes: list[str], out_dir: str, cache_dir: str = "raw/cache") -> Path:
    today = datetime.now(timezone.utc).date().isoformat()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[Result]] = {}
    summary_all: dict[str, dict] = {}
    for tf in timeframes:
        res = run_sweep(timeframe=tf, cache_dir=cache_dir)
        all_results[tf] = res
        summary_all[tf] = summarize(res)

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
    log_line = (f"## [{today}] nightly | sweep {'/'.join(timeframes)}: {tot} combo, "
                f"{conf} confermate. Report: {md_path}\n")
    log_stub = out / "nightly_log_stub.txt"
    with log_stub.open("a") as fh:
        fh.write(log_line)

    print(f"Report scritto: {md_path}")
    print(f"  {tot} combinazioni, {conf} confermate.")
    return md_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="nightly", description="Sweep di ricerca notturno")
    p.add_argument("--tf", nargs="+", default=["D"], help="timeframe (default: D)")
    p.add_argument("--out", default="raw/research", help="cartella output report")
    p.add_argument("--cache", default="raw/cache", help="cartella dati")
    args = p.parse_args(argv)
    run(args.tf, args.out, args.cache)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
