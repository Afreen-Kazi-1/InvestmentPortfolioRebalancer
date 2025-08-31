from portfolio_balancer.src.api.app import db, Holding, TargetAllocation
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
        del item["quantity"]
        del item["latest_price"]

    return {
        "total_value": round(total_value, 2),
        "breakdown": breakdown
    }