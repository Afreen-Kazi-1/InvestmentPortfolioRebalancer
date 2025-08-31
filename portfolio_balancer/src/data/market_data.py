import yfinance as yf
from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta
import time
import functools
import os
import json

# Define cache directory
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Simple in-memory cache for API responses
_api_cache = {}
_API_CACHE_TTL_SECONDS = 3600 # Cache for 1 hour

# On-disk cache for API responses
def on_disk_cache(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a unique filename based on function name and arguments
        cache_key = f"{func.__name__}_{hash(frozenset(args))}_{hash(frozenset(kwargs.items()))}"
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")

        # Check if cached data exists and is still valid
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                timestamp = data.get('timestamp')
                if time.time() - timestamp < _API_CACHE_TTL_SECONDS:
                    print(f"On-disk cache hit for {func.__name__}")
                    return data['value']
                else:
                    print(f"On-disk cache expired for {func.__name__}")

        # If not cached or expired, call the original function and cache the result
        print(f"On-disk cache miss for {func.__name__}. Fetching data...")
        value = func(*args, **kwargs)
        with open(cache_file, 'w') as f:
            json.dump({'timestamp': time.time(), 'value': value}, f)
        return value
    return wrapper

def cached_api_call(func):
    """Decorator to cache API responses with a time-to-live."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (func.__name__, args, tuple(sorted(kwargs.items())))
        
        if key in _api_cache:
            timestamp, value = _api_cache[key]
            if time.time() - timestamp < _API_CACHE_TTL_SECONDS:
                print(f"In-memory cache hit for {func.__name__} with key {key}")
                return value
            else:
                print(f"In-memory cache expired for {func.__name__} with key {key}")
                del _api_cache[key]
        
        print(f"In-memory cache miss for {func.__name__} with key {key}. Fetching data...")
        value = func(*args, **kwargs)
        _api_cache[key] = (time.time(), value)
        return value
    return wrapper

@on_disk_cache
@cached_api_call
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

@on_disk_cache
@cached_api_call
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

@on_disk_cache
@cached_api_call
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

@on_disk_cache
@cached_api_call
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