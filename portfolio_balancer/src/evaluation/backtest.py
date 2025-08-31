import pandas as pd
import numpy as np
from datetime import timedelta
from portfolio_balancer.src.evaluation.metrics import calculate_daily_returns, calculate_portfolio_volatility, calculate_sharpe_ratio
from portfolio_balancer.src.optimization.rebalancer import deterministic_rebalance
from portfolio_balancer.src.optimization.cvxpy_rebalancer import cvxpy_rebalance
from portfolio_balancer.src.optimization.markowitz_mvo import markowitz_mvo

def run_backtest(
    price_history: pd.DataFrame,
    initial_portfolio: dict, # {'ticker': {'amount': float, 'price': float}}
    target_weights: dict, # {'ticker': weight}
    rebalance_frequency: str = 'quarterly', # 'quarterly', 'monthly', 'drift'
    drift_threshold: float = 0.05, # For drift-triggered rebalancing
    rebalance_engine: str = 'deterministic', # 'deterministic', 'cvxpy', 'mvo'
    mvo_params: dict = None, # Parameters for MVO if rebalance_engine is 'mvo'
    fees_per_trade: float = 0.0,
    min_trade_threshold: float = 0.01,
    risk_free_rate: float = 0.01
) -> dict:
    """
    Runs a rolling window backtest for a given rebalancing strategy.

    Args:
        price_history (pd.DataFrame): Historical closing prices for all assets.
                                      Index should be datetime, columns are tickers.
        initial_portfolio (dict): Starting portfolio with 'ticker': {'amount': float, 'price': float}.
        target_weights (dict): Desired target weights for each asset.
        rebalance_frequency (str): How often to rebalance ('quarterly', 'monthly', 'drift').
        drift_threshold (float): Percentage drift from target to trigger rebalance (for 'drift' frequency).
        rebalance_engine (str): Which rebalancing engine to use ('deterministic', 'cvxpy', 'mvo').
        mvo_params (dict): Dictionary of parameters for MVO (e.g., 'target_return', 'max_equities_weight').
        fees_per_trade (float): Fixed fee per trade.
        min_trade_threshold (float): Minimum dollar amount for a trade.
        risk_free_rate (float): Annualized risk-free rate for Sharpe Ratio calculation.

    Returns:
        dict: A dictionary containing backtest results, including:
            - 'portfolio_value_history': List of (date, value) tuples.
            - 'metrics': Dictionary of performance metrics (CAGR, Sharpe, Max Drawdown, Turnover).
            - 'trades_history': List of trades executed at each rebalance.
    """
    
    portfolio_value_history = []
    trades_history = []
    
    current_portfolio = initial_portfolio.copy()
    
    # Ensure price history is sorted by date
    price_history = price_history.sort_index()

    # Get unique dates for iteration
    dates = price_history.index.unique().tolist()
    
    # Initialize current portfolio value
    current_total_value = sum(item['amount'] * item['price'] for item in current_portfolio.values())
    portfolio_value_history.append((dates[0], current_total_value))

    last_rebalance_date = dates[0]

    for i in range(1, len(dates)):
        current_date = dates[i]
        
        # Update portfolio values with current prices
        for ticker, holding in current_portfolio.items():
            if ticker in price_history.columns and current_date in price_history.index:
                current_price = price_history.loc[current_date, ticker]
                holding['price'] = current_price
            elif ticker == 'CASH':
                # Cash value remains constant, but ensure it's in the portfolio dict
                if 'value' not in holding:
                    holding['value'] = holding['amount'] # Assuming amount for cash is its value
            else:
                # Handle missing price data for an asset
                print(f"Warning: Price for {ticker} not available on {current_date}. Using last known price.")
                # For simplicity, use last known price or skip.
                # A more robust solution might drop the asset or use a proxy.
                pass # Already using last known price if not updated

        # Calculate current total value
        current_total_value = 0
        for ticker, holding in current_portfolio.items():
            if ticker == 'CASH':
                current_total_value += holding.get('value', 0)
            else:
                current_total_value += holding.get('amount', 0) * holding.get('price', 0)
        
        # Check for rebalancing
        perform_rebalance = False
        if rebalance_frequency == 'quarterly':
            if (current_date.month - last_rebalance_date.month) % 3 == 0 and current_date.month != last_rebalance_date.month:
                perform_rebalance = True
        elif rebalance_frequency == 'monthly':
            if current_date.month != last_rebalance_date.month:
                perform_rebalance = True
        elif rebalance_frequency == 'drift':
            # Calculate current weights
            current_weights_actual = {}
            for ticker, holding in current_portfolio.items():
                if ticker == 'CASH':
                    current_weights_actual[ticker] = holding.get('value', 0) / current_total_value if current_total_value > 0 else 0
                else:
                    current_weights_actual[ticker] = (holding.get('amount', 0) * holding.get('price', 0)) / current_total_value if current_total_value > 0 else 0
            
            # Check drift for each asset
            for ticker, target_w in target_weights.items():
                actual_w = current_weights_actual.get(ticker, 0)
                if target_w > 0 and abs(actual_w - target_w) / target_w > drift_threshold:
                    perform_rebalance = True
                    break
                elif target_w == 0 and actual_w > drift_threshold: # If target is 0 but we hold significant amount
                    perform_rebalance = True
                    break

        if perform_rebalance:
            print(f"Rebalancing on {current_date} using {rebalance_engine} engine...")
            
            # Prepare current portfolio for rebalancer
            rebalancer_current_portfolio = {}
            asset_prices = {}
            for ticker, holding in current_portfolio.items():
                if ticker == 'CASH':
                    rebalancer_current_portfolio[ticker] = {'value': holding.get('value', 0)}
                else:
                    rebalancer_current_portfolio[ticker] = {'amount': holding.get('amount', 0), 'price': holding.get('price', 0)}
                    asset_prices[ticker] = holding.get('price', 0)

            rebalance_result = None
            if rebalance_engine == 'deterministic':
                rebalance_result = deterministic_rebalance(
                    current_portfolio=rebalancer_current_portfolio,
                    target_weights=target_weights,
                    total_value=current_total_value,
                    min_trade_threshold=min_trade_threshold,
                    fees_per_trade=fees_per_trade,
                    round_to_nearest_share=True, # Always round to nearest share in backtest for realism
                    asset_prices=asset_prices
                )
            elif rebalance_engine == 'cvxpy':
                rebalance_result = cvxpy_rebalance(
                    current_portfolio=rebalancer_current_portfolio,
                    target_weights=target_weights,
                    total_value=current_total_value,
                    asset_prices=asset_prices,
                    min_trade_threshold=min_trade_threshold,
                    fees_per_trade=fees_per_trade
                )
            elif rebalance_engine == 'mvo':
                # For MVO, we need to calculate optimal weights based on historical data up to current_date
                # This requires a look-back window for MVO calculation
                lookback_window_start = current_date - timedelta(days=365 * 5) # 5 years lookback
                mvo_price_history = price_history.loc[lookback_window_start:current_date].dropna(axis=1)
                
                if mvo_price_history.empty or mvo_price_history.shape[1] < 2:
                    print(f"Not enough data for MVO on {current_date}. Skipping MVO rebalance.")
                    rebalance_result = {"trades": [], "post_trade_weights_est": {}}
                else:
                    # Ensure mvo_params are passed correctly
                    mvo_result = markowitz_mvo(
                        price_history=mvo_price_history,
                        risk_free_rate=risk_free_rate,
                        target_return=mvo_params.get('target_return'),
                        max_equities_weight=mvo_params.get('max_equities_weight'),
                        max_bonds_weight=mvo_params.get('max_bonds_weight'),
                        max_cash_weight=mvo_params.get('max_cash_weight'),
                        asset_class_mapping=mvo_params.get('asset_class_mapping')
                    )
                    
                    if mvo_result['status'] in ["optimal", "optimal_near"]:
                        optimal_weights = mvo_result['optimal_weights']
                        # Convert optimal weights to target_weights format for rebalancer
                        mvo_target_weights = {k: v for k, v in optimal_weights.items() if v > 1e-6} # Filter tiny weights
                        
                        rebalance_result = deterministic_rebalance( # Use deterministic to execute MVO trades
                            current_portfolio=rebalancer_current_portfolio,
                            target_weights=mvo_target_weights,
                            total_value=current_total_value,
                            min_trade_threshold=min_trade_threshold,
                            fees_per_trade=fees_per_trade,
                            round_to_nearest_share=True,
                            asset_prices=asset_prices
                        )
                    else:
                        print(f"MVO failed on {current_date}. Status: {mvo_result['status']}. Skipping MVO rebalance.")
                        rebalance_result = {"trades": [], "post_trade_weights_est": {}}
            
            if rebalance_result:
                trades_history.extend(rebalance_result['trades'])
                
                # Apply trades to current_portfolio
                for trade in rebalance_result['trades']:
                    ticker = trade['ticker']
                    amount = trade['amount']
                    action = trade['action']
                    
                    if ticker == 'CASH':
                        if action == 'BUY':
                            current_portfolio['CASH']['value'] += amount
                        elif action == 'SELL':
                            current_portfolio['CASH']['value'] -= amount
                    else:
                        if action == 'BUY':
                            # Assuming amount is in dollars, convert to shares
                            shares_to_trade = amount / asset_prices[ticker] if asset_prices.get(ticker) else 0
                            current_portfolio[ticker]['amount'] = current_portfolio.get(ticker, {}).get('amount', 0) + shares_to_trade
                            current_portfolio['CASH']['value'] -= amount + fees_per_trade
                        elif action == 'SELL':
                            shares_to_trade = amount / asset_prices[ticker] if asset_prices.get(ticker) else 0
                            current_portfolio[ticker]['amount'] = current_portfolio.get(ticker, {}).get('amount', 0) - shares_to_trade
                            current_portfolio['CASH']['value'] += amount - fees_per_trade
                
                last_rebalance_date = current_date
        
        # Record portfolio value at end of day
        current_total_value = 0
        for ticker, holding in current_portfolio.items():
            if ticker == 'CASH':
                current_total_value += holding.get('value', 0)
            else:
                current_total_value += holding.get('amount', 0) * holding.get('price', 0)
        
        portfolio_value_history.append((current_date, current_total_value))

    # Calculate performance metrics
    portfolio_df = pd.DataFrame(portfolio_value_history, columns=['Date', 'Value']).set_index('Date')
    portfolio_returns = portfolio_df['Value'].pct_change().dropna()

    cagr = (portfolio_df['Value'].iloc[-1] / portfolio_df['Value'].iloc[0])**(252/len(portfolio_returns)) - 1 if len(portfolio_returns) > 0 else 0
    
    # Max Drawdown
    rolling_max = portfolio_df['Value'].expanding(min_periods=1).max()
    daily_drawdown = portfolio_df['Value'] / rolling_max - 1.0
    max_drawdown = daily_drawdown.min()

    # Sharpe Ratio
    # Need daily returns of the portfolio
    portfolio_daily_returns_series = portfolio_df['Value'].pct_change().dropna()
    sharpe = calculate_sharpe_ratio(portfolio_daily_returns_series, portfolio_daily_returns_series.std() * np.sqrt(252), risk_free_rate)

    # Turnover (simplified: sum of all trades / average portfolio value)
    total_trade_amount = sum(trade['amount'] for trade in trades_history)
    average_portfolio_value = portfolio_df['Value'].mean()
    turnover = total_trade_amount / average_portfolio_value if average_portfolio_value > 0 else 0

    metrics = {
        "CAGR": cagr,
        "Sharpe_Ratio": sharpe,
        "Max_Drawdown": max_drawdown,
        "Turnover": turnover
    }

    return {
        "portfolio_value_history": portfolio_value_history,
        "metrics": metrics,
        "trades_history": trades_history
    }

