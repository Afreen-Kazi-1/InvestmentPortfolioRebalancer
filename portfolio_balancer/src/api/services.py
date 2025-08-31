from portfolio_balancer.src.api.models import Holding, TargetAllocation
from portfolio_balancer.src.api.price_service import price_service
from supabase import create_client, Client
import os
import pandas as pd

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_portfolio_snapshot(user_id):
    # Fetch holdings from Supabase
    holdings_data = supabase.table('holding').select("*").eq("user_id", user_id).execute().data
    holdings = [Holding(id=h['id'], user_id=h['user_id'], ticker=h['ticker'], quantity=h['quantity'], avg_cost=h['avg_cost']) for h in holdings_data]

    # Fetch target allocation from Supabase
    target_allocation_data = supabase.table('target_allocation').select("*").eq("user_id", user_id).limit(1).execute().data
    target_allocation = TargetAllocation(id=t['id'], user_id=t['user_id'], equities=t['equities'], bonds=t['bonds'], cash=t['cash']) if target_allocation_data else None

    if not holdings:
        return {"total_value": 0, "breakdown": []}

    breakdown = []
    total_value = 0

    for holding in holdings:
        latest_price_obj = price_service.get_latest_price(holding.ticker)
        if latest_price_obj is None:
            print(f"Warning: Could not retrieve latest price for {holding.ticker}. Skipping this holding.")
            continue
        
        latest_price = latest_price_obj # Assuming get_latest_price now returns the price directly
        value = holding.quantity * latest_price
        total_value += value
        breakdown.append({
            "ticker": holding.ticker,
            "value": value,
            "quantity": holding.quantity,
            "latest_price": latest_price
        })

    # Compute weights and drift
    for item in breakdown:
        item["weight"] = item["value"] / total_value if total_value else 0
        
        # Determine target weight based on ticker type (simplified for now)
        # This part needs to be more robust, potentially mapping tickers to asset classes
        target_weight = 0
        if target_allocation:
            if item["ticker"] == "AAPL": # Example: map AAPL to equities
                target_weight = target_allocation.equities
            elif item["ticker"] == "BND": # Example: map BND to bonds
                target_weight = target_allocation.bonds
            elif item["ticker"] == "CASH": # Example: map CASH to cash
                target_weight = target_allocation.cash
            # For other tickers, a more sophisticated mapping would be needed
            # For now, if no specific target, assume 0 or handle as needed
        
        item["target"] = target_weight
        item["drift"] = item["weight"] - target_weight
        
        # Remove quantity and latest_price from final output
        # Ensure these keys exist before attempting to delete
        if "quantity" in item:
            del item["quantity"]
        if "latest_price" in item:
            del item["latest_price"]

    return {
        "total_value": round(total_value, 2),
        "breakdown": breakdown
    }

def get_asset_class_mapping(tickers: list) -> dict:
    """
    Provides a simplified mapping of tickers to asset classes.
    In a real application, this would be fetched from a database or a more robust service.
    """
    mapping = {}
    for ticker in tickers:
        if ticker in ["AAPL", "GOOGL", "MSFT"]: # Example equities
            mapping[ticker] = "equities"
        elif ticker in ["BND", "AGG"]: # Example bonds
            mapping[ticker] = "bonds"
        elif ticker == "CASH":
            mapping[ticker] = "cash"
        elif ticker in ["BTC-USD", "ETH-USD"]: # Example crypto
            mapping[ticker] = "crypto" # Add crypto as a new asset class
        else:
            mapping[ticker] = "other" # Default or unknown
    return mapping

from datetime import datetime, timedelta

def get_historical_portfolio_by_asset_class(user_id: int, days: int = 365) -> list:
    """
    Retrieves historical portfolio value broken down by asset class for a given user.

    Args:
        user_id (int): The ID of the user.
        days (int): The number of days back from today to fetch historical data.

    Returns:
        list: A list of dictionaries, each containing 'date' and asset class values.
              Example: [{'date': '2023-01-01', 'equities': 1000, 'bonds': 500, 'cash': 200}, ...]
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Fetch all holdings for the user
    holdings_data = supabase.table('holding').select("*").eq("user_id", user_id).execute().data
    
    if not holdings_data:
        return []

    # Get all unique tickers from holdings
    all_tickers = list(set([h['ticker'] for h in holdings_data]))
    asset_class_mapping = get_asset_class_mapping(all_tickers)

    historical_data = []
    current_date = start_date
    while current_date <= end_date:
        daily_asset_values = {
            'date': current_date.isoformat(),
            'equities': 0.0,
            'bonds': 0.0,
            'cash': 0.0,
            'crypto': 0.0,
            'other': 0.0
        }
        
        for holding in holdings_data:
            ticker = holding['ticker']
            quantity = holding['quantity']
            asset_class = asset_class_mapping.get(ticker, 'other')

            # Fetch historical price for the specific date
            # This is a simplified approach. In a real system, you'd query your
            # price_history table for the exact date or the closest available date.
            # For now, we'll use price_service.get_historical_prices for a single day.
            # This might be inefficient for many dates/tickers and should be optimized.
            
            # Fetch historical prices for a small range around the current_date
            # to find the closest available price.
            price_history_response = supabase.table('price_history') \
                .select("close") \
                .eq("ticker", ticker) \
                .lte("date", current_date.isoformat()) \
                .order("date", desc=True) \
                .limit(1) \
                .execute()
            
            price_on_date = None
            if price_history_response.data:
                price_on_date = price_history_response.data[0]['close']
            
            if price_on_date is not None:
                value = quantity * price_on_date
                daily_asset_values[asset_class] += value
            else:
                # If no price found for the date, try to get the latest price
                # This is a fallback and might not be accurate for historical context
                latest_price_obj = price_service.get_latest_price(ticker)
                if latest_price_obj is not None:
                    value = quantity * latest_price_obj
                    daily_asset_values[asset_class] += value
                else:
                    print(f"Warning: No price found for {ticker} on {current_date.isoformat()} or latest.")

        historical_data.append(daily_asset_values)
        current_date += timedelta(days=1)
    
    return historical_data
