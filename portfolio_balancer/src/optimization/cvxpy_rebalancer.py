import cvxpy as cp
import numpy as np
import pandas as pd

def cvxpy_rebalance(
    current_portfolio: dict,
    target_weights: dict,
    total_value: float,
    asset_prices: dict,
    min_trade_threshold: float = 0.01,
    min_cash_reserve: float = 0.0,
    fees_per_trade: float = 0.0,
    epsilon: float = 0.01 # Tolerance for deviation from target weights
) -> dict:
    """
    Calculates trades needed to rebalance a portfolio to target weights using cvxpy optimization.
    Minimizes transaction costs while staying close to target weights and respecting constraints.

    Args:
        current_portfolio (dict): Current portfolio with 'ticker': {'amount': float, 'price': float}
                                  or 'ticker': {'value': float} for cash.
                                  Example: {'AAPL': {'amount': 10, 'price': 150}, 'CASH': {'value': 500}}
        target_weights (dict): Desired target weights for each asset, including CASH.
                               Example: {'AAPL': 0.2, 'BND': 0.3, 'CASH': 0.5}
        total_value (float): Total current value of the portfolio (sum of all assets + cash).
        asset_prices (dict): Dictionary of current asset prices {'ticker': price}.
        min_trade_threshold (float): Minimum dollar amount for a trade to be executed.
        min_cash_reserve (float): Minimum cash amount to maintain in the portfolio.
        fees_per_trade (float): Fixed fee per trade (buy or sell).
        epsilon (float): Maximum allowed deviation from target weights (L2 norm).

    Returns:
        dict: A dictionary containing:
            - "trades": List of trade dictionaries (action, ticker, amount).
            - "post_trade_weights_est": Estimated post-trade weights.
    """
    
    # Prepare data
    tickers = sorted(list(set(current_portfolio.keys()) | set(target_weights.keys())))
    
    current_values = np.array([current_portfolio.get(t, {}).get('value', current_portfolio.get(t, {}).get('amount', 0) * current_portfolio.get(t, {}).get('price', 0)) for t in tickers])
    current_weights = current_values / total_value if total_value > 0 else np.zeros_like(current_values)
    
    target_w = np.array([target_weights.get(t, 0) for t in tickers])
    
    prices = np.array([asset_prices.get(t, 1) for t in tickers]) # Use 1 for cash or if price not available

    # Define optimization variables
    # w_new: new portfolio weights
    # x_buy: dollar amount to buy for each asset
    # x_sell: dollar amount to sell for each asset
    w_new = cp.Variable(len(tickers), name="w_new")
    x_buy = cp.Variable(len(tickers), name="x_buy")
    x_sell = cp.Variable(len(tickers), name="x_sell")

    # Objective: Minimize transaction costs (sum of buys and sells)
    # We also want to stay close to target weights.
    # A common approach is to minimize the L1 norm of trades, or a combination.
    # Let's minimize the sum of absolute trades (buys + sells)
    # and also penalize deviation from target weights.
    
    # Penalize deviation from target weights (L2 norm)
    objective = cp.Minimize(cp.sum(x_buy) + cp.sum(x_sell) + cp.sum_squares(w_new - target_w))

    # Constraints
    constraints = []

    # 1. New weights must sum to 1
    constraints.append(cp.sum(w_new) == 1)

    # 2. Non-negativity of new weights and trades
    constraints.append(w_new >= 0)
    constraints.append(x_buy >= 0)
    constraints.append(x_sell >= 0)

    # 3. Relationship between current value, trades, and new value
    # current_value_i + x_buy_i - x_sell_i = new_value_i
    # new_value_i / total_value = w_new_i
    # So, (current_value_i + x_buy_i - x_sell_i) / total_value = w_new_i
    # Assuming total_value remains constant for simplicity in this equation,
    # or we can make total_value a variable if we want to optimize for it.
    # For rebalancing, total_value is usually given.
    
    # If total_value is fixed, then new_value_i = w_new_i * total_value
    # current_values[i] + x_buy[i] - x_sell[i] == w_new[i] * total_value
    constraints.append(current_values + x_buy - x_sell == w_new * total_value)

    # 4. Cannot simultaneously buy and sell the same asset
    # This is implicitly handled by x_buy and x_sell being non-negative and separate variables.
    # However, for numerical stability or to enforce strictness, one might add:
    # x_buy[i] * x_sell[i] == 0 (non-convex) or using indicator variables (more complex).
    # For simplicity, we rely on the solver to find a solution where this is true.

    # 5. Cash constraint
    # Calculate cash after trades
    # Initial cash: current_portfolio.get('CASH', {}).get('value', 0)
    # Cash from sells: sum(x_sell)
    # Cash used for buys: sum(x_buy)
    # Fees: sum(indicator_buy) * fees_per_trade + sum(indicator_sell) * fees_per_trade
    
    # For simplicity, let's assume fees are deducted from cash.
    # This requires knowing which trades actually happen.
    # A common way to handle fixed fees in convex optimization is to use a penalty
    # or to approximate them. For now, let's simplify the cash constraint.
    
    # Total cash available for buys (from initial cash + sells)
    total_cash_available = current_portfolio.get('CASH', {}).get('value', 0) + cp.sum(x_sell)
    
    # Total cash needed for buys + fees
    total_cash_needed = cp.sum(x_buy) + fees_per_trade * (cp.sum(cp.ceil(x_buy / min_trade_threshold)) + cp.sum(cp.ceil(x_sell / min_trade_threshold))) # Approximation for number of trades
    
    # Ensure cash after trades meets minimum reserve
    # This is tricky because cash is also an asset.
    # Let's treat CASH as a regular asset in `tickers` and `w_new`.
    # The `min_cash_reserve` can be enforced by setting a minimum target weight for CASH
    # or by adding a specific constraint for the cash variable.
    
    # If 'CASH' is one of the tickers:
    cash_idx = -1
    if 'CASH' in tickers:
        cash_idx = tickers.index('CASH')
        # Ensure cash weight is at least min_cash_reserve / total_value
        constraints.append(w_new[cash_idx] * total_value >= min_cash_reserve)
        
        # Ensure total cash available covers non-cash buys and fees
        # This is a more robust way to handle cash.
        # Sum of all non-cash buys + fees <= current cash + sum of non-cash sells
        non_cash_buy_sum = cp.sum([x_buy[i] for i in range(len(tickers)) if i != cash_idx])
        non_cash_sell_sum = cp.sum([x_sell[i] for i in range(len(tickers)) if i != cash_idx])
        
        # Approximate number of trades for fees
        num_buys = cp.sum([cp.ceil(x_buy[i] / min_trade_threshold) for i in range(len(tickers)) if i != cash_idx])
        num_sells = cp.sum([cp.ceil(x_sell[i] / min_trade_threshold) for i in range(len(tickers)) if i != cash_idx])
        
        total_fees = fees_per_trade * (num_buys + num_sells)
        
        constraints.append(non_cash_buy_sum + total_fees <= current_values[cash_idx] + non_cash_sell_sum)
    
    # 6. Ignore tiny trades (using big-M formulation or similar for binary variables)
    # This is complex in pure convex optimization without mixed-integer programming.
    # For a purely convex problem, we can't strictly enforce "ignore tiny trades"
    # without introducing binary variables (which makes it mixed-integer convex program).
    # A common approximation is to penalize small trades in the objective.
    # Or, we can apply the threshold *after* solving the optimization.
    
    # Let's apply the threshold after solving for simplicity, as the prompt implies
    # a purely convex optimization.
    
    # Problem definition
    problem = cp.Problem(objective, constraints)

    # Solve the problem
    try:
        problem.solve()
    except Exception as e:
        print(f"Error solving cvxpy problem: {e}")
        return {
            "trades": [],
            "post_trade_weights_est": {},
            "error": str(e)
        }

    if problem.status not in ["optimal", "optimal_near"]:
        print(f"Problem status: {problem.status}")
        return {
            "trades": [],
            "post_trade_weights_est": {},
            "error": f"Optimization problem could not be solved to optimality. Status: {problem.status}"
        }

    # Extract results
    new_weights = w_new.value
    buy_amounts = x_buy.value
    sell_amounts = x_sell.value

    trades = []
    post_trade_values = {}

    for i, ticker in enumerate(tickers):
        current_val = current_values[i]
        
        # Apply min_trade_threshold
        buy_val = buy_amounts[i] if buy_amounts[i] >= min_trade_threshold else 0
        sell_val = sell_amounts[i] if sell_amounts[i] >= min_trade_threshold else 0

        # Ensure we don't buy and sell the same asset (due to thresholding)
        if buy_val > 0 and sell_val > 0:
            if buy_val > sell_val:
                buy_val -= sell_val
                sell_val = 0
            else:
                sell_val -= buy_val
                buy_val = 0

        if buy_val > 0:
            trades.append({"action": "BUY", "ticker": ticker, "amount": buy_val})
            current_val += buy_val
        if sell_val > 0:
            trades.append({"action": "SELL", "ticker": ticker, "amount": sell_val})
            current_val -= sell_val
        
        post_trade_values[ticker] = current_val

    # Adjust for fees (simplified: deduct from cash after all trades)
    total_fees_incurred = len(trades) * fees_per_trade
    if 'CASH' in post_trade_values:
        post_trade_values['CASH'] -= total_fees_incurred
        if post_trade_values['CASH'] < min_cash_reserve:
            print(f"Warning: Cash reserve fell below minimum after fees. Current cash: {post_trade_values['CASH']}")

    # Estimate post-trade weights
    final_total_value = sum(post_trade_values.values())
    post_trade_weights_est = {ticker: value / final_total_value
                              for ticker, value in post_trade_values.items() if final_total_value > 0}

    return {
        "trades": trades,
        "post_trade_weights_est": post_trade_weights_est
    }