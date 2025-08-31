from datetime import datetime, timedelta
from portfolio_balancer.src.api.models import Asset # Removed Portfolio as it's not used
from portfolio_balancer.src.api.price_service import PriceService
from portfolio_balancer.src.evaluation.metrics import calculate_volatility, calculate_correlation # Corrected import path
from supabase import create_client, Client
import os
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

price_service = PriceService()

def precompute_common_stats():
    """
    Nightly job to precompute common financial statistics (volatility, correlations)
    for all unique assets across all portfolios.
    """
    print("Starting nightly job: Precomputing common stats...")

    # Fetch all portfolios to get unique assets
    # Fetch all holdings to get unique assets, as 'portfolios' table does not exist
    response = supabase.table('holding').select("ticker").execute()
    unique_tickers = set()
    if response.data:
        for holding_data in response.data:
            if 'ticker' in holding_data:
                unique_tickers.add(holding_data['ticker'])
    
    tickers = list(unique_tickers)

    tickers = list(unique_assets.keys())

    # Fetch historical prices for all unique tickers for the last year
    # This assumes we need a year's worth of data for volatility/correlation
    today = datetime.now().date()
    one_year_ago = today - timedelta(days=365)

    historical_prices = {}
    for ticker in tickers:
        prices = price_service.get_historical_prices(ticker, one_year_ago.isoformat(), today.isoformat())
        historical_prices[ticker] = {p['date']: p['close_price'] for p in prices}

    # Precompute Volatility
    volatility_data = {}
    for ticker in tickers:
        prices_df = price_service._prices_to_dataframe(historical_prices[ticker])
        if not prices_df.empty:
            volatility = calculate_volatility(prices_df['close_price'])
            volatility_data[ticker] = volatility
            print(f"Volatility for {ticker}: {volatility:.4f}")
        else:
            print(f"Not enough data to calculate volatility for {ticker}")

    # Precompute Correlations
    correlation_data = {}
    if len(tickers) > 1:
        # Create a DataFrame of close prices for all tickers
        all_prices_df = pd.DataFrame()
        for ticker, prices in historical_prices.items():
            temp_df = pd.DataFrame(prices.items(), columns=['date', ticker])
            temp_df['date'] = pd.to_datetime(temp_df['date'])
            temp_df.set_index('date', inplace=True)
            if all_prices_df.empty:
                all_prices_df = temp_df
            else:
                all_prices_df = all_prices_df.join(temp_df, how='outer')
        
        all_prices_df.fillna(method='ffill', inplace=True) # Forward fill missing data
        all_prices_df.fillna(method='bfill', inplace=True) # Backward fill remaining missing data

        if not all_prices_df.empty:
            correlations_df = calculate_correlation(all_prices_df)
            correlation_data = correlations_df.to_dict()
            print("Correlations:\n", correlations_df)
        else:
            print("Not enough common data to calculate correlations.")
    else:
        print("Need at least two assets to calculate correlations.")

    # Save precomputed stats to Supabase (e.g., in a 'precomputed_stats' table)
    # This table would need to be created in Supabase
    stats_entry = {
        "date": today.isoformat(),
        "volatility": volatility_data,
        "correlations": correlation_data
    }

    response = supabase.table('precomputed_stats').insert(stats_entry).execute()
    if response.data:
        print("Saved precomputed stats to Supabase.")
    else:
        print(f"Failed to save precomputed stats to Supabase: {response.error}")

    print("Finished nightly job: Precomputing common stats.")

if __name__ == "__main__":
    precompute_common_stats()