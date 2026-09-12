import telebot
import time
import threading
import json
from signal_generator import check_signal
from trade_manager import connect_mt5, execute_order, close_all_positions, set_sl_tp

# --- Load konfigurasi ---
with open("config/settings.json") as f:
    config = json.load(f)

TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
CHAT_ID = config["CHAT_ID"]
SYMBOL = config["SYMBOL"]
TIMEFRAME = config["TIMEFRAME"]
MT5_LOGIN = config["MT5_LOGIN"]
MT5_PASSWORD = config["MT5_PASSWORD"]
MT5_SERVER = config["MT5_SERVER"]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- Connect MT5 ---
connect_mt5(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER)

running = True
default_lot = 0.01
risk_percent = None

def send_msg(text):
    bot.send_message(CHAT_ID, text)

# --- Command Telegram ---
@bot.message_handler(commands=['pause'])
def pause(message):
    global running
    running = False
    send_msg("Bot trading PAUSED")

@bot.message_handler(commands=['resume'])
def resume(message):
    global running
    running = True
    send_msg("Bot trading RESUMED")

@bot.message_handler(commands=['report'])
def report(message):
    import MetaTrader5 as mt5
    info = mt5.account_info()
    send_msg(f"Report:\nBalance: {info.balance}\nEquity: {info.equity}")

@bot.message_handler(commands=['closeall'])
def closeall(message):
    result = close_all_positions()
    send_msg(result)

@bot.message_handler(commands=['setsl'])
def setsl(message):
    args = message.text.split()
    if len(args) < 3:
        send_msg("Format salah. Gunakan: /setsl SYMBOL PRICE")
        return
    symbol = args[1]
    sl_price = float(args[2])
    result = set_sl_tp(symbol, sl=sl_price)
    send_msg(result)

@bot.message_handler(commands=['settp'])
def settp(message):
    args = message.text.split()
    if len(args) < 3:
        send_msg("Format salah. Gunakan: /settp SYMBOL PRICE")
        return
    symbol = args[1]
    tp_price = float(args[2])
    result = set_sl_tp(symbol, tp=tp_price)
    send_msg(result)

@bot.message_handler(commands=['setlot'])
def setlot(message):
    global default_lot, risk_percent
    args = message.text.split()
    if len(args) < 2:
        send_msg("Format salah. Gunakan: /setlot LOTSIZE")
        return
    default_lot = float(args[1])
    risk_percent = None
    send_msg(f"Lot default diubah menjadi {default_lot}")

@bot.message_handler(commands=['risk'])
def setrisk(message
