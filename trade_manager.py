import MetaTrader5 as mt5

def connect_mt5(login, password, server):
    if not mt5.initialize(login=login, password=password, server=server):
        print("❌ MT5 gagal connect")
        return False
    print("✅ MT5 berhasil connect")
    return True

def execute_order(symbol, signal, lot, deviation=20):
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if signal == "BUY" else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": deviation,
        "magic": 123456,
        "comment": "AutoTradeSignal",
    }

    result = mt5.order_send(request)
    return result

def close_all_positions():
    positions = mt5.positions_get()
    if not positions:
        return "Tidak ada posisi aktif."
    for pos in positions:
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": pos.ticket,
            "price": mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask,
            "deviation": 20,
            "magic": 123456,
            "comment": "CloseAll",
        }
        mt5.order_send(close_request)
    return "Semua posisi ditutup."

def set_sl_tp(symbol, sl=None, tp=None):
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return f"Tidak ada posisi aktif untuk {symbol}"
    for pos in positions:
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": pos.ticket,
            "sl": sl if sl else pos.sl,
            "tp": tp if tp else pos.tp,
            "magic": 123456,
            "comment": "ModifySLTP",
        }
        mt5.order_send(modify_request)
    return f"SL/TP {symbol} diperbarui."
