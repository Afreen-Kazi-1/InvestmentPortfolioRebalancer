import yfinance as yf
from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta

def fetch_yfinance_data(ticker, start_date, end_date):
    """Fetches historical OHLCV data for a given stock/ETF ticker using yfinance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            return data[['Open', 'High', 'Low', 'Close', 'Volume']]
        else:
            print(f"No data found for {ticker} from {start_date} to {end_date}")
            return None
    except Exception as e:
        print(f"Error fetching yfinance data for {ticker}: {e}")
        return None

def fetch_coingecko_data(coin_id, vs_currency, days):
    """Fetches historical price data for a given cryptocurrency using CoinGecko API."""
    cg = CoinGeckoAPI()
    try:
        data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
        if data and 'prices' in data:
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            # CoinGecko only provides close price for historical data
            df.rename(columns={'price': 'Close'}, inplace=True)
            df['Open'] = df['High'] = df['Low'] = df['Volume'] = None # Placeholder for OHLCV
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        else:
            print(f"No data found for {coin_id} from CoinGecko.")
            return None
    except Exception as e:
        print(f"Error fetching CoinGecko data for {coin_id}: {e}")
        return None

def get_latest_yfinance_price(ticker):
    """Fetches the latest closing price for a given stock/ETF ticker using yfinance."""
    try:
        data = yf.download(ticker, period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            print(f"No latest price found for {ticker}")
            return None
    except Exception as e:
        print(f"Error fetching latest yfinance price for {ticker}: {e}")
        return None

def get_latest_coingecko_price(coin_id, vs_currency):
    """Fetches the latest price for a given cryptocurrency using CoinGecko API."""
    cg = CoinGeckoAPI()
    try:
        data = cg.get_price(ids=coin_id, vs_currencies=vs_currency)
        if data and coin_id in data and vs_currency in data[coin_id]:
            return data[coin_id][vs_currency]
        else:
            print(f"No latest price found for {coin_id} in {vs_currency}")
            return None
    except Exception as e:
        print(f"Error fetching latest CoinGecko price for {coin_id}: {e}")
        return None