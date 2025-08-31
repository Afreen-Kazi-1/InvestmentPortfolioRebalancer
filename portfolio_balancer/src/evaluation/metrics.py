import pandas as pd
import numpy as np

def calculate_daily_returns(price_history: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates daily returns for each asset in the price history.
    
    Args:
        price_history (pd.DataFrame): DataFrame with asset prices, indexed by date.
                                      Each column represents an asset.
                                      
    Returns:
        pd.DataFrame: DataFrame with daily returns.
    """
    return price_history.pct_change().dropna()

def calculate_covariance_matrix(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the covariance matrix of daily returns.
    
    Args:
        daily_returns (pd.DataFrame): DataFrame with daily returns.
        
    Returns:
        pd.DataFrame: Covariance matrix.
    """
    return daily_returns.cov()

def calculate_annualized_volatility(daily_returns: pd.DataFrame) -> pd.Series:
    """
    Calculates the annualized volatility for each asset.
    
    Args:
        daily_returns (pd.DataFrame): DataFrame with daily returns.
        
    Returns:
        pd.Series: Annualized volatility for each asset.
    """
    return daily_returns.std() * np.sqrt(252) # Assuming 252 trading days in a year

def calculate_portfolio_volatility(weights: np.ndarray, cov_matrix: pd.DataFrame) -> float:
    """
    Calculates the portfolio volatility.
    
    Args:
        weights (np.ndarray): Array of asset weights.
        cov_matrix (pd.DataFrame): Covariance matrix of asset returns.
        
    Returns:
        float: Portfolio volatility.
    """
    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    return np.sqrt(portfolio_variance)

def calculate_sharpe_ratio(mean_returns: pd.Series, portfolio_volatility: float, risk_free_rate: float = 0.01) -> float:
    """
    Calculates the Sharpe Ratio.
    
    Args:
        mean_returns (pd.Series): Mean daily returns for each asset.
        portfolio_volatility (float): Portfolio volatility.
        risk_free_rate (float): Risk-free rate (annualized).
        
    Returns:
        float: Sharpe Ratio.
    """
    # Annualize mean returns for Sharpe Ratio calculation
    annualized_mean_return = (1 + mean_returns).prod()**(252/len(mean_returns)) - 1
    
    if portfolio_volatility == 0:
        return 0 # Avoid division by zero
    return (annualized_mean_return - risk_free_rate) / portfolio_volatility

def calculate_risk_metrics(price_history: pd.DataFrame, weights: np.ndarray, risk_free_rate: float = 0.01) -> dict:
    """
    Computes various risk metrics for a portfolio.
    
    Args:
        price_history (pd.DataFrame): DataFrame with asset prices, indexed by date.
                                      Each column represents an asset.
        weights (np.ndarray): Array of asset weights.
        risk_free_rate (float): Annualized risk-free rate.
        
    Returns:
        dict: A dictionary containing 'risk_score', 'volatility', and 'sharpe_ratio'.
    """
    daily_returns = calculate_daily_returns(price_history)
    cov_matrix = calculate_covariance_matrix(daily_returns)
    
    # Ensure weights and cov_matrix are aligned
    if len(weights) != cov_matrix.shape[0]:
        raise ValueError("Number of weights must match the number of assets in the covariance matrix.")
        
    portfolio_volatility_val = calculate_portfolio_volatility(weights, cov_matrix)
    
    # For Sharpe, we need mean portfolio return. Simple mean return for now.
    # This assumes weights are applied to daily returns to get portfolio daily returns
    portfolio_daily_returns = daily_returns.dot(weights)
    mean_portfolio_daily_return = portfolio_daily_returns.mean()
    
    sharpe_ratio_val = calculate_sharpe_ratio(portfolio_daily_returns, portfolio_volatility_val, risk_free_rate)
    
    # A simple risk score could be just the volatility, or a combination.
    # For now, let's use volatility as the risk_score.
    risk_score = portfolio_volatility_val
    
    return {
        "risk_score": risk_score,
        "volatility": portfolio_volatility_val,
        "sharpe_ratio": sharpe_ratio_val
    }