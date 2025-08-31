from datetime import datetime, timedelta
from portfolio_balancer.src.api.price_service import PriceService
from portfolio_balancer.src.api.models import Snapshot, Portfolio, User
from portfolio_balancer.src.api.services import calculate_portfolio_value, calculate_asset_allocation
from supabase import create_client, Client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

price_service = PriceService()

def refresh_historical_and_latest_prices():
    """
    Daily job to refresh historical and latest prices for all unique tickers
    across all portfolios.
    """
    print("Starting daily job: Refreshing historical and latest prices...")

    # Fetch all portfolios to get unique tickers
    response = supabase.table('portfolios').select("assets").execute()
    all_assets = []
    if response.data:
        for portfolio_data in response.data:
            if portfolio_data and 'assets' in portfolio_data:
                all_assets.extend(portfolio_data['assets'])
    
    unique_tickers = set()
    for asset in all_assets:
        if 'ticker' in asset:
            unique_tickers.add(asset['ticker'])

    today = datetime.now().date()
    # For historical data, fetch for the last 7 days to ensure we catch any missed updates
    # and to have enough data for potential calculations.
    start_date = today - timedelta(days=7) 

    for ticker in unique_tickers:
        print(f"Refreshing data for ticker: {ticker}")
        # Fetch historical prices (this will use cache or fetch from provider)
        price_service.get_historical_prices(ticker, start_date.isoformat(), today.isoformat())
        # Fetch latest price (this will use cache or fetch from provider)
        price_service.get_latest_price(ticker)
    
    print("Finished daily job: Refreshing historical and latest prices.")

def recompute_snapshots():
    """
    Daily job to recompute portfolio snapshots for all users.
    """
    print("Starting daily job: Recomputing snapshots...")

    response = supabase.table('users').select("id").execute()
    user_ids = [user['id'] for user in response.data] if response.data else []

    for user_id in user_ids:
        print(f"Recomputing snapshots for user: {user_id}")
        # Fetch user's portfolios
        response = supabase.table('portfolios').select("*").eq("user_id", user_id).execute()
        user_portfolios = response.data if response.data else []

        for portfolio_data in user_portfolios:
            portfolio = Portfolio(**portfolio_data)
            
            # Calculate current value and allocation
            current_value = calculate_portfolio_value(portfolio)
            current_allocation = calculate_asset_allocation(portfolio)

            # Create new snapshot entry
            snapshot_entry = {
                "user_id": user_id,
                "portfolio_id": portfolio.id,
                "date": datetime.now().date().isoformat(),
                "total_value": current_value,
                "asset_allocation": current_allocation # Store as JSONB in Supabase
            }

            # Insert into Supabase
            response = supabase.table('snapshots').insert(snapshot_entry).execute()
            if response.data:
                print(f"Saved snapshot for portfolio {portfolio.id} of user {user_id}.")
            else:
                print(f"Failed to save snapshot for portfolio {portfolio.id} of user {user_id}: {response.error}")
    
    print("Finished daily job: Recomputing snapshots.")

if __name__ == "__main__":
    refresh_historical_and_latest_prices()
    recompute_snapshots()