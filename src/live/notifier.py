"""Notifiche Telegram del bot di trading.

Manda un messaggio su Telegram ogni volta che il bot fa qualcosa (BUY/CLOSE) e un
riepilogo a fine giornata. Si configura con due variabili d'ambiente (in .env):
  TELEGRAM_BOT_TOKEN  (creato con @BotFather)
  TELEGRAM_CHAT_ID    (l'id della chat/utente a cui scrivere)

Se non è configurato, è un NO-OP silenzioso: il bot funziona lo stesso, senza avvisi.
Testo SEMPRE plain-text (Telegram non rende bene il Markdown): niente asterischi/
backtick, enfasi con emoji.
"""
from __future__ import annotations

import os

import requests


class TelegramNotifier:
    """Invio messaggi Telegram. Silenzioso e non-bloccante se non configurato."""

    API = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, token: str | None = None, chat_id: str | None = None,
                 *, timeout: float = 10.0):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, text: str) -> bool:
        """Invia `text`. Ritorna True se inviato, False se disabilitato o fallito.

        Non solleva mai: un problema di notifica non deve fermare il trading.
        """
        if not self.enabled:
            return False
        try:
            r = requests.post(
                self.API.format(token=self.token),
                json={"chat_id": self.chat_id, "text": text,
                      "disable_web_page_preview": True},
                timeout=self.timeout,
            )
            return r.ok
        except requests.RequestException:
            return False


def format_action(instrument: str, action: str, reason: str, close: float,
                  stop: float | None = None, qty: int | None = None,
                  dry_run: bool = False) -> str:
    """Messaggio plain-text per una singola azione (BUY/CLOSE/HOLD).

    Funzione pura: testabile offline, nessuna rete.
    """
    icon = {"BUY": "🟢", "CLOSE": "🔴", "HOLD": "⚪️"}.get(action, "•")
    tag = " [PROVA]" if dry_run else ""
    lines = [f"{icon} {action} {instrument}{tag}", f"prezzo {close:,.1f} — {reason}"]
    if action == "BUY":
        if qty is not None:
            lines.append(f"quantità {qty}")
        if stop is not None:
            lines.append(f"stop {stop:,.1f}")
    return "\n".join(lines)


def format_summary(date: str, actions: list[dict], equity: float,
                   dry_run: bool = False) -> str:
    """Riepilogo di fine run (una riga per azione non-HOLD, o 'nessuna azione')."""
    tag = " [PROVA]" if dry_run else ""
    ops = [a for a in actions if a.get("action") in ("BUY", "CLOSE")]
    head = f"📋 Bot mean-reversion {date}{tag}\nequity {equity:,.0f}"
    if not ops:
        return head + f"\nnessuna operazione (controllati {len(actions)} strumenti, tutti in attesa)"
    body = "\n".join(f"{'🟢' if a['action']=='BUY' else '🔴'} {a['action']} "
                     f"{a['instrument']} @ {a['close']:,.1f}" for a in ops)
    return head + "\n" + body
