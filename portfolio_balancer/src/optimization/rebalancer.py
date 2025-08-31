import pandas as pd
import numpy as np

def deterministic_rebalance(
    current_portfolio: dict,
    target_weights: dict,
    total_value: float,
    min_trade_threshold: float = 0.01, # e.g., $10
    min_cash_reserve: float = 0.0,
    fees_per_trade: float = 0.0,
    round_to_nearest_share: bool = False,
    asset_prices: dict = None # Required if round_to_nearest_share is True
) -> dict:
    """
    Calculates trades needed to rebalance a portfolio to target weights with minimal trades.

    Args:
        current_portfolio (dict): Current portfolio with 'ticker': {'amount': float, 'price': float}
                                  or 'ticker': {'value': float} for cash.
                                  Example: {'AAPL': {'amount': 10, 'price': 150}, 'CASH': {'value': 500}}
        target_weights (dict): Desired target weights for each asset, including CASH.
                               Example: {'AAPL': 0.2, 'BND': 0.3, 'CASH': 0.5}
        total_value (float): Total current value of the portfolio (sum of all assets + cash).
        min_trade_threshold (float): Minimum dollar amount for a trade to be executed.
        min_cash_reserve (float): Minimum cash amount to maintain in the portfolio.
        fees_per_trade (float): Fixed fee per trade (buy or sell).
        round_to_nearest_share (bool): If True, trade amounts will be rounded to nearest whole share.
        asset_prices (dict): Dictionary of current asset prices {'ticker': price}.
                             Required if round_to_nearest_share is True.

    Returns:
        dict: A dictionary containing:
            - "trades": List of trade dictionaries (action, ticker, amount).
            - "post_trade_weights_est": Estimated post-trade weights.
    """
    trades = []
    post_trade_values = {ticker: data.get('value', data['amount'] * data['price'])
                         for ticker, data in current_portfolio.items()}
    
    # Calculate target dollar per asset
    target_dollars = {ticker: weight * total_value for ticker, weight in target_weights.items()}

    # Calculate delta dollars
    delta_dollars = {ticker: target_dollars.get(ticker, 0) - post_trade_values.get(ticker, 0)
                     for ticker in set(target_dollars.keys()) | set(post_trade_values.keys())}

    # Adjust for minimum cash reserve
    cash_delta = delta_dollars.get('CASH', 0)
    current_cash = post_trade_values.get('CASH', 0)

    # If cash is below reserve and we need to sell, prioritize selling to meet reserve
    if current_cash + cash_delta < min_cash_reserve:
        needed_cash = min_cash_reserve - (current_cash + cash_delta)
        # Try to generate cash by selling other assets if possible
        # This is a simplification; a more complex rebalancer would iterate
        # and prioritize selling overweighted assets.
        # For now, we'll just ensure cash doesn't go below reserve.
        if cash_delta < 0: # If we were planning to reduce cash
            delta_dollars['CASH'] = max(delta_dollars.get('CASH', 0), min_cash_reserve - current_cash)
            
    # Separate buys and sells
    buys = {ticker: amount for ticker, amount in delta_dollars.items() if amount > 0}
    sells = {ticker: abs(amount) for ticker, amount in delta_dollars.items() if amount < 0}

    # Process sells first to generate cash for buys
    for ticker, amount in sorted(sells.items(), key=lambda item: item[1], reverse=True):
        if amount >= min_trade_threshold:
            trade_amount = amount
            if round_to_nearest_share and ticker != 'CASH':
                if ticker not in asset_prices or asset_prices[ticker] == 0:
                    print(f"Warning: Price for {ticker} not found, cannot round to nearest share for sell. Selling exact amount.")
                else:
                    num_shares = trade_amount / asset_prices[ticker]
                    trade_amount = round(num_shares) * asset_prices[ticker]
                    if trade_amount == 0 and num_shares > 0: # Ensure we don't round down to 0 if there's something to sell
                        trade_amount = asset_prices[ticker] # Sell at least one share
            
            if trade_amount > 0:
                trades.append({"action": "SELL", "ticker": ticker, "amount": trade_amount})
                post_trade_values[ticker] -= trade_amount
                post_trade_values['CASH'] = post_trade_values.get('CASH', 0) + trade_amount - fees_per_trade

    # Process buys
    for ticker, amount in sorted(buys.items(), key=lambda item: item[1]):
        if ticker == 'CASH':
            # Cash target is handled by ensuring min_cash_reserve and using remaining cash for buys
            continue

        if amount >= min_trade_threshold:
            trade_amount = amount
            if round_to_nearest_share:
                if ticker not in asset_prices or asset_prices[ticker] == 0:
                    print(f"Warning: Price for {ticker} not found, cannot round to nearest share for buy. Buying exact amount.")
                else:
                    num_shares = trade_amount / asset_prices[ticker]
                    trade_amount = round(num_shares) * asset_prices[ticker]
                    if trade_amount == 0 and num_shares > 0: # Ensure we buy at least one share if needed
                        trade_amount = asset_prices[ticker]
            
            # Ensure we have enough cash for the trade + fees
            required_cash = trade_amount + fees_per_trade
            if post_trade_values.get('CASH', 0) >= required_cash:
                trades.append({"action": "BUY", "ticker": ticker, "amount": trade_amount})
                post_trade_values[ticker] = post_trade_values.get(ticker, 0) + trade_amount
                post_trade_values['CASH'] -= required_cash
            else:
                print(f"Not enough cash to buy {ticker}. Needed: {required_cash}, Available: {post_trade_values.get('CASH', 0)}")

    # Final check for cash reserve after all trades
    if post_trade_values.get('CASH', 0) < min_cash_reserve:
        print(f"Warning: Cash reserve fell below minimum after trades. Current cash: {post_trade_values.get('CASH', 0)}")

    # Estimate post-trade weights
    final_total_value = sum(post_trade_values.values())
    post_trade_weights_est = {ticker: value / final_total_value
                              for ticker, value in post_trade_values.items() if final_total_value > 0}

    return {
        "trades": trades,
        "post_trade_weights_est": post_trade_weights_est
    }