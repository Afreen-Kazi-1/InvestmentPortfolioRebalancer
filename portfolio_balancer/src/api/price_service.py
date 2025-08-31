from datetime import datetime, timedelta
from portfolio_balancer.src.api.models import PriceHistory, LatestPrice
from portfolio_balancer.src.data.market_data import fetch_yfinance_data, fetch_coingecko_data, get_latest_yfinance_price, get_latest_coingecko_price
import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime, timedelta

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PriceService:
    def __init__(self):
        pass

    def _prices_to_dataframe(self, prices_dict):
        """Converts a dictionary of prices {date: price} to a pandas DataFrame."""
        df = pd.DataFrame.from_dict(prices_dict, orient='index', columns=['close_price'])
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df

    def _get_historical_data_from_db(self, ticker, start_date, end_date):
        """Fetches historical price data for a given ticker from the database."""
        response = supabase.table('price_history').select("*").eq("ticker", ticker).gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).execute()
        return [PriceHistory(ticker=item['ticker'], date=datetime.strptime(item['date'], '%Y-%m-%d').date(), close=item['close']) for item in response.data]

    def _save_historical_data_to_db(self, ticker, df):
        """Saves historical price data to the database."""
        data_to_insert = []
        for index, row in df.iterrows():
            date = index.date() if isinstance(index, pd.Timestamp) else index
            data_to_insert.append({
                "ticker": ticker,
                "date": date.isoformat(),
                "close": row['Close'] if 'Close' in row else row['close_price'] # Handle both 'Close' and 'close_price'
            })
        if data_to_insert:
            response = supabase.table('price_history').insert(data_to_insert).execute()
            if response.data:
                print(f"Saved {len(response.data)} price entries to Supabase.")
            else:
                print(f"Failed to save price entries to Supabase: {response.error}")

    def get_historical_prices(self, ticker, start_date_str, end_date_str):
        """
        Retrieves historical prices for a given ticker, fetching from providers if not cached.
        start_date_str and end_date_str should be in 'YYYY-MM-DD' format.
        """
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        cached_data = self._get_historical_data_from_db(ticker, start_date, end_date)
        cached_dates = {entry.date for entry in cached_data}

        # Check for missing dates
        all_dates = set()
        current_date = start_date
        while current_date <= end_date:
            all_dates.add(current_date)
            current_date += timedelta(days=1)
        
        missing_dates = list(all_dates - cached_dates)
        
        if missing_dates:
            print(f"Missing data for {ticker} on dates: {missing_dates}. Fetching from provider.")
            # Determine if it's a stock/ETF or crypto based on ticker format (simple heuristic)
            if ticker.isupper() and not ticker.startswith('USD-'): # Assuming crypto tickers might be lower or have specific prefixes
                fetched_df = fetch_yfinance_data(ticker, start_date, end_date)
            else:
                # For crypto, CoinGecko needs a coin_id (e.g., 'bitcoin' for BTC).
                # This is a simplification; a real app would need a mapping.
                coin_id = ticker.lower().replace('usd-', '') # Example: 'BTC-USD' -> 'btc'
                fetched_df = fetch_coingecko_data(coin_id, 'usd', (end_date - start_date).days + 1)
            
            if fetched_df is not None and not fetched_df.empty:
                self._save_historical_data_to_db(ticker, fetched_df)
                # Re-fetch all data including newly saved ones
                cached_data = self._get_historical_data_from_db(ticker, start_date, end_date)
            else:
                print(f"Could not fetch missing data for {ticker}.")

        return [{'date': entry.date.strftime('%Y-%m-%d'), 'close': entry.close} for entry in cached_data]

    def get_latest_price(self, ticker):
        """
        Retrieves the latest price for a given ticker, fetching from providers if not available.
        """
        # First, try to get the latest price from Supabase's 'latest_price' table
        response = supabase.table('latest_price').select("*").eq("ticker", ticker).limit(1).execute()
        latest_db_entry_data = response.data[0] if response.data else None
        latest_db_entry = LatestPrice(ticker=latest_db_entry_data['ticker'], price=latest_db_entry_data['price'], as_of=datetime.fromisoformat(latest_db_entry_data['as_of'])) if latest_db_entry_data else None

        if latest_db_entry and latest_db_entry.as_of.date() == datetime.now().date():
            return latest_db_entry.price
        else:
            print(f"Latest price for {ticker} not in cache or outdated. Fetching from provider.")
            if ticker.isupper() and not ticker.startswith('USD-'):
                fetched_price = get_latest_yfinance_price(ticker)
            else:
                coin_id = ticker.lower().replace('usd-', '')
                fetched_price = get_latest_coingecko_price(coin_id, 'usd')
            
            if fetched_price is not None:
                # Upsert the latest price to the 'latest_price' table
                price_entry = {
                    "ticker": ticker,
                    "price": fetched_price,
                    "as_of": datetime.now().isoformat()
                }
                response = supabase.table('latest_price').upsert(price_entry).execute()
                if response.data:
                    print(f"Upserted latest price for {ticker} to Supabase.")
                else:
                    print(f"Failed to upsert latest price for {ticker} to Supabase: {response.error}")
                return fetched_price
            else:
                print(f"Could not fetch latest price for {ticker}.")
                return None

price_service = PriceService()