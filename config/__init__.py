import json
import os

# Path ke settings.json
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

# Load file JSON
with open(SETTINGS_PATH, "r") as f:
    settings = json.load(f)

# Variabel global yang bisa langsung diimport
TELEGRAM_TOKEN = settings.get("TELEGRAM_TOKEN")
CHAT_ID = settings.get("CHAT_ID")
SYMBOL = settings.get("SYMBOL", "XAUUSD")
TIMEFRAME = settings.get("TIMEFRAME", "M5")
