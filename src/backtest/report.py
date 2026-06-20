"""CLI di backtest e report (vedi docs/tutorials/01-primo-backtest.md, passi 3-4).

    # Passo 3 — backtest in-sample
    python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1

    # Passo 4 — walk-forward (obbligatorio prima di concludere qualcosa)
    python -m src.backtest.report --strategy pullback --instrument EUR_USD --tf H1 --walkforward

Legge la cache prodotta da data_fetcher (raw/cache/), esegue il backtest e SALVA
l'output grezzo in raw/ (fonte di verità immutabile, da cui poi l'ingest costruisce
la pagina in research/).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

import pandas as pd

from src.adapters.oanda.data import granularity_to_seconds
from src.backtest.backtest_engine import (
    CostModel,
    run_backtest,
    walk_forward,
)
from src.backtest.data_fetcher import cache_path
from src.config import RAW_DIR
from src.core.strategy import make_strategy

# Griglia di default per il walk-forward della pullback. Volutamente piccola:
# più parametri = più rischio di overfitting (vedi explanation/perche-walk-forward).
DEFAULT_GRIDS = {
    "pullback": {
        "ema_fast": [10, 20],
        "ema_slow": [50, 100],
        "rsi_low": [35.0, 40.0],
        "rsi_high": [60.0, 65.0],
        "min_conditions": [2, 3],
    }
}


def periods_per_year(granularity: str) -> float:
    """Periodi/anno per annualizzare lo Sharpe (~252 giorni di trading)."""
    return (252 * 86400) / granularity_to_seconds(granularity)


def load_cached(instrument: str, granularity: str) -> pd.DataFrame:
    path = cache_path(instrument, granularity)
    if not path.exists():
        raise FileNotFoundError(
            f"Cache assente: {path}\n"
            f"Scaricala prima: python -m src.backtest.data_fetcher "
            f"--instrument {instrument} --tf {granularity} --years 3"
        )
    df = pd.read_csv(path, parse_dates=["time"])
    return df


def save_raw(payload: dict, strategy: str, instrument: str, granularity: str, kind: str) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"exp_{date.today().isoformat()}_{strategy}_{instrument}_{granularity}_{kind}.json"
    out = RAW_DIR / fname
    out.write_text(json.dumps(payload, indent=2, default=str))
    return str(out.relative_to(RAW_DIR.parent))


def cmd_backtest(args) -> int:
    df = load_cached(args.instrument, args.tf)
    strat = make_strategy(args.strategy)
    res = run_backtest(df, strat, periods_per_year=periods_per_year(args.tf))
    m = res.metrics

    print(f"Backtest in-sample — {args.strategy} {args.instrument} {args.tf}")
    print(f"  barre         : {res.bars:,}")
    print(f"  n. trade      : {m.n_trades}")
    print(f"  profit factor : {m.profit_factor:.3f}")
    print(f"  win rate      : {m.win_rate:.1%}")
    print(f"  sharpe        : {m.sharpe:.2f}")
    print(f"  max drawdown  : {m.max_drawdown:.1%}")
    print(f"  rendimento    : {m.total_return:.1%}  (equity finale {m.final_equity:,.0f})")

    rel = save_raw(
        {"type": "backtest", "strategy": args.strategy, "instrument": args.instrument,
         "tf": args.tf, "metrics": m.as_dict(), "n_trades": m.n_trades},
        args.strategy, args.instrument, args.tf, "backtest",
    )
    print(f"\nOutput grezzo -> {rel}")
    if m.profit_factor <= 1.0:
        print("VERDETTO: PF <= 1 -> non c'è edge in-sample. Niente walk-forward, si scarta.")
    else:
        print("VERDETTO: PF > 1 in-sample. NON basta: ora il walk-forward (--walkforward).")
    return 0


def cmd_walkforward(args) -> int:
    df = load_cached(args.instrument, args.tf)
    grid = DEFAULT_GRIDS.get(args.strategy)
    if grid is None:
        print(f"Nessuna griglia di default per '{args.strategy}'.", file=sys.stderr)
        return 2

    wf = walk_forward(df, args.strategy, grid)
    print(f"Walk-forward — {args.strategy} {args.instrument} {args.tf}  ({len(wf.windows)} finestre)")
    for i, w in enumerate(wf.windows, 1):
        print(f"  finestra {i}: IS PF {w.train_metrics.profit_factor:.2f} "
              f"-> OOS PF {w.test_metrics.profit_factor:.2f}  params={w.best_params}")
    print(f"\n  IS  PF medio : {wf.is_profit_factor:.3f}")
    print(f"  OOS PF medio : {wf.oos_profit_factor:.3f}")

    rel = save_raw(wf.as_dict(), args.strategy, args.instrument, args.tf, "walkforward")
    print(f"\nOutput grezzo -> {rel}")
    if wf.overfitting:
        print("VERDETTO: IS buono ma OOS crolla -> OVERFITTING. Si scarta. Sempre.")
    elif wf.oos_profit_factor > 1.0:
        print("VERDETTO: regge out-of-sample -> candidato a edge-confirmed. Prossimo: paper.")
    else:
        print("VERDETTO: OOS <= 1 -> nessun edge confermato. Si scarta.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="report", description="Backtest e walk-forward")
    p.add_argument("--strategy", required=True)
    p.add_argument("--instrument", required=True)
    p.add_argument("--tf", required=True)
    p.add_argument("--walkforward", action="store_true", help="esegue il walk-forward OOS")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.walkforward:
            return cmd_walkforward(args)
        return cmd_backtest(args)
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
