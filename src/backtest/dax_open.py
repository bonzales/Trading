"""Backtest intraday della strategia di scalping sull'apertura del DAX.

Vedi research/strategies/dax_open_volume.md per l'idea. Qui la traduzione MECCANICA
e il simulatore, separato dal motore continuo (`backtest_engine.py`) perché la
logica è a SESSIONE: un setup al giorno, finestre orarie, apertura di Francoforte.

Sequenza di una giornata (orari Europe/Berlin, DST-aware):
  1. baseline volume 08:30–09:00.
  2. candela segnale = candela M1 in 09:00–09:05 col volume più alto e ≥ vol_mult×
     baseline. Se nessuna supera la soglia → nessun trade.
  3. la candela segnale definisce una zona [low, high] e un livello (close).
  4. finestra d'ingresso 09:06–entry_end: si cerca un RIMBALZO sulla zona, con
     elasticità (fascia di prossimità `tol`, conferma `confirm`).
  5. gestione: stop dietro la candela, +be_trigger→pari, +partial_at→parziale +
     trailing, poi lascia correre. Chiusura forzata a session_close.

I numeri fini (tol, confirm, buffer) sono scelte di compromesso documentate, poi
si ottimizzano col walk-forward. Costi: spread in punti applicato a ogni fill.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


@dataclass
class DaxOpenConfig:
    tz: str = "Europe/Berlin"
    baseline_start: str = "08:30"
    baseline_end: str = "09:00"      # esclusivo
    signal_start: str = "09:00"
    signal_end: str = "09:06"        # esclusivo → candele 09:00..09:05
    entry_end: str = "09:30"         # ultimo minuto in cui si può APRIRE
    session_close: str = "17:30"     # chiusura forzata della posizione
    vol_mult: float = 5.0            # soglia volume relativa (×baseline)
    tol_pts: float = 4.0             # fascia di prossimità attorno alla zona
    confirm_pts: float = 3.0         # conferma del rimbalzo (punti)
    stop_buffer_pts: float = 2.0     # margine oltre l'estremo della candela
    be_trigger_pts: float = 25.0     # +profitto → stop a pari
    partial_at_pts: float = 40.0     # +profitto → chiusura parziale
    partial_frac: float = 0.5        # frazione chiusa al parziale
    trail_dist_pts: float = 15.0     # distanza del trailing dopo il parziale
    spread_pts: float = 1.5          # spread DAX in apertura (~misurato)
    risk_pct: float = 0.02           # rischio per trade
    start_equity: float = 10_000.0
    # --- v2 "rettangolo" (come opera davvero l'utente) ------------------------
    # zona = [chiusura, estremo] della candela segnale (non tutta la candela);
    # ingresso sul rettangolo (limite al bordo); stop appena dietro il rettangolo;
    # uscite in multipli di R (a +1R → pari + parziale, poi trailing).
    be_R: float = 1.0                # +profitto in R → stop a pari
    partial_R: float = 1.0           # +profitto in R → chiusura parziale
    trail_R: float = 1.0             # distanza trailing in R dopo il parziale


@dataclass
class Trade:
    day: object
    side: str            # "long" | "short"
    entry_time: object
    entry: float
    stop: float
    r_points: float
    exit_time: object = None
    exit: float = None
    pnl_points: float = None   # per-unità, ponderato per il parziale, NETTO costi
    r_multiple: float = None
    reason: str = ""


def _hm(series_idx_local) -> np.ndarray:
    return series_idx_local.strftime("%H:%M").to_numpy()


def find_signal(day_df: pd.DataFrame, cfg: DaxOpenConfig) -> dict | None:
    """Trova la candela segnale del giorno. day_df ha colonne o/h/l/c/volume e
    indice locale (Europe/Berlin). Ritorna dict con zona e livelli, o None."""
    hm = day_df.index.strftime("%H:%M")
    base = day_df[(hm >= cfg.baseline_start) & (hm < cfg.baseline_end)]["volume"]
    window = day_df[(hm >= cfg.signal_start) & (hm < cfg.signal_end)]
    if len(base) < 5 or len(window) < 3:
        return None
    baseline = float(base.mean())
    if baseline <= 0:
        return None
    q = window[window["volume"] >= cfg.vol_mult * baseline]
    if q.empty:
        return None
    sig = q.loc[q["volume"].idxmax()]
    return {
        "time": sig.name,
        "high": float(sig["high"]),
        "low": float(sig["low"]),
        "close": float(sig["close"]),
        "ratio": float(sig["volume"] / baseline),
    }


def _simulate_trade(entry_df: pd.DataFrame, side: str, entry_price: float,
                    stop: float, cfg: DaxOpenConfig, day) -> Trade:
    """Gestisce la posizione candela per candela fino all'uscita.

    entry_df: candele DAL minuto SUCCESSIVO all'ingresso fino a session_close.
    Ordine conservativo: dentro una candela si controlla PRIMA lo stop.
    """
    half = cfg.spread_pts / 2.0
    sign = 1.0 if side == "long" else -1.0
    r_points = abs(entry_price - stop)
    peak = entry_price
    cur_stop = stop
    be_done = False
    partial_done = False
    partial_pnl = 0.0          # punti già incassati col parziale (per-unità)
    remaining = 1.0            # frazione ancora aperta

    def favorable(price):
        return sign * (price - entry_price)

    for t, bar in entry_df.iterrows():
        hi, lo, cl = float(bar["high"]), float(bar["low"]), float(bar["close"])
        # 1) stop / trailing colpito? (conservativo: prima dell'obiettivo)
        stop_hit = (lo <= cur_stop) if side == "long" else (hi >= cur_stop)
        if stop_hit:
            exit_price = cur_stop - sign * half   # esci pagando mezzo spread
            pnl = partial_pnl + remaining * favorable(exit_price)
            return Trade(day, side, None, entry_price, stop, r_points,
                         exit_time=t, exit=exit_price, pnl_points=pnl,
                         r_multiple=pnl / r_points if r_points else 0.0,
                         reason="stop" if not partial_done else "trail")
        # 2) aggiorna il massimo favorevole
        fav_extreme = hi if side == "long" else lo
        if sign * (fav_extreme - peak) > 0:
            peak = fav_extreme
        prof = favorable(fav_extreme)
        # 3) breakeven
        if not be_done and prof >= cfg.be_trigger_pts:
            cur_stop = entry_price
            be_done = True
        # 4) parziale + attiva trailing
        if not partial_done and prof >= cfg.partial_at_pts:
            tp = entry_price + sign * cfg.partial_at_pts
            partial_pnl += cfg.partial_frac * (favorable(tp) - half)
            remaining -= cfg.partial_frac
            partial_done = True
            cur_stop = entry_price   # almeno pari sul resto
        # 5) trailing dopo il parziale
        if partial_done:
            trail = peak - sign * cfg.trail_dist_pts
            if side == "long":
                cur_stop = max(cur_stop, trail)
            else:
                cur_stop = min(cur_stop, trail)

    # chiusura forzata a fine sessione
    last = entry_df.iloc[-1]
    exit_price = float(last["close"]) - sign * half
    pnl = partial_pnl + remaining * favorable(exit_price)
    return Trade(day, side, None, entry_price, stop, r_points,
                 exit_time=entry_df.index[-1], exit=exit_price, pnl_points=pnl,
                 r_multiple=pnl / r_points if r_points else 0.0,
                 reason="session_close")


def run_day(day_df: pd.DataFrame, cfg: DaxOpenConfig) -> Trade | None:
    """Simula un singolo giorno. Ritorna il Trade o None se niente setup."""
    sig = find_signal(day_df, cfg)
    if sig is None:
        return None
    hm = day_df.index.strftime("%H:%M")
    entry_win = day_df[(hm > sig["time"].strftime("%H:%M")) & (hm <= cfg.entry_end)]
    zlow, zhigh = sig["low"], sig["high"]
    prev_close = float(day_df.loc[sig["time"], "close"])
    half = cfg.spread_pts / 2.0

    for t, bar in entry_win.iterrows():
        hi, lo, op, cl = float(bar["high"]), float(bar["low"]), float(bar["open"]), float(bar["close"])
        # LONG: rimbalzo di supporto (venuto dall'alto, tocca la zona, chiude su)
        came_from_above = prev_close > zhigh
        reached_zone_down = lo <= zhigh + cfg.tol_pts and lo >= zlow - cfg.tol_pts
        bullish_reject = cl > op and (cl - lo) >= cfg.confirm_pts
        if came_from_above and reached_zone_down and bullish_reject:
            entry_price = cl + half
            stop = zlow - cfg.stop_buffer_pts
            after = day_df[day_df.index > t]
            after = after[after.index.strftime("%H:%M") <= cfg.session_close]
            if len(after) == 0:
                return None
            return _simulate_trade(after, "long", entry_price, stop, cfg, day_df.index[0].date())
        # SHORT: rimbalzo di resistenza (venuto dal basso, tocca la zona, chiude giù)
        came_from_below = prev_close < zlow
        reached_zone_up = hi >= zlow - cfg.tol_pts and hi <= zhigh + cfg.tol_pts
        bearish_reject = cl < op and (hi - cl) >= cfg.confirm_pts
        if came_from_below and reached_zone_up and bearish_reject:
            entry_price = cl - half
            stop = zhigh + cfg.stop_buffer_pts
            after = day_df[day_df.index > t]
            after = after[after.index.strftime("%H:%M") <= cfg.session_close]
            if len(after) == 0:
                return None
            return _simulate_trade(after, "short", entry_price, stop, cfg, day_df.index[0].date())
        prev_close = cl
    return None


def _simulate_R(entry_df: pd.DataFrame, side: str, entry_price: float,
                stop: float, cfg: DaxOpenConfig, day) -> Trade:
    """Come _simulate_trade ma con soglie in MULTIPLI di R (versione rettangolo).

    R = distanza entry↔stop. A +partial_R → pari + parziale; poi trailing a
    trail_R dal massimo favorevole. Ordine conservativo: prima lo stop.
    """
    half = cfg.spread_pts / 2.0
    sign = 1.0 if side == "long" else -1.0
    r_points = abs(entry_price - stop)
    if r_points <= 0:
        r_points = 1e-9
    peak = entry_price
    cur_stop = stop
    be_done = partial_done = False
    partial_pnl = 0.0
    remaining = 1.0

    def favorable(price):
        return sign * (price - entry_price)

    for t, bar in entry_df.iterrows():
        hi, lo, cl = float(bar["high"]), float(bar["low"]), float(bar["close"])
        stop_hit = (lo <= cur_stop) if side == "long" else (hi >= cur_stop)
        if stop_hit:
            exit_price = cur_stop - sign * half
            pnl = partial_pnl + remaining * favorable(exit_price)
            return Trade(day, side, None, entry_price, stop, r_points,
                         exit_time=t, exit=exit_price, pnl_points=pnl,
                         r_multiple=pnl / r_points,
                         reason="stop" if not partial_done else "trail")
        fav_extreme = hi if side == "long" else lo
        if sign * (fav_extreme - peak) > 0:
            peak = fav_extreme
        prof_R = favorable(fav_extreme) / r_points
        if not be_done and prof_R >= cfg.be_R:
            cur_stop = entry_price
            be_done = True
        if not partial_done and prof_R >= cfg.partial_R:
            tp = entry_price + sign * cfg.partial_R * r_points
            partial_pnl += cfg.partial_frac * (favorable(tp) - half)
            remaining -= cfg.partial_frac
            partial_done = True
            cur_stop = entry_price
        if partial_done:
            trail = peak - sign * cfg.trail_R * r_points
            cur_stop = max(cur_stop, trail) if side == "long" else min(cur_stop, trail)

    last = entry_df.iloc[-1]
    exit_price = float(last["close"]) - sign * half
    pnl = partial_pnl + remaining * favorable(exit_price)
    return Trade(day, side, None, entry_price, stop, r_points,
                 exit_time=entry_df.index[-1], exit=exit_price, pnl_points=pnl,
                 r_multiple=pnl / r_points, reason="session_close")


def run_day_rect(day_df: pd.DataFrame, cfg: DaxOpenConfig) -> Trade | None:
    """Versione 'rettangolo' fedele all'operatività dell'utente.

    Zona = [chiusura, estremo] della candela segnale (rettangolo stretto). Si entra
    quando il prezzo RITORNA a toccare il rettangolo (fill al bordo), stop appena
    dietro il lato opposto del rettangolo → R piccolo. Uscite in R.
    """
    sig = find_signal(day_df, cfg)
    if sig is None:
        return None
    # rettangolo tra chiusura ed estremo (lato della coda/volume)
    day_open = float(day_df.loc[sig["time"], "open"])
    bullish = sig["close"] >= day_open
    if bullish:
        rlow, rhigh = sig["close"], sig["high"]     # rettangolo in alto
    else:
        rlow, rhigh = sig["low"], sig["close"]       # rettangolo in basso
    if rhigh - rlow < 1.0:                            # rettangolo degenere
        return None

    hm = day_df.index.strftime("%H:%M")
    entry_win = day_df[(hm > sig["time"].strftime("%H:%M")) & (hm <= cfg.entry_end)]
    buf = cfg.stop_buffer_pts
    # Elasticità: ordine LIMITE a `tol` punti dal bordo del rettangolo, così scatta
    # anche quando il prezzo ci va solo VICINO senza ritoccarlo esattamente.
    band_long = rhigh + cfg.tol_pts    # buy-limit sopra il rettangolo (supporto)
    band_short = rlow - cfg.tol_pts    # sell-limit sotto il rettangolo (resistenza)
    prev_close = float(day_df.loc[sig["time"], "close"])

    day = day_df.index[0].date()
    session_mask = day_df.index.strftime("%H:%M") <= cfg.session_close
    for t, bar in entry_win.iterrows():
        hi, lo, cl = float(bar["high"]), float(bar["low"]), float(bar["close"])
        side = stop = entry_price = None
        # LONG: veniva dall'alto e scende fino alla fascia del rettangolo (supporto)
        if prev_close > band_long and lo <= band_long:
            side, entry_price, stop = "long", band_long + cfg.spread_pts / 2.0, rlow - buf
        # SHORT: veniva dal basso e sale fino alla fascia del rettangolo (resistenza)
        elif prev_close < band_short and hi >= band_short:
            side, entry_price, stop = "short", band_short - cfg.spread_pts / 2.0, rhigh + buf
        if side is not None:
            after = day_df[(day_df.index > t) & session_mask]
            if len(after) == 0:
                return None
            return _simulate_R(after, side, entry_price, stop, cfg, day)
        prev_close = cl
    return None


def backtest(df: pd.DataFrame, cfg: DaxOpenConfig | None = None, day_fn=run_day) -> dict:
    """Esegue il backtest su tutto il DataFrame M1 (colonna 'time' UTC + OHLCV).

    `day_fn` sceglie la logica giornaliera: run_day (v1) o run_day_rect (v2).
    Ritorna un dizionario con la lista trade e le metriche aggregate.
    """
    cfg = cfg or DaxOpenConfig()
    tz = ZoneInfo(cfg.tz)
    d = df.copy()
    d["time"] = pd.to_datetime(d["time"], utc=True)
    d = d.set_index("time").sort_index()
    d.index = d.index.tz_convert(tz)
    d["day"] = d.index.date

    trades: list[Trade] = []
    for day, g in d.groupby("day"):
        tr = day_fn(g.drop(columns="day"), cfg)
        if tr is not None:
            trades.append(tr)

    return _summarize(trades, cfg)


def _summarize(trades: list[Trade], cfg: DaxOpenConfig) -> dict:
    equity = cfg.start_equity
    curve = [equity]
    for tr in trades:
        risk_amount = cfg.risk_pct * equity
        pnl_money = tr.r_multiple * risk_amount
        equity += pnl_money
        curve.append(equity)
    curve = np.array(curve)

    rmults = np.array([t.r_multiple for t in trades]) if trades else np.array([])
    pts = np.array([t.pnl_points for t in trades]) if trades else np.array([])
    wins = rmults[rmults > 0]
    losses = rmults[rmults < 0]
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    peak = np.maximum.accumulate(curve)
    dd = (curve - peak) / peak

    metrics = {
        "n_trades": len(trades),
        "win_rate": float((rmults > 0).mean()) if len(rmults) else 0.0,
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "expectancy_R": float(rmults.mean()) if len(rmults) else 0.0,
        "avg_points": float(pts.mean()) if len(pts) else 0.0,
        "total_points": float(pts.sum()) if len(pts) else 0.0,
        "max_drawdown": float(dd.min()) if len(dd) else 0.0,
        "total_return": float(curve[-1] / curve[0] - 1) if len(curve) > 1 else 0.0,
        "final_equity": float(curve[-1]),
        "long": int(sum(1 for t in trades if t.side == "long")),
        "short": int(sum(1 for t in trades if t.side == "short")),
        "reasons": {r: int(sum(1 for t in trades if t.reason == r))
                    for r in {t.reason for t in trades}},
    }
    return {"trades": trades, "metrics": metrics, "equity_curve": curve.tolist()}
