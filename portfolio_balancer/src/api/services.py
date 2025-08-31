from portfolio_balancer.src.data.database import db
from portfolio_balancer.src.data.models import Holding, TargetAllocation, LatestPrice
from portfolio_balancer.src.api.price_service import price_service

def get_portfolio_snapshot(user_id):
    holdings = Holding.query.filter_by(user_id=user_id).all()
    target_allocation = TargetAllocation.query.filter_by(user_id=user_id).first()

    if not holdings:
        return {"total_value": 0, "breakdown": []}

    breakdown = []
    total_value = 0

    for holding in holdings:
        latest_price = price_service.get_latest_price(holding.ticker)
        if latest_price is None:
            # Handle cases where price cannot be retrieved, maybe skip or use a default
            continue
        
        value = holding.quantity * latest_price
        total_value += value
        breakdown.append({
            "ticker": holding.ticker,
            "value": value,
            "quantity": holding.quantity,
            "latest_price": latest_price
        })

    # Compute weights and drift
    # Define a simple mapping for asset classes for MVP
    # In a real application, this would be more dynamic (e.g., from a database or configuration)
    ASSET_CLASS_MAPPING = {
        "AAPL": "equities",
        "GOOGL": "equities",
        "MSFT": "equities",
        "VOO": "equities", # Example ETF
        "BND": "bonds",    # Example Bond ETF
        "AGG": "bonds",    # Example Bond ETF
        "BTC-USD": "crypto", # Crypto can be treated as a separate asset class or mapped to equities
        "ETH-USD": "crypto",
        "CASH": "cash"
    }

    for item in breakdown:
        item["weight"] = round(item["value"] / total_value, 3) if total_value else 0
        
        target_weight = 0
        if target_allocation:
            asset_class = ASSET_CLASS_MAPPING.get(item["ticker"], None)
            if asset_class == "equities":
                target_weight = target_allocation.equities
            elif asset_class == "bonds":
                target_weight = target_allocation.bonds
            elif asset_class == "cash":
                target_weight = target_allocation.cash
            # For crypto, if not explicitly in target_allocation, it will have 0 target weight
            # A more advanced system would allow users to set target for crypto specifically

        item["target"] = round(target_weight, 3)
        item["drift"] = round(item["weight"] - target_weight, 3)
        
        # Remove quantity and latest_price from final output
        del item["quantity"]
        del item["latest_price"]

    return {
        "total_value": round(total_value, 2),
        "breakdown": breakdown
    }

def suggest_rebalance(user_id):
    snapshot = get_portfolio_snapshot(user_id)
    total_value = snapshot["total_value"]
    breakdown = snapshot["breakdown"]

    target_allocation = TargetAllocation.query.filter_by(user_id=user_id).first()

    trades = []
    post_trade_weights_est = {}

    if not target_allocation:
        return {"trades": [], "post_trade_weights_est": {}}

    # Calculate target dollar amounts for each asset class
    target_dollars = {
        "equities": total_value * target_allocation.equities,
        "bonds": total_value * target_allocation.bonds,
        "cash": total_value * target_allocation.cash
    }

    # Initialize current values per asset class
    current_dollars = {
        "equities": 0,
        "bonds": 0,
        "cash": 0
    }

    # Map current holdings to asset classes and sum their values
    ASSET_CLASS_MAPPING = {
        "AAPL": "equities",
        "GOOGL": "equities",
        "MSFT": "equities",
        "VOO": "equities",
        "BND": "bonds",
        "AGG": "bonds",
        "BTC-USD": "crypto",
        "ETH-USD": "crypto",
        "CASH": "cash"
    }

    for item in breakdown:
        asset_class = ASSET_CLASS_MAPPING.get(item["ticker"])
        if asset_class in current_dollars:
            current_dollars[asset_class] += item["value"]
        # Handle crypto or other unmapped assets - for now, they don't contribute to target rebalancing

    # Calculate deltas and generate trades
    # This is a simplified rebalancing logic. A real one would consider individual tickers.
    # For MVP, we'll rebalance at the asset class level.
    
    # Prioritize selling over buying to free up cash if needed
    # Sell assets that are over-allocated
    for asset_class, current_val in current_dollars.items():
        target_val = target_dollars.get(asset_class, 0)
        delta = current_val - target_val # Positive if over-allocated, negative if under-allocated

        if delta > 0.01 * total_value: # Threshold for significant trade (e.g., 1% of total portfolio value)
            # Find a ticker within this asset class to sell
            # This is a very simplistic approach. In reality, you'd pick specific holdings.
            for item in breakdown:
                if ASSET_CLASS_MAPPING.get(item["ticker"]) == asset_class and item["value"] > 0:
                    sell_amount = min(delta, item["value"])
                    trades.append({"action": "SELL", "ticker": item["ticker"], "amount": round(sell_amount, 2)})
                    delta -= sell_amount
                    if delta <= 0:
                        break
    
    # Buy assets that are under-allocated
    for asset_class, current_val in current_dollars.items():
        target_val = target_dollars.get(asset_class, 0)
        delta = target_val - current_val # Positive if under-allocated, negative if over-allocated

        if delta > 0.01 * total_value: # Threshold for significant trade
            # Find a ticker within this asset class to buy
            # Again, very simplistic. You'd need to decide which specific ticker to buy.
            for item in breakdown: # Re-iterate to find a suitable ticker to buy
                if ASSET_CLASS_MAPPING.get(item["ticker"]) == asset_class:
                    buy_amount = delta
                    trades.append({"action": "BUY", "ticker": item["ticker"], "amount": round(buy_amount, 2)})
                    break # Only buy one ticker per asset class for simplicity

    # Estimate post-trade weights (very rough estimation for MVP)
    # This would require a more detailed calculation based on actual trades
    if target_allocation:
        post_trade_weights_est["equities"] = target_allocation.equities
        post_trade_weights_est["bonds"] = target_allocation.bonds
        post_trade_weights_est["cash"] = target_allocation.cash
        # For other assets like crypto, their weight might remain as current or be adjusted manually

    return {
        "trades": trades,
        "post_trade_weights_est": post_trade_weights_est
    }