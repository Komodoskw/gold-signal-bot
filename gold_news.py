"""
Gold News Bot - kirim berita relevan XAUUSD/gold ke Telegram.
Sumber: Finnhub (free tier), difilter pakai kata kunci yang relevan
buat pergerakan harga gold (Fed, inflasi, dollar, geopolitik, dll).
Dijalankan terjadwal lewat GitHub Actions.
"""

import os
import json
import requests

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

NEWS_STATE_FILE = "news_seen.json"
MAX_SEEN_IDS = 300      # jumlah id berita lama yang disimpan biar tidak dikirim ulang
MAX_SEND_PER_RUN = 3    # batas jumlah berita dikirim tiap kali jalan, biar tidak banjir

KEYWORDS = [
    "gold", "xau", "bullion", "fed", "federal reserve", "interest rate",
    "inflation", "cpi", "nonfarm", "payroll", "jobs report", "safe haven",
    "dollar index", "dxy", "geopolitical", "rate cut", "rate hike",
    "fomc", "powell", "treasury yield",
]


def load_state():
    if os.path.exists(NEWS_STATE_FILE):
        with open(NEWS_STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen_ids": []}


def save_state(state):
    with open(NEWS_STATE_FILE, "w") as f:
        json.dump(state, f)


def fetch_news():
    url = "https://finnhub.io/api/v1/news"
    params = {"category": "general", "token": FINNHUB_API_KEY}
    r = requests.get(url, params=params, timeout=20)
    if r.status_code != 200:
        print("Gagal ambil berita:", r.status_code, r.text)
        return []
    return r.json()


def is_relevant(article):
    text = (article.get("headline", "") + " " + article.get("summary", "")).lower()
    return any(kw in text for kw in KEYWORDS)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, data=payload, timeout=15)
    if r.status_code != 200:
        print("Gagal kirim Telegram:", r.text)


def format_news_message(article):
    headline = article.get("headline", "").strip()
    summary = article.get("summary", "").strip()
    source = article.get("source", "")
    url = article.get("url", "")
    if len(summary) > 220:
        summary = summary[:220].rsplit(" ", 1)[0] + "..."
    parts = [f"📰 <b>{headline}</b>"]
    if summary:
        parts.append(summary)
    if source:
        parts.append(f"Sumber: {source}")
    if url:
        parts.append(url)
    return "\n".join(parts)


def main():
    if not FINNHUB_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Env var belum lengkap (Finnhub key / Telegram token / chat id).")
        return

    state = load_state()
    seen_ids = state.get("seen_ids", [])
    seen_set = set(seen_ids)

    articles = fetch_news()
    if not articles:
        print("Tidak ada berita diambil.")
        return

    relevant = [a for a in articles if a.get("id") not in seen_set and is_relevant(a)]
    relevant.sort(key=lambda a: a.get("datetime", 0))  # yang lebih lama dulu

    to_send = relevant[-MAX_SEND_PER_RUN:] if len(relevant) > MAX_SEND_PER_RUN else relevant

    for article in to_send:
        send_telegram(format_news_message(article))
        seen_ids.append(article.get("id"))

    if len(seen_ids) > MAX_SEEN_IDS:
        seen_ids = seen_ids[-MAX_SEEN_IDS:]
    state["seen_ids"] = seen_ids
    save_state(state)

    if to_send:
        print(f"{len(to_send)} berita terkirim.")
    else:
        print("Tidak ada berita relevan baru.")


if __name__ == "__main__":
    main()
