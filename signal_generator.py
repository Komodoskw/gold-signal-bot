import MetaTrader5 as mt5
import numpy as np

def check_signal(symbol="XAUUSD", timeframe=mt5.TIMEFRAME_M5, n=50):
    # Ambil data harga
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) < 21:
        return None

    closes = np.array([r.close for r in rates], dtype=float)

    # Hitung EMA sederhana (pakai rata-rata untuk contoh)
    ema_fast = np.mean(closes[-9:])
    ema_slow = np.mean(closes[-21:])

    # Logika sinyal
    if ema_fast > ema_slow:
        return "BUY"
    elif ema_fast < ema_slow:
        return "SELL"
    else:
        return None
