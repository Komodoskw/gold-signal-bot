
import telebot
import json
import schedule
import time
import threading
from price_feed import get_gold_data
from signal_generator import ema_crossover, rsi, macd, combined_signal, entry_with_levels

with open("config/settings.json") as f:
    settings = json.load(f)

bot = telebot.TeleBot(settings["TELEGRAM_TOKEN"])
CHAT_ID = settings["CHAT_ID"]

def generate_report():
    df = get_gold_data(symbol="XAUUSD=X", interval="5m", period="1d")
    ema_signal = ema_crossover(df)
    rsi_signal = rsi(df)
    macd_signal = macd(df)
    final_signal, price, sl, tp = entry_with_levels(df)

    msg = (
        f"📊 Auto‑Report {settings['SYMBOL']} {settings['TIMEFRAME']}:\n"
        f"EMA: {ema_signal}\n"
        f"RSI: {rsi_signal}\n"
        f"MACD: {macd_signal}\n"
        f"➡️ Rekomendasi Final: {final_signal}\n\n"
        f"🎯 Entry: {final_signal} @ {price}\n"
        f"🛑 SL: {sl}\n"
        f"✅ TP: {tp}"
    )
    bot.send_message(CHAT_ID, msg)

@bot.message_handler(commands=['signal'])
def send_signal(message):
    generate_report()

# Jadwal auto‑report harian (misalnya jam 09:00 WIB dan 15:00 WIB)
schedule.every().day.at("09:00").do(generate_report)
schedule.every().day.at("15:00").do(generate_report)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Jalankan scheduler di thread terpisah
threading.Thread(target=run_schedule).start()

bot.polling()
