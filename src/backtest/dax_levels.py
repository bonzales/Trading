"""Backtest v3: sistema a LIVELLI DI VOLUME multi-day su indici (M1).

Metodo completo descritto dall'utente (vedi research/strategies/dax_open_volume.md):
  - MAPPA di livelli lasciati dalle candele ad alto volume (apertura, chiusura,
    spike), che il prezzo "ricorda" per giorni (normali ~5gg, "oro" a lungo);
  - ingresso sulla ROTTURA netta di un livello in gioco, PIÙ setup al giorno;
  - stop al livello di volume OPPOSTO più vicino;
  - uscite proxy della gestione discrezionale (time-stop, pari 1R, parziale, trail).

Multi-strumento: DAX (apertura 09:00 Berlino) e indici USA S&P500/NASDAQ/DowJones
(apertura 15:30 Berlino). Usa make_config(instrument) per la sessione giusta.

ONESTÀ: lo stop reale dell'utente era discrezionale; qui è una proxy meccanica →
il backtest misura soprattutto l'edge dell'INGRESSO, su 4 mercati indipendenti.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date as date_cls
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


# Sessioni per strumento (orari Europe/Berlin). L'ingresso parte poco dopo
# l'apertura e resta aperto per alcune ore (più setup al giorno).
SESSIONS = {
    "DAX":    dict(session_start="09:00", entry_start="09:06", entry_cutoff="12:00", session_close="17:30"),
    "US500":  dict(session_start="15:30", entry_start="15:36", entry_cutoff="19:00", session_close="22:00"),
    "NAS100": dict(session_start="15:30", entry_start="15:36", entry_cutoff="19:00", session_close="22:00"),
    "US30":   dict(session_start="15:30", entry_start="15:36", entry_cutoff="19:00", session_close="22:00"),
}


@dataclass
class LevelsConfig:
    tz: str = "Europe/Berlin"
    session_start: str = "09:00"
    entry_start: str = "09:06"
    entry_cutoff: str = "12:00"
    session_close: str = "17:30"
    # livelli di volume
    vol_mult_normal: float = 5.0
    vol_mult_gold: float = 10.0
    keep_days_normal: int = 5
    keep_days_gold: int = 60
    max_levels_per_day: int = 4
    cluster_pts: float = 8.0
    # ingresso / rischio
    in_play_pts: float = 25.0
    break_pts: float = 6.0
    stop_buffer_pts: float = 3.0
    max_stop_pts: float = 45.0
    max_trades_day: int = 6
    cooldown_min: int = 3
    # uscite (proxy della gestione discrezionale)
    time_stop_min: int = 12
    time_stop_move: float = 8.0
    be_R: float = 1.0
    partial_R: float = 1.0
    partial_frac: float = 0.5
    trail_R: float = 1.0
    spread_pts: float = 1.5
    risk_pct: float = 0.02
    start_equity: float = 10_000.0


def make_config(instrument: str, **overrides) -> LevelsConfig:
    """Config con la sessione giusta per lo strumento (+ eventuali override)."""
    sess = SESSIONS.get(instrument.upper())
    if sess is None:
        raise ValueError(f"Sessione non definita per '{instrument}'. Note: {list(SESSIONS)}.")
    return replace(LevelsConfig(), **sess, **overrides)


@dataclass
class Level:
    price: float
    born: date_cls
    tier: str  # "normal" | "gold"


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


def build_level_map(d: pd.DataFrame, cfg: LevelsConfig) -> dict:
    """Per ogni giorno, i livelli lasciati dalle candele ad alto volume."""
    out: dict = {}
    for day, g in d.groupby("day"):
        hm = g.index.strftime("%H:%M")
        sess = g[(hm >= cfg.session_start) & (hm <= cfg.session_close)]
        if len(sess) < 30:
            continue
        base = float(sess["volume"].median())
        if base <= 0:
            out[day] = []
            continue
        big = sess[sess["volume"] >= cfg.vol_mult_normal * base]
        big = big.sort_values("volume", ascending=False).head(cfg.max_levels_per_day)
        levels: list[Level] = []
        for _, row in big.iterrows():
            price = float(row["close"])
            if any(abs(price - lv.price) < cfg.cluster_pts for lv in levels):
                continue
            tier = "gold" if row["volume"] >= cfg.vol_mult_gold * base else "normal"
            levels.append(Level(price, day, tier))
        out[day] = levels
    return out


def active_levels(day, level_map, days_sorted, day_to_i, cfg) -> list[Level]:
    i = day_to_i[day]
    out: list[Level] = []
    for j in range(max(0, i - cfg.keep_days_gold), i):
        age = i - j
        for lv in level_map.get(days_sorted[j], []):
            keep = cfg.keep_days_gold if lv.tier == "gold" else cfg.keep_days_normal
            if age <= keep:
                out.append(lv)
    return out


def _opposite_stop(level, side, prices, cfg):
    if side == "long":
        below = [p for p in prices if p < level - 1e-6]
        base = max(below) if below else level - cfg.max_stop_pts
        return base - cfg.stop_buffer_pts
    above = [p for p in prices if p > level + 1e-6]
    base = min(above) if above else level + cfg.max_stop_pts
    return base + cfg.stop_buffer_pts


def _simulate(highs, lows, closes, start, end, side, entry, stop, cfg, day):
    """Gestisce la posizione (posizionale, veloce). Ritorna (LTrade, exit_pos)."""
    half = cfg.spread_pts / 2.0
    sign = 1.0 if side == "long" else -1.0
    r = max(abs(entry - stop), 1e-9)
    peak = entry
    cur_stop = stop
    be = part = False
    ppnl = 0.0
    rem = 1.0
    fav = lambda p: sign * (p - entry)

    for pos in range(start, end + 1):
        hi, lo, cl = highs[pos], lows[pos], closes[pos]
        if (lo <= cur_stop) if side == "long" else (hi >= cur_stop):
            ex = cur_stop - sign * half
            pnl = ppnl + rem * fav(ex)
            return LTrade(day, side, entry, stop, r, pnl, pnl / r,
                          "stop" if not part else "trail"), pos
        fe = hi if side == "long" else lo
        if sign * (fe - peak) > 0:
            peak = fe
        pr = fav(fe) / r
        if not part and (pos - start) >= cfg.time_stop_min and fav(cl) < cfg.time_stop_move:
            ex = cl - sign * half
            pnl = ppnl + rem * fav(ex)
            return LTrade(day, side, entry, stop, r, pnl, pnl / r, "time_stop"), pos
        if not be and pr >= cfg.be_R:
            cur_stop = entry
            be = True
        if not part and pr >= cfg.partial_R:
            tp = entry + sign * cfg.partial_R * r
            ppnl += cfg.partial_frac * (fav(tp) - half)
            rem -= cfg.partial_frac
            part = True
            cur_stop = entry
        if part:
            trail = peak - sign * cfg.trail_R * r
            cur_stop = max(cur_stop, trail) if side == "long" else min(cur_stop, trail)

    ex = closes[end] - sign * half
    pnl = ppnl + rem * fav(ex)
    return LTrade(day, side, entry, stop, r, pnl, pnl / r, "session_close"), end


def run_day(g, levels, today_open, cfg) -> list[LTrade]:
    """Un giorno: PIÙ setup. Prende ogni rottura netta, con cooldown tra i trade."""
    hm = np.array(g.index.strftime("%H:%M"))
    sess = np.where(hm <= cfg.session_close)[0]
    if len(sess) == 0:
        return []
    close_pos = int(sess[-1])
    ewin = np.where((hm >= cfg.entry_start) & (hm <= cfg.entry_cutoff))[0]
    if len(ewin) < 5:
        return []
    prices = [lv.price for lv in levels if abs(lv.price - today_open) <= cfg.in_play_pts * 3]
    if not prices:
        return []

    highs = g["high"].to_numpy()
    lows = g["low"].to_numpy()
    closes = g["close"].to_numpy()
    day0 = g.index[0].date()
    half = cfg.spread_pts / 2.0
    last = int(ewin[-1])

    trades: list[LTrade] = []
    pos = int(ewin[0])
    prev_close = today_open
    while pos <= last and len(trades) < cfg.max_trades_day:
        cl = float(closes[pos])
        hit = None
        for p in prices:
            if prev_close <= p + cfg.break_pts and cl >= p + cfg.break_pts:
                hit = ("long", cl + half, _opposite_stop(p, "long", prices, cfg))
                break
            if prev_close >= p - cfg.break_pts and cl <= p - cfg.break_pts:
                hit = ("short", cl - half, _opposite_stop(p, "short", prices, cfg))
                break
        if hit is not None and pos < close_pos:
            tr, ex = _simulate(highs, lows, closes, pos + 1, close_pos, *hit, cfg, day0)
            trades.append(tr)
            pos = ex + cfg.cooldown_min
            prev_close = float(closes[min(ex, close_pos)])
        else:
            prev_close = cl
            pos += 1
    return trades


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
    day_to_i = {day: i for i, day in enumerate(days_sorted)}

    trades: list[LTrade] = []
    for day, g in d.groupby("day"):
        if day not in level_map:
            continue
        lv = active_levels(day, level_map, days_sorted, day_to_i, cfg)
        if not lv:
            continue
        hm = g.index.strftime("%H:%M")
        openrow = g[hm >= cfg.session_start]
        if openrow.empty:
            continue
        today_open = float(openrow.iloc[0]["open"])
        trades.extend(run_day(g.drop(columns="day"), lv, today_open, cfg))
    return _summarize(trades, cfg)


def _summarize(trades, cfg) -> dict:
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
