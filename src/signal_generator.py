import pandas as pd
import numpy as np

def ema_crossover(data, short=9, long=21):
    data['EMA_short'] = data['close'].ewm(span=short).mean()
    data['EMA_long'] = data['close'].ewm(span=long).mean()
    if data['EMA_short'].iloc[-1] > data['EMA_long'].iloc[-1]:
        return "BUY"
    elif data['EMA_short'].iloc[-1] < data['EMA_long'].iloc[-1]:
        return "SELL"
    return "HOLD"

def rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    if data['RSI'].iloc[-1] > 70:
        return "SELL"
    elif data['RSI'].iloc[-1] < 30:
        return "BUY"
    return "HOLD"

def macd(data, short=12, long=26, signal=9):
    data['EMA_short'] = data['close'].ewm(span=short).mean()
    data['EMA_long'] = data['close'].ewm(span=long).mean()
    data['MACD'] = data['EMA_short'] - data['EMA_long']
    data['Signal'] = data['MACD'].ewm(span=signal).mean()
    if data['MACD'].iloc[-1] > data['Signal'].iloc[-1]:
        return "BUY"
    elif data['MACD'].iloc[-1] < data['Signal'].iloc[-1]:
        return "SELL"
    return "HOLD"

def combined_signal(data):
    signals = [ema_crossover(data), rsi(data), macd(data)]
    buy_count = signals.count("BUY")
    sell_count = signals.count("SELL")
    if buy_count > sell_count:
        return "BUY"
    elif sell_count > buy_count:
        return "SELL"
    return "HOLD"

def entry_with_levels(data):
    final_signal = combined_signal(data)
    price = data['close'].iloc[-1]

    if final_signal == "BUY":
        sl = round(price - 2.0, 2)   # contoh SL 2 USD di bawah harga
        tp = round(price + 3.0, 2)   # contoh TP 3 USD di atas harga
    elif final_signal == "SELL":
        sl = round(price + 2.0, 2)
        tp = round(price - 3.0, 2)
    else:
        sl = None
        tp = None

    return final_signal, price, sl, tp