def compare_strategies(
    price_history: pd.DataFrame,
    initial_portfolio: dict,
    target_weights: dict,
    baseline_weights: dict, # e.g., {'SPY': 0.6, 'BND': 0.4} for 60/40
    rebalance_frequency: str = 'quarterly',
    drift_threshold: float = 0.05,
    fees_per_trade: float = 0.0,
    min_trade_threshold: float = 0.01,
    risk_free_rate: float = 0.01,
    mvo_params: dict = None
) -> dict:
    """
    Compares different rebalancing strategies against a baseline.

    Args:
        Same as run_backtest, plus:
        baseline_weights (dict): Target weights for the baseline portfolio (e.g., 60/40).

    Returns:
        dict: A dictionary with results for each strategy and the baseline.
    """
    results = {}

    # Run for deterministic engine
    print("Running backtest for Deterministic Rebalancing...")
    results['deterministic'] = run_backtest(
        price_history=price_history,
        initial_portfolio=initial_portfolio,
        target_weights=target_weights,
        rebalance_frequency=rebalance_frequency,
        drift_threshold=drift_threshold,
        rebalance_engine='deterministic',
        fees_per_trade=fees_per_trade,
        min_trade_threshold=min_trade_threshold,
        risk_free_rate=risk_free_rate
    )

    # Run for cvxpy engine
    print("Running backtest for Cvxpy Rebalancing...")
    results['cvxpy'] = run_backtest(
        price_history=price_history,
        initial_portfolio=initial_portfolio,
        target_weights=target_weights,
        rebalance_frequency=rebalance_frequency,
        drift_threshold=drift_threshold,
        rebalance_engine='cvxpy',
        fees_per_trade=fees_per_trade,
        min_trade_threshold=min_trade_threshold,
        risk_free_rate=risk_free_rate
    )

    # Run for MVO engine
    print("Running backtest for MVO Rebalancing...")
    results['mvo'] = run_backtest(
        price_history=price_history,
        initial_portfolio=initial_portfolio,
        target_weights=target_weights, # MVO will calculate its own optimal weights
        rebalance_frequency=rebalance_frequency,
        drift_threshold=drift_threshold,
        rebalance_engine='mvo',
        mvo_params=mvo_params,
        fees_per_trade=fees_per_trade,
        min_trade_threshold=min_trade_threshold,
        risk_free_rate=risk_free_rate
    )

    # Run for baseline (static allocation, rebalanced quarterly)
    print("Running backtest for Baseline (Static Allocation)...")
    # Adjust initial portfolio for baseline to match its assets
    baseline_initial_portfolio = {}
    for ticker, weight in baseline_weights.items():
        # Need to get initial price for baseline assets
        initial_price = price_history.loc[price_history.index[0], ticker] if ticker in price_history.columns else 1 # Default to 1 for cash or missing
        # Distribute initial total value based on baseline weights
        initial_value_for_asset = (sum(item['amount'] * item['price'] for item in initial_portfolio.values()) * weight)
        baseline_initial_portfolio[ticker] = {'amount': initial_value_for_asset / initial_price, 'price': initial_price}
    
    # Add cash to baseline initial portfolio if not present
    if 'CASH' not in baseline_initial_portfolio and 'CASH' in baseline_weights:
        initial_cash_value = (sum(item['amount'] * item['price'] for item in initial_portfolio.values()) * baseline_weights['CASH'])
        baseline_initial_portfolio['CASH'] = {'value': initial_cash_value}

    results['baseline'] = run_backtest(
        price_history=price_history,
        initial_portfolio=baseline_initial_portfolio,
        target_weights=baseline_weights, # Baseline uses its own fixed target weights
        rebalance_frequency='quarterly', # Baseline is typically rebalanced periodically
        rebalance_engine='deterministic', # Use deterministic rebalancer for baseline
        fees_per_trade=fees_per_trade,
        min_trade_threshold=min_trade_threshold,
        risk_free_rate=risk_free_rate
    )

    return results

def generate_backtest_report(backtest_results: dict) -> dict:
    """
    Generates a summary report from backtest results.

    Args:
        backtest_results (dict): Output from compare_strategies.

    Returns:
        dict: A dictionary containing summary metrics and plot data.
    """
    summary_metrics = {}
    portfolio_value_plots = {}

    for strategy, result in backtest_results.items():
        summary_metrics[strategy] = result['metrics']
        portfolio_value_plots[strategy] = result['portfolio_value_history']
    
    return {
        "summary_metrics": summary_metrics,
        "portfolio_value_plots": portfolio_value_plots
    }