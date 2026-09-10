"""
Gold Signal Bot - XAUUSD M5 RSI+MACD -> Telegram
Dijalankan terjadwal (tiap 5 menit) lewat GitHub Actions.
Tidak melakukan auto-entry - hanya mengirim SINYAL (entry, SL, TP) ke Telegram.
"""

import os
import json
import sys
import requests
import pandas as pd

# ============== KONFIGURASI ==============
SYMBOL = "XAU/USD"
INTERVAL = "5min"
RSI_PERIOD = 14
RSI_MIDLINE = 50.0
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

SL_USD = 3.0   # jarak Stop Loss dalam USD (harga gold), sesuaikan sesuai selera
TP_USD = 6.0   # jarak Take Profit dalam USD

H1_INTERVAL = "1h"
H1_EMA_FAST = 50
H1_EMA_SLOW = 200

STATE_FILE = "state.json"

TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_candles():
    """Ambil data candle XAUUSD M5 dari TwelveData."""
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "outputsize": 100,
        "apikey": TWELVEDATA_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=20)
    data = resp.json()

    if data.get("status") == "error" or "values" not in data:
        print("Gagal ambil data:", data)
        sys.exit(1)

    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["close"] = df["close"].astype(float)
    df = df.sort_values("datetime").reset_index(drop=True)  # urut lama -> baru
    return df


def fetch_h1_trend():
    """
    Ambil data H1 dan tentukan arah trend besar pakai EMA50 vs EMA200.
    Return "bullish", "bearish", atau None kalau data belum cukup.
    """
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": H1_INTERVAL,
        "outputsize": H1_EMA_SLOW + 20,
        "apikey": TWELVEDATA_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=20)
    data = resp.json()

    if data.get("status") == "error" or "values" not in data:
        print("Gagal ambil data H1:", data)
        return None

    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["close"] = df["close"].astype(float)
    df = df.sort_values("datetime").reset_index(drop=True)

    if len(df) < H1_EMA_SLOW + 5:
        return None  # data H1 belum cukup buat EMA200 stabil

    ema_fast = df["close"].ewm(span=H1_EMA_FAST, adjust=False).mean()
    ema_slow = df["close"].ewm(span=H1_EMA_SLOW, adjust=False).mean()

    # pakai candle H1 yang sudah close (-2), skip yang mungkin masih jalan (-1)
    if ema_fast.iloc[-2] > ema_slow.iloc[-2]:
        return "bullish"
    elif ema_fast.iloc[-2] < ema_slow.iloc[-2]:
        return "bearish"
    return None


def calculate_indicators(df):
    """Hitung RSI dan MACD, tambahkan sebagai kolom baru."""
    close = df["close"]

    # RSI (Wilder smoothing)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD).mean()
    avg_loss = loss.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=MACD_SIGNAL, adjust=False).mean()

    return df


def detect_signal(df, h1_trend):
    """
    Pakai 2 candle yang SUDAH close (index -2 dan -3), skip candle terakhir
    (-1) karena kemungkinan belum close saat data diambil.
    Sinyal hanya diambil kalau searah dengan trend H1 (EMA50 vs EMA200).
    """
    if len(df) < MACD_SLOW + MACD_SIGNAL + 5:
        return None  # data belum cukup buat hitung indikator stabil

    if h1_trend is None:
        return None  # data H1 belum cukup, skip demi keamanan

    prev = df.iloc[-3]
    curr = df.iloc[-2]

    bullish_cross = prev["macd"] < prev["macd_signal"] and curr["macd"] > curr["macd_signal"]
    bearish_cross = prev["macd"] > prev["macd_signal"] and curr["macd"] < curr["macd_signal"]

    rsi_bullish = curr["rsi"] > RSI_MIDLINE
    rsi_bearish = curr["rsi"] < RSI_MIDLINE

    signal_time = str(curr["datetime"])
    entry_price = float(curr["close"])

    # BUY hanya kalau trend H1 juga bullish, SELL hanya kalau trend H1 bearish
    if bullish_cross and rsi_bullish and h1_trend == "bullish":
        return {
            "type": "BUY",
            "time": signal_time,
            "entry": entry_price,
            "sl": round(entry_price - SL_USD, 2),
            "tp": round(entry_price + TP_USD, 2),
            "rsi": round(float(curr["rsi"]), 1),
            "h1_trend": h1_trend,
        }
    elif bearish_cross and rsi_bearish and h1_trend == "bearish":
        return {
            "type": "SELL",
            "time": signal_time,
            "entry": entry_price,
            "sl": round(entry_price + SL_USD, 2),
            "tp": round(entry_price - TP_USD, 2),
            "rsi": round(float(curr["rsi"]), 1),
            "h1_trend": h1_trend,
        }
    return None


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_signal_time": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, data=payload, timeout=15)
    if r.status_code != 200:
        print("Gagal kirim Telegram:", r.text)


def format_message(signal):
    emoji = "🟢 BUY" if signal["type"] == "BUY" else "🔴 SELL"
    trend_label = "Bullish 📈" if signal["h1_trend"] == "bullish" else "Bearish 📉"
    return (
        f"{emoji} XAUUSD (M5)\n"
        f"Entry: {signal['entry']}\n"
        f"SL: {signal['sl']}\n"
        f"TP: {signal['tp']}\n"
        f"RSI: {signal['rsi']}\n"
        f"Trend H1: {trend_label}\n"
        f"Candle: {signal['time']} UTC\n\n"
        f"⚠️ Sinyal otomatis, entry manual di MT5. Harga real bisa sedikit beda "
        f"dari harga di sinyal ini, cek ulang sebelum entry."
    )


def main():
    if not TWELVEDATA_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Environment variable belum lengkap (API key / Telegram token / chat id).")
        sys.exit(1)

    h1_trend = fetch_h1_trend()
    print("Trend H1 saat ini:", h1_trend)

    df = fetch_candles()
    df = calculate_indicators(df)
    signal = detect_signal(df, h1_trend)

    if signal is None:
        print("Tidak ada sinyal baru saat ini (atau tidak searah trend H1).")
        return

    state = load_state()
    if state.get("last_signal_time") == signal["time"]:
        print("Sinyal untuk candle ini sudah pernah dikirim, skip.")
        return

    send_telegram(format_message(signal))
    state["last_signal_time"] = signal["time"]
    save_state(state)
    print("Sinyal terkirim:", signal)


if __name__ == "__main__":
    main()
