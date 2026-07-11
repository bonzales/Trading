"""Test della formattazione dei messaggi Telegram (offline, nessuna rete)."""
from src.live.notifier import TelegramNotifier, format_action, format_summary


def test_notifier_disabilitato_e_noop():
    n = TelegramNotifier(token="", chat_id="")
    assert n.enabled is False
    assert n.send("ciao") is False  # non solleva, ritorna False


def test_format_action_buy():
    msg = format_action("US500", "BUY", "RSI2 basso", 5000.0, stop=4950.0, qty=3)
    assert "BUY US500" in msg and "5,000" in msg
    assert "stop" in msg and "quantità 3" in msg
    assert "*" not in msg and "`" not in msg  # plain text: niente markdown


def test_format_action_dry_run_tag():
    msg = format_action("DAX", "CLOSE", "RSI risalito", 25000.0, dry_run=True)
    assert "[PROVA]" in msg and "CLOSE DAX" in msg


def test_format_summary_nessuna_operazione():
    acts = [{"instrument": "US500", "action": "HOLD", "close": 5000.0}]
    msg = format_summary("2026-07-11", acts, 10000.0)
    assert "nessuna operazione" in msg


def test_format_summary_con_operazioni():
    acts = [{"instrument": "US500", "action": "BUY", "close": 5000.0},
            {"instrument": "DAX", "action": "HOLD", "close": 25000.0}]
    msg = format_summary("2026-07-11", acts, 10000.0)
    assert "BUY US500" in msg and "DAX" not in msg  # solo le operazioni, non gli HOLD
