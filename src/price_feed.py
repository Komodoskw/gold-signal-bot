import yfinance as yf
import pandas as pd

def get_gold_data(symbol="XAUUSD=X", interval="5m", period="1d"):
    try:
        df = yf.download(
            tickers=symbol,
            interval=interval,
            period=period
        )

        # Pastikan dataframe tidak kosong
        if df.empty:
            print("⚠️ Data kosong, tidak ada harga terbaru.")
            return pd.DataFrame()

        # Reset index agar kolom datetime rapi
        df.reset_index(inplace=True)

        # Rename kolom agar konsisten
        df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }, inplace=True)

        return df

    except Exception as e:
        print(f"⚠️ Error ambil data: {e}")
        return pd.DataFrame()
