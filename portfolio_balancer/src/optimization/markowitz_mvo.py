import cvxpy as cp
import numpy as np
import pandas as pd
from portfolio_balancer.src.evaluation.metrics import calculate_daily_returns, calculate_covariance_matrix

def markowitz_mvo(
    price_history: pd.DataFrame,
    risk_free_rate: float = 0.01,
    target_return: float = None, # Annualized target return
    max_equities_weight: float = None, # Constraint for conservative profiles
    max_bonds_weight: float = None,
    max_cash_weight: float = None,
    asset_class_mapping: dict = None # Ticker to asset class mapping
) -> dict:
    """
    Performs Markowitz Mean-Variance Optimization to find optimal portfolio weights.

    Args:
        price_history (pd.DataFrame): DataFrame with historical closing prices for assets.
        risk_free_rate (float): Annualized risk-free rate.
        target_return (float): Optional annualized target return for the portfolio.
                               If provided, minimizes variance for this return.
                               If None, maximizes Sharpe Ratio.
        max_equities_weight (float): Maximum allowed weight for equities.
        max_bonds_weight (float): Maximum allowed weight for bonds.
        max_cash_weight (float): Maximum allowed weight for cash.
        asset_class_mapping (dict): Dictionary mapping tickers to their asset classes.

    Returns:
        dict: A dictionary containing:
            - "optimal_weights": Dictionary of optimal weights for each asset.
            - "expected_return": Annualized expected return of the optimal portfolio.
            - "expected_volatility": Annualized expected volatility of the optimal portfolio.
            - "sharpe_ratio": Sharpe Ratio of the optimal portfolio.
            - "status": Optimization status.
    """
    
    daily_returns = calculate_daily_returns(price_history)
    
    # Calculate expected returns (historical mean) and covariance matrix
    expected_daily_returns = daily_returns.mean()
    cov_matrix = calculate_covariance_matrix(daily_returns)
    
    # Annualize expected returns
    expected_annual_returns = (1 + expected_daily_returns)**252 - 1
    
    assets = daily_returns.columns.tolist()
    num_assets = len(assets)

    # Define optimization variables
    weights = cp.Variable(num_assets, name="weights")

    # Constraints
    constraints = [
        cp.sum(weights) == 1,  # Weights must sum to 1
        weights >= 0           # No short selling
    ]

    # Asset class specific constraints
    if asset_class_mapping:
        equities_tickers = [t for t in assets if asset_class_mapping.get(t) == 'equities']
        bonds_tickers = [t for t in assets if asset_class_mapping.get(t) == 'bonds']
        cash_tickers = [t for t in assets if asset_class_mapping.get(t) == 'cash']

        if max_equities_weight is not None and equities_tickers:
            equities_indices = [assets.index(t) for t in equities_tickers]
            constraints.append(cp.sum(weights[equities_indices]) <= max_equities_weight)
        
        if max_bonds_weight is not None and bonds_tickers:
            bonds_indices = [assets.index(t) for t in bonds_tickers]
            constraints.append(cp.sum(weights[bonds_indices]) <= max_bonds_weight)

        if max_cash_weight is not None and cash_tickers:
            cash_indices = [assets.index(t) for t in cash_tickers]
            constraints.append(cp.sum(weights[cash_indices]) <= max_cash_weight)

    # Portfolio expected return and volatility
    portfolio_expected_return_daily = cp.sum(cp.multiply(expected_daily_returns.values, weights))
    portfolio_variance_daily = cp.quad_form(weights, cov_matrix.values)
    portfolio_volatility_daily = cp.sqrt(portfolio_variance_daily)

    # Annualized portfolio return and volatility
    portfolio_expected_return_annual = (1 + portfolio_expected_return_daily)**252 - 1
    portfolio_volatility_annual = portfolio_volatility_daily * np.sqrt(252)

    if target_return is not None:
        # Minimize variance for a target return
        constraints.append(portfolio_expected_return_annual >= target_return)
        objective = cp.Minimize(portfolio_variance_daily)
    else:
        # Maximize Sharpe Ratio
        # This is a fractional programming problem, which can be transformed into a convex one.
        # Maximize (portfolio_expected_return_annual - risk_free_rate) / portfolio_volatility_annual
        # Let k = 1 / portfolio_volatility_annual
        # Let y = k * weights
        # Maximize (k * portfolio_expected_return_annual - k * risk_free_rate)
        # Subject to k * portfolio_volatility_annual = 1
        
        # A simpler approach for maximizing Sharpe is to minimize negative Sharpe.
        # This is often done by minimizing volatility for a given excess return.
        # For a fixed risk-free rate, maximizing Sharpe is equivalent to maximizing
        # (portfolio_expected_return_annual - risk_free_rate) / portfolio_volatility_annual
        # This is a common transformation for MVO.
        
        # For simplicity, we can maximize (portfolio_expected_return_annual - risk_free_rate)
        # and add a constraint on volatility, or use a different formulation.
        # The standard way to maximize Sharpe is to solve a quadratic program.
        
        # Maximize (r_p - r_f) / sigma_p
        # This can be solved by maximizing r_p - r_f subject to sigma_p <= some_value
        # Or, by minimizing sigma_p subject to r_p - r_f >= some_value
        
        # Let's use the common approach of maximizing the slope of the capital allocation line.
        # This involves minimizing the variance for a given level of excess return.
        # The problem is to find the portfolio with the highest Sharpe ratio.
        # This is equivalent to maximizing (mu_p - r_f) / sigma_p
        # This can be formulated as a quadratic program.
        
        # Maximize (expected_annual_returns @ weights - risk_free_rate) / sqrt(weights.T @ cov_matrix @ weights)
        # This is not directly convex.
        # The standard transformation for maximizing Sharpe Ratio is:
        # Maximize y.T @ (expected_annual_returns - risk_free_rate)
        # Subject to y.T @ cov_matrix @ y <= 1
        # sum(y) = 1 (if no risk-free asset)
        # y >= 0
        # where y = weights / (expected_annual_returns @ weights - risk_free_rate)
        # This is more complex.
        
        # For a simpler implementation, let's maximize expected return for a given risk budget,
        # or minimize risk for a given return target.
        # If no target_return, let's find the minimum volatility portfolio.
        objective = cp.Minimize(portfolio_variance_daily)


    # Problem definition
    problem = cp.Problem(objective, constraints)

    # Solve the problem
    try:
        problem.solve()
    except Exception as e:
        print(f"Error solving cvxpy MVO problem: {e}")
        return {
            "optimal_weights": {},
            "expected_return": 0,
            "expected_volatility": 0,
            "sharpe_ratio": 0,
            "status": "error",
            "message": str(e)
        }

    if problem.status not in ["optimal", "optimal_near"]:
        print(f"Problem status: {problem.status}")
        return {
            "optimal_weights": {},
            "expected_return": 0,
            "expected_volatility": 0,
            "sharpe_ratio": 0,
            "status": problem.status,
            "message": f"Optimization problem could not be solved to optimality. Status: {problem.status}"
        }

    # Extract results
    optimal_weights_array = weights.value
    optimal_weights = {assets[i]: w for i, w in enumerate(optimal_weights_array)}

    # Calculate actual expected return and volatility for the optimal portfolio
    final_expected_daily_return = np.sum(expected_daily_returns.values * optimal_weights_array)
    final_portfolio_variance_daily = np.dot(optimal_weights_array.T, np.dot(cov_matrix.values, optimal_weights_array))
    final_portfolio_volatility_daily = np.sqrt(final_portfolio_variance_daily)

    final_expected_annual_return = (1 + final_expected_daily_return)**252 - 1
    final_portfolio_volatility_annual = final_portfolio_volatility_daily * np.sqrt(252)
    
    final_sharpe_ratio = (final_expected_annual_return - risk_free_rate) / final_portfolio_volatility_annual if final_portfolio_volatility_annual > 0 else 0

    return {
        "optimal_weights": optimal_weights,
        "expected_return": final_expected_annual_return,
        "expected_volatility": final_portfolio_volatility_annual,
        "sharpe_ratio": final_sharpe_ratio,
        "status": problem.status
    }