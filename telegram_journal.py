"""
Telegram Journal Bot - update jurnal trading langsung lewat chat Telegram.
Dijalankan terjadwal lewat GitHub Actions, mengecek pesan baru tiap kali jalan.

Perintah yang didukung (kirim sebagai chat biasa ke bot Telegram kamu):
  MENANG <cent>     -> catat trade menang, misal: MENANG 150
  KALAH <cent>      -> catat trade kalah, misal: KALAH 100
  BE                -> catat breakeven
  /stats            -> lihat ringkasan (saldo, win rate, progress)
  /saldo <cent>     -> set/reset saldo awal, misal: /saldo 766
  /target <cent>    -> set target saldo, misal: /target 1000
  /help             -> lihat daftar perintah
"""

import os
import json
import requests
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

JOURNAL_FILE = "journal_data.json"
OFFSET_FILE = "journal_offset.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_updates(offset):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 0}
    if offset:
        params["offset"] = offset
    r = requests.get(url, params=params, timeout=20)
    return r.json()


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=15,
    )


def fmt_cent(c):
    sign = "-" if c < 0 else ""
    return f"{sign}{abs(c):,.0f}\u00A2".replace(",", ".")


def fmt_usd(c):
    return f"${c / 100:.2f}"


def compute_summary(journal):
    trades = journal.get("trades", [])
    wins = sum(1 for t in trades if t["result"] == "win")
    losses = sum(1 for t in trades if t["result"] == "loss")
    total_pl = sum(
        t.get("plCents", 0) for t in trades if t["result"] in ("win", "loss", "breakeven")
    )
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else None
    balance = journal.get("startingBalanceCents", 0) + total_pl
    return wins, losses, total_pl, win_rate, balance, len(trades)


def render_table(rows):
    """rows: list of tuple/list, baris pertama = header. Return string tabel rata kolom (monospace)."""
    col_count = len(rows[0])
    widths = [max(len(str(row[i])) for row in rows) for i in range(col_count)]
    lines = []
    for idx, row in enumerate(rows):
        cells = [str(row[i]).ljust(widths[i]) for i in range(col_count)]
        lines.append("  ".join(cells).rstrip())
        if idx == 0:
            lines.append("  ".join("-" * widths[i] for i in range(col_count)))
    return "\n".join(lines)


def format_stats_message(journal):
    trades = journal.get("trades", [])
    wins, losses, total_pl, win_rate, balance, total_trades = compute_summary(journal)
    breakevens = sum(1 for t in trades if t["result"] == "breakeven")
    win_pl = sum(t.get("plCents", 0) for t in trades if t["result"] == "win")
    loss_pl = sum(t.get("plCents", 0) for t in trades if t["result"] == "loss")
    be_pl = sum(t.get("plCents", 0) for t in trades if t["result"] == "breakeven")

    rows = [
        ("Hasil", "Jml", "P/L"),
        ("Menang", str(wins), ("+" + fmt_cent(win_pl)) if wins else "-"),
        ("Kalah", str(losses), fmt_cent(loss_pl) if losses else "-"),
        ("BE", str(breakevens), fmt_cent(be_pl) if breakevens else "-"),
    ]
    table = render_table(rows)
    wr_text = f"{win_rate:.0f}%" if win_rate is not None else "-"

    lines = [
        "📊 <b>Ringkasan Jurnal</b>",
        f"<pre>{table}</pre>",
        f"Saldo sekarang: {fmt_usd(balance)} ({fmt_cent(balance)})",
        f"Win rate: {wr_text}",
        f"Total P/L: {'+' if total_pl >= 0 else ''}{fmt_cent(total_pl)}",
    ]
    target = journal.get("targetBalanceCents")
    start = journal.get("startingBalanceCents")
    if target and start is not None and target > start:
        progress = max(0, min(1, (balance - start) / (target - start)))
        lines.append(f"Progres ke target {fmt_usd(target)}: {progress * 100:.0f}%")
    return "\n".join(lines)


def format_history_message(journal, limit=10):
    trades = journal.get("trades", [])
    if not trades:
        return "Belum ada trade tercatat. Ketik MENANG/KALAH/BE dulu buat mulai catat."

    sorted_trades = sorted(trades, key=lambda t: t.get("dateTime", ""), reverse=True)[:limit]
    result_label = {"win": "Menang", "loss": "Kalah", "breakeven": "BE", "pending": "Jalan"}

    rows = [("Tgl", "Hasil", "P/L")]
    for t in sorted_trades:
        dt = t.get("dateTime", "")
        try:
            date_str = datetime.fromisoformat(dt).strftime("%d/%m")
        except ValueError:
            date_str = dt[:5] if dt else "-"
        label = result_label.get(t["result"], t["result"])
        pl = t.get("plCents", 0)
        pl_str = ("+" + fmt_cent(pl)) if (t["result"] != "pending" and pl > 0) else (
            fmt_cent(pl) if t["result"] != "pending" else "-"
        )
        rows.append((date_str, label, pl_str))

    table = render_table(rows)
    return f"🧾 <b>Riwayat Trade</b> (terakhir {len(sorted_trades)})\n<pre>{table}</pre>"


