"""Backtest v3: sistema a LIVELLI DI VOLUME multi-day sul DAX (M1).

Evoluzione di dax_open.py dopo che l'utente ha spiegato il metodo completo (vedi
research/strategies/dax_open_volume.md). Non più un semplice rimbalzo sull'apertura,
ma:
  - una MAPPA di livelli lasciati dalle candele ad alto volume (apertura 09:00,
    chiusura 17:30, spike di giornata), che il prezzo "ricorda" per giorni;
  - ingresso sulla ROTTURA netta di un livello in gioco (finestra oraria flessibile);
  - stop ancorato al livello di volume OPPOSTO più vicino;
  - uscite meccaniche che APPROSSIMANO la gestione discrezionale (time-stop se non
    si muove, pari a 1R, parziale, trailing sui runner).

ONESTÀ: la gestione dello stop dell'utente era discrezionale/adattiva. Qui è una
proxy meccanica: il backtest misura soprattutto se l'INGRESSO ha un edge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


@dataclass
class LevelsConfig:
    tz: str = "Europe/Berlin"
    session_start: str = "09:00"
    session_end: str = "17:30"
    entry_start: str = "09:06"
    entry_cutoff: str = "11:00"       # oltre non si apre più
    session_close: str = "17:30"
    # soglie volume (× mediana volume della sessione del giorno)
    vol_mult_normal: float = 5.0
    vol_mult_gold: float = 10.0
    keep_days_normal: int = 5
    keep_days_gold: int = 60
    max_levels_per_day: int = 4
    cluster_pts: float = 8.0
    # ingresso / rischio
    in_play_pts: float = 25.0         # livello "in gioco" se il prezzo gli è vicino
    break_pts: float = 6.0            # rottura netta: chiusura oltre il livello di
    stop_buffer_pts: float = 3.0
    max_stop_pts: float = 45.0        # fallback se non c'è livello opposto
    # uscite (proxy della gestione discrezionale)
    time_stop_min: int = 12           # se dopo N minuti non si è mosso a favore…
    time_stop_move: float = 8.0       # …di almeno questi punti → chiudo
    be_R: float = 1.0
    partial_R: float = 1.0
    partial_frac: float = 0.5
    trail_R: float = 1.0
    spread_pts: float = 1.5
    risk_pct: float = 0.02
    start_equity: float = 10_000.0


@dataclass
class Level:
    price: float
    born: date_cls
    tier: str          # "normal" | "gold"


@dataclass
class LTrade:
    day: object
    side: str
    entry: float
    stop: float
    r_points: float
    pnl_points: float
    r_multiple: float
    reason: str


def _hm(idx):
    return idx.strftime("%H:%M")


def build_level_map(d: pd.DataFrame, cfg: LevelsConfig) -> dict:
    """Per ogni giorno, i livelli lasciati dalle candele ad alto volume.

    d: DataFrame M1 con indice locale (Europe/Berlin) e colonna 'day'.
    Ritorna {day: [Level, ...]}.
    """
    out: dict = {}
    for day, g in d.groupby("day"):
        hm = g.index.strftime("%H:%M")
        sess = g[(hm >= cfg.session_start) & (hm <= cfg.session_end)]
        if len(sess) < 30:
            continue
        base = float(sess["volume"].median())
        if base <= 0:
            continue
        big = sess[sess["volume"] >= cfg.vol_mult_normal * base].copy()
        if big.empty:
            out[day] = []
            continue
        big = big.sort_values("volume", ascending=False).head(cfg.max_levels_per_day)
        levels: list[Level] = []
        for t, row in big.iterrows():
            price = float(row["close"])
            tier = "gold" if row["volume"] >= cfg.vol_mult_gold * base else "normal"
            # cluster: salta se troppo vicino a un livello già preso (tieni il primo, più forte)
            if any(abs(price - lv.price) < cfg.cluster_pts for lv in levels):
                continue
            levels.append(Level(price, day, tier))
        out[day] = levels
    return out


def active_levels(day, level_map: dict, days_sorted: list, cfg: LevelsConfig) -> list[Level]:
    """Livelli validi (dei giorni PRECEDENTI) per la data `day`."""
    i = days_sorted.index(day)
    out: list[Level] = []
    for prev in days_sorted[max(0, i - cfg.keep_days_gold):i]:
        age = i - days_sorted.index(prev)
        for lv in level_map.get(prev, []):
            keep = cfg.keep_days_gold if lv.tier == "gold" else cfg.keep_days_normal
            if age <= keep:
                out.append(lv)
    return out


def _simulate(after: pd.DataFrame, side: str, entry: float, stop: float,
              cfg: LevelsConfig, day) -> LTrade:
    half = cfg.spread_pts / 2.0
    sign = 1.0 if side == "long" else -1.0
    r_points = max(abs(entry - stop), 1e-9)
    peak = entry
    cur_stop = stop
    be_done = partial_done = False
    partial_pnl = 0.0
    remaining = 1.0
    fav = lambda p: sign * (p - entry)

    for n, (t, bar) in enumerate(after.iterrows()):
        hi, lo, cl = float(bar["high"]), float(bar["low"]), float(bar["close"])
        # stop / trailing
        if (lo <= cur_stop) if side == "long" else (hi >= cur_stop):
            ex = cur_stop - sign * half
            pnl = partial_pnl + remaining * fav(ex)
            return LTrade(day, side, entry, stop, r_points, pnl, pnl / r_points,
                          "stop" if not partial_done else "trail")
        fav_ext = hi if side == "long" else lo
        if sign * (fav_ext - peak) > 0:
            peak = fav_ext
        prof_R = fav(fav_ext) / r_points
        # time-stop: dopo N minuti senza movimento a favore → chiudo
        if not partial_done and n >= cfg.time_stop_min and fav(cl) < cfg.time_stop_move:
            ex = cl - sign * half
            pnl = partial_pnl + remaining * fav(ex)
            return LTrade(day, side, entry, stop, r_points, pnl, pnl / r_points, "time_stop")
        if not be_done and prof_R >= cfg.be_R:
            cur_stop = entry
            be_done = True
        if not partial_done and prof_R >= cfg.partial_R:
            tp = entry + sign * cfg.partial_R * r_points
            partial_pnl += cfg.partial_frac * (fav(tp) - half)
            remaining -= cfg.partial_frac
            partial_done = True
            cur_stop = entry
        if partial_done:
            trail = peak - sign * cfg.trail_R * r_points
            cur_stop = max(cur_stop, trail) if side == "long" else min(cur_stop, trail)

    last = after.iloc[-1]
    ex = float(last["close"]) - sign * half
    pnl = partial_pnl + remaining * fav(ex)
    return LTrade(day, side, entry, stop, r_points, pnl, pnl / r_points, "session_close")


def run_day(g: pd.DataFrame, levels: list[Level], today_open_price: float,
            cfg: LevelsConfig) -> LTrade | None:
    """Un giorno: prende la PRIMA rottura netta di un livello in gioco."""
    hm = g.index.strftime("%H:%M")
    win = g[(hm >= cfg.entry_start) & (hm <= cfg.entry_cutoff)]
    if len(win) < 5:
        return None
    # livelli in gioco: vicini al prezzo di apertura odierno
    in_play = [lv for lv in levels if abs(lv.price - today_open_price) <= cfg.in_play_pts * 3]
    if not in_play:
        return None
    prices = [lv.price for lv in in_play]

    prev_close = today_open_price
    for t, bar in win.iterrows():
        cl = float(bar["close"])
        after = g[(g.index > t) & (g.index.strftime("%H:%M") <= cfg.session_close)]
        if len(after) == 0:
            continue
        for p in prices:
            # rottura AL RIALZO del livello → long
            if prev_close <= p + cfg.break_pts and cl >= p + cfg.break_pts:
                stop = _opposite_stop(p, "long", prices, cfg)
                return _simulate(after, "long", cl + cfg.spread_pts / 2, stop, cfg, g.index[0].date())
            # rottura AL RIBASSO del livello → short
            if prev_close >= p - cfg.break_pts and cl <= p - cfg.break_pts:
                stop = _opposite_stop(p, "short", prices, cfg)
                return _simulate(after, "short", cl - cfg.spread_pts / 2, stop, cfg, g.index[0].date())
        prev_close = cl
    return None


def _opposite_stop(level: float, side: str, prices: list, cfg: LevelsConfig) -> float:
    """Stop al livello di volume opposto più vicino; fallback a max_stop_pts."""
    if side == "long":
        below = [p for p in prices if p < level - 1e-6]
        base = max(below) if below else level - cfg.max_stop_pts
        return base - cfg.stop_buffer_pts
    else:
        above = [p for p in prices if p > level + 1e-6]
        base = min(above) if above else level + cfg.max_stop_pts
        return base + cfg.stop_buffer_pts


def backtest(df: pd.DataFrame, cfg: LevelsConfig | None = None) -> dict:
    cfg = cfg or LevelsConfig()
    tz = ZoneInfo(cfg.tz)
    d = df.copy()
    d["time"] = pd.to_datetime(d["time"], utc=True)
    d = d.set_index("time").sort_index()
    d.index = d.index.tz_convert(tz)
    d["day"] = d.index.date

    level_map = build_level_map(d, cfg)
    days_sorted = sorted(level_map.keys())

    trades: list[LTrade] = []
    for day, g in d.groupby("day"):
        if day not in level_map:
            continue
        lv = active_levels(day, level_map, days_sorted, cfg)
        if not lv:
            continue
        hm = g.index.strftime("%H:%M")
        openrow = g[hm >= cfg.session_start]
        if openrow.empty:
            continue
        today_open = float(openrow.iloc[0]["open"])
        tr = run_day(g.drop(columns="day"), lv, today_open, cfg)
        if tr is not None:
            trades.append(tr)
    return _summarize(trades, cfg)


def _summarize(trades: list, cfg: LevelsConfig) -> dict:
    equity = cfg.start_equity
    curve = [equity]
    for tr in trades:
        equity += tr.r_multiple * cfg.risk_pct * equity
        curve.append(equity)
    curve = np.array(curve)
    r = np.array([t.r_multiple for t in trades]) if trades else np.array([])
    pts = np.array([t.pnl_points for t in trades]) if trades else np.array([])
    gw = r[r > 0].sum()
    gl = -r[r < 0].sum()
    peak = np.maximum.accumulate(curve)
    dd = (curve - peak) / peak
    return {
        "trades": trades,
        "metrics": {
            "n_trades": len(trades),
            "win_rate": float((r > 0).mean()) if len(r) else 0.0,
            "profit_factor": float(gw / gl) if gl > 0 else float("inf"),
            "expectancy_R": float(r.mean()) if len(r) else 0.0,
            "total_points": float(pts.sum()) if len(pts) else 0.0,
            "max_drawdown": float(dd.min()) if len(dd) else 0.0,
            "total_return": float(curve[-1] / curve[0] - 1) if len(curve) > 1 else 0.0,
            "long": int(sum(1 for t in trades if t.side == "long")),
            "short": int(sum(1 for t in trades if t.side == "short")),
            "reasons": {r_: int(sum(1 for t in trades if t.reason == r_))
                        for r_ in {t.reason for t in trades}},
        },
    }
