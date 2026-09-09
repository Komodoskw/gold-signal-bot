import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

message = (
    "🟢 BUY XAUUSD (M5) [CONTOH]\n"
    "Entry: 2385.40\n"
    "SL: 2382.40\n"
    "TP: 2391.40\n"
    "RSI: 58.3\n"
    "Candle: 2026-09-09 10:25:00 UTC\n\n"
    "⚠️ Ini contoh format sinyal (test), bukan sinyal asli."
)

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
print(resp.status_code, resp.text)