def process_command(text, journal):
    text = text.strip()
    if not text:
        return None

    parts = text.split()
    cmd = parts[0].lower().lstrip("/")

    if cmd in ("menang", "win"):
        if len(parts) < 2:
            return "Format: MENANG <jumlah_cent>, misal: MENANG 150"
        try:
            pl = abs(float(parts[1]))
        except ValueError:
            return "Jumlah cent-nya harus angka, misal: MENANG 150"
        journal["trades"].append(
            {"result": "win", "plCents": pl, "dateTime": now_iso(), "note": "via Telegram"}
        )
        return f"✅ Dicatat: Menang +{fmt_cent(pl)}\n\n" + format_stats_message(journal)

    if cmd in ("kalah", "loss"):
        if len(parts) < 2:
            return "Format: KALAH <jumlah_cent>, misal: KALAH 100"
        try:
            pl = abs(float(parts[1]))
        except ValueError:
            return "Jumlah cent-nya harus angka, misal: KALAH 100"
        journal["trades"].append(
            {"result": "loss", "plCents": -pl, "dateTime": now_iso(), "note": "via Telegram"}
        )
        return f"❌ Dicatat: Kalah -{fmt_cent(pl)}\n\n" + format_stats_message(journal)

    if cmd in ("be", "breakeven"):
        journal["trades"].append(
            {"result": "breakeven", "plCents": 0, "dateTime": now_iso(), "note": "via Telegram"}
        )
        return "➖ Dicatat: Breakeven\n\n" + format_stats_message(journal)

    if cmd in ("stats", "statistik"):
        return format_stats_message(journal)

    if cmd in ("riwayat", "history"):
        return format_history_message(journal)

    if cmd in ("saldo", "setsaldo"):
        if len(parts) < 2:
            return "Format: /saldo <jumlah_cent>, misal: /saldo 766"
        try:
            val = float(parts[1])
        except ValueError:
            return "Jumlah cent-nya harus angka, misal: /saldo 766"
        journal["startingBalanceCents"] = val
        return f"✅ Saldo awal diset ke {fmt_cent(val)}"

    if cmd == "target":
        if len(parts) < 2:
            return "Format: /target <jumlah_cent>, misal: /target 1000"
        try:
            val = float(parts[1])
        except ValueError:
            return "Jumlah cent-nya harus angka, misal: /target 1000"
        journal["targetBalanceCents"] = val
        return f"✅ Target diset ke {fmt_cent(val)}"

    if cmd in ("help", "bantuan", "start"):
        return (
            "Perintah yang tersedia:\n"
            "MENANG <cent> - catat trade menang\n"
            "KALAH <cent> - catat trade kalah\n"
            "BE - catat breakeven\n"
            "/stats - lihat ringkasan (tabel)\n"
            "/riwayat - lihat 10 trade terakhir (tabel)\n"
            "/saldo <cent> - set saldo awal\n"
            "/target <cent> - set target saldo"
        )

    return None  # bukan perintah yang dikenali, diamkan saja


def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Token/Chat ID Telegram belum lengkap.")
        return

    journal = load_json(JOURNAL_FILE, {"startingBalanceCents": 0, "targetBalanceCents": None, "trades": []})
    offset_data = load_json(OFFSET_FILE, {"last_update_id": None})

    result = get_updates(offset_data.get("last_update_id"))
    if not result.get("ok"):
        print("Gagal ambil update Telegram:", result)
        return

    updates = result.get("result", [])
    if not updates:
        print("Tidak ada pesan baru.")
        return

    changed = False
    for update in updates:
        offset_data["last_update_id"] = update["update_id"] + 1
        message = update.get("message")
        if not message or "text" not in message:
            continue
        # hanya proses pesan dari chat ID yang dikonfigurasi (keamanan dasar)
        if str(message["chat"]["id"]) != str(TELEGRAM_CHAT_ID):
            continue

        reply = process_command(message["text"], journal)
        if reply:
            send_message(reply)
            changed = True

    save_json(OFFSET_FILE, offset_data)
    if changed:
        save_json(JOURNAL_FILE, journal)
        print("Jurnal terupdate.")
    else:
        print("Tidak ada perubahan jurnal.")


if __name__ == "__main__":
    main()
