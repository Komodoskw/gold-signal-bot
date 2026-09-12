import yfinance as yf
import pandas as pd

def get_gold_data(symbol="XAUUSD=X", interval="5m", period="1d"):
    data = yf.download(tickers=symbol, interval=interval, period=period)
    df = pd.DataFrame(data)
    df.reset_index(inplace=True)
    df.rename(columns={"Close":"close"}, inplace=True)
    return df
