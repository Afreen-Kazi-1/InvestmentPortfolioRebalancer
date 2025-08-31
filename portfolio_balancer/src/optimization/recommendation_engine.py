import pandas as pd
import numpy as np
from portfolio_balancer.src.evaluation.metrics import calculate_portfolio_volatility, calculate_covariance_matrix, calculate_daily_returns
from portfolio_balancer.src.api.services import get_asset_class_mapping

def generate_recommendations_mvp(
    current_portfolio_snapshot: dict,
    user_risk_tolerance: float, # e.g., 0.15 for 15% max portfolio volatility
    price_history_df: pd.DataFrame
) -> list:
    """
    Generates portfolio recommendations based on simple rules and current portfolio state.

    Args:
        current_portfolio_snapshot (dict): Snapshot of the current portfolio from get_portfolio_snapshot.
        user_risk_tolerance (float): User's maximum acceptable portfolio volatility.
        price_history_df (pd.DataFrame): DataFrame with historical closing prices for all assets in the portfolio.

    Returns:
        list: A list of recommendation strings.
    """
    recommendations = []
    
    breakdown = current_portfolio_snapshot['breakdown']
    total_value = current_portfolio_snapshot['total_value']

    if not breakdown:
        return ["Your portfolio is empty. Consider adding some assets to get recommendations."]

    # Convert breakdown to a more usable format
    current_weights = {item['ticker']: item['weight'] for item in breakdown}
    tickers = list(current_weights.keys())

    # Ensure price_history_df contains all tickers in the portfolio
    # And align columns for calculations
    aligned_price_history = price_history_df[price_history_df.columns.intersection(tickers)]
    
    if aligned_price_history.empty:
        return ["Not enough historical price data to generate detailed recommendations."]

    # Calculate current portfolio volatility
    daily_returns = calculate_daily_returns(aligned_price_history)
    cov_matrix = calculate_covariance_matrix(daily_returns)
    
    # Align weights with the assets in aligned_price_history
    current_weights_array = np.array([current_weights.get(col, 0) for col in aligned_price_history.columns])
    
    # Normalize weights if they don't sum to 1 (e.g., if some assets had no price history)
    if np.sum(current_weights_array) > 0:
        current_weights_array = current_weights_array / np.sum(current_weights_array)
    else:
        current_weights_array = np.array([1/len(aligned_price_history.columns)] * len(aligned_price_history.columns))

    current_portfolio_volatility = calculate_portfolio_volatility(current_weights_array, cov_matrix)

    # Rule 1: Detect concentration (asset > 25%)
    for item in breakdown:
        if item['weight'] > 0.25:
            recommendations.append(
                f"Reduce concentration in {item['ticker']} (currently {item['weight']:.1%}). "
                "Consider diversifying with sector or market ETFs."
            )

    # Rule 2: If volatility > user tolerance → propose shifting % from high-σ assets to bonds/cash.
    if current_portfolio_volatility > user_risk_tolerance:
        # Identify high-volatility assets
        asset_volatilities = daily_returns.std() * np.sqrt(252)
        high_sigma_assets = asset_volatilities[asset_volatilities > asset_volatilities.mean()].sort_values(ascending=False)
        
        if not high_sigma_assets.empty:
            recommendations.append(
                f"Your portfolio volatility ({current_portfolio_volatility:.2%}) exceeds your tolerance ({user_risk_tolerance:.2%}). "
                "Consider shifting some allocation from high-volatility assets like "
                f"{', '.join(high_sigma_assets.index[:3])} to bonds or cash."
            )
        else:
            recommendations.append(
                f"Your portfolio volatility ({current_portfolio_volatility:.2%}) exceeds your tolerance ({user_risk_tolerance:.2%}). "
                "Consider shifting some allocation to bonds or cash."
            )

    # Rule 3: If correlation high across top holdings → suggest low-corr ETF
    # (This requires more sophisticated analysis, for MVP, let's simplify)
    # Identify top holdings by weight
    top_holdings = sorted(breakdown, key=lambda x: x['weight'], reverse=True)[:5]
    top_tickers = [item['ticker'] for item in top_holdings if item['ticker'] in daily_returns.columns]

    if len(top_tickers) > 1:
        top_returns = daily_returns[top_tickers]
        correlation_matrix = top_returns.corr()
        
        # Check for high average correlation among top holdings
        # Exclude self-correlation (diagonal)
        sum_corr = 0
        count_corr = 0
        for i in range(len(top_tickers)):
            for j in range(i + 1, len(top_tickers)):
                sum_corr += correlation_matrix.iloc[i, j]
                count_corr += 1
        
        if count_corr > 0 and (sum_corr / count_corr) > 0.7: # Threshold for high correlation
            recommendations.append(
                f"The top holdings in your portfolio ({', '.join(top_tickers)}) show high correlation. "
                "Consider adding assets with low correlation, such as healthcare (e.g., XLV) or utilities ETFs, "
                "to improve diversification."
            )
    
    if not recommendations:
        recommendations.append("Your portfolio looks well-balanced based on current rules. Keep monitoring!")

    return recommendations