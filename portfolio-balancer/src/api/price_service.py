from datetime import datetime, timedelta
from portfolio_balancer.src.api.app import db, PriceHistory
from portfolio_balancer.src.data.market_data import fetch_yfinance_data, fetch_coingecko_data, get_latest_yfinance_price, get_latest_coingecko_price
import pandas as pd

class PriceService:
    def __init__(self):
        pass

    def _get_historical_data_from_db(self, ticker, start_date, end_date):
        """Fetches historical price data for a given ticker from the database."""
        return PriceHistory.query.filter(
            PriceHistory.ticker == ticker,
            PriceHistory.date >= start_date,
            PriceHistory.date <= end_date
        ).order_by(PriceHistory.date).all()

    def _save_historical_data_to_db(self, ticker, df):
        """Saves historical price data to the database."""
        for index, row in df.iterrows():
            # Ensure the date is a date object
            date = index.date() if isinstance(index, pd.Timestamp) else index
            price_entry = PriceHistory(
                ticker=ticker,
                date=date,
                close_price=row['Close']
            )
            db.session.add(price_entry)
        db.session.commit()

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

        return [{'date': entry.date.strftime('%Y-%m-%d'), 'close_price': entry.close_price} for entry in cached_data]

    def get_latest_price(self, ticker):
        """
        Retrieves the latest price for a given ticker, fetching from providers if not available.
        """
        # First, try to get the latest price from the database (most recent entry)
        latest_db_entry = PriceHistory.query.filter_by(ticker=ticker).order_by(PriceHistory.date.desc()).first()

        if latest_db_entry and latest_db_entry.date == datetime.now().date():
            return latest_db_entry.close_price
        else:
            print(f"Latest price for {ticker} not in cache or outdated. Fetching from provider.")
            if ticker.isupper() and not ticker.startswith('USD-'):
                latest_price = get_latest_yfinance_price(ticker)
            else:
                coin_id = ticker.lower().replace('usd-', '')
                latest_price = get_latest_coingecko_price(coin_id, 'usd')
            
            if latest_price is not None:
                # Save the latest price to the database
                price_entry = PriceHistory(
                    ticker=ticker,
                    date=datetime.now().date(),
                    close_price=latest_price
                )
                db.session.add(price_entry)
                db.session.commit()
                return latest_price
            else:
                print(f"Could not fetch latest price for {ticker}.")
                return None

price_service = PriceService()