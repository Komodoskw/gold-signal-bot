import telebot
import schedule
import time
from config.settings import TELEGRAM_TOKEN, CHAT_ID, SYMBOL, TIMEFRAME
from src.price_feed import get_gold_data
from src.signal_generator import entry_with_levels

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Command manual: /signal
@bot.message_handler(commands=['signal'])
def send_signal(message):
    df = get_gold_data(symbol=SYMBOL, interval=TIMEFRAME, period="5d")
    if df.empty:
        bot.send_message(CHAT_ID, "⚠️ Data kosong, tidak ada harga terbaru.")
        return
    entry = entry_with_levels(df)
    if entry:
        msg = (
            f"📊 Signal {SYMBOL} {TIMEFRAME}\n"
            f"➡️ {entry['signal']}\n"
            f"🎯 Entry: {entry['entry']}\n"
            f"🛑 SL: {entry['sl']}\n"
            f"✅ TP: {entry['tp']}"
        )
        bot.send_message(CHAT_ID, msg)

# Auto-report harian
def auto_report():
    df = get_gold_data(symbol=SYMBOL, interval=TIMEFRAME, period="5d")
    if df.empty:
        bot.send_message(CHAT_ID, "⚠️ Data kosong, tidak ada harga terbaru.")
        return
    entry = entry_with_levels(df)
    if entry:
        msg = (
            f"📊 Auto-Report {SYMBOL} {TIMEFRAME}\n"
            f"➡️ {entry['signal']}\n"
            f"🎯 Entry: {entry['entry']}\n"
            f"🛑 SL: {entry['sl']}\n"
            f"✅ TP: {entry['tp']}"
        )
        bot.send_message(CHAT_ID, msg)

# Jadwal auto-report (09:00 & 15:00 WIB)
schedule.every().day.at("09:00").do(auto_report)
schedule.every().day.at("15:00").do(auto_report)

# Loop utama
def run_bot():
    while True:
        schedule.run_pending()
        time.sleep(1)
        bot.polling(none_stop=True)

if __name__ == "__main__":
    run_bot()
