from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import os
import pandas as pd # Added for risk metrics
import numpy as np # Added for risk metrics

load_dotenv() # Load environment variables from .env file

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

from portfolio_balancer.src.api.price_service import price_service
from portfolio_balancer.src.api.services import get_portfolio_snapshot, get_asset_class_mapping
from portfolio_balancer.src.api.models import User, RiskProfile, TargetAllocation, Holding, PriceHistory
from portfolio_balancer.src.evaluation.metrics import calculate_risk_metrics
from portfolio_balancer.src.optimization.rebalancer import deterministic_rebalance
from portfolio_balancer.src.optimization.cvxpy_rebalancer import cvxpy_rebalance
from portfolio_balancer.src.optimization.recommendation_engine import generate_recommendations_mvp
from portfolio_balancer.src.optimization.markowitz_mvo import markowitz_mvo
from portfolio_balancer.src.evaluation.backtest import compare_strategies, generate_backtest_report
from portfolio_balancer.src.api.auth import init_auth_routes

app = Flask(__name__)
CORS(app)

# Initialize authentication routes
init_auth_routes(app, supabase)

@app.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({'message': 'Test route is working!'}), 200


@app.route('/api/user/<int:user_id>/target-allocation', methods=['POST'])
def set_user_target_allocation(user_id):
    data = request.get_json()
    data['user_id'] = user_id
    try:
        response = supabase.table('target_allocation').upsert(data).execute()
        return jsonify({'message': 'Target allocation set successfully', 'data': response.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/risk-profile', methods=['POST'])
def create_risk_profile(user_id):
    data = request.get_json()
    data['user_id'] = user_id
    try:
        response = supabase.table('risk_profile').insert(data).execute()
        return jsonify({'message': 'Risk profile created successfully', 'data': response.data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/portfolio/import', methods=['POST'])
def import_portfolio():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            # Expected columns: ticker, quantity, purchase_price, purchase_date
            required_columns = ['ticker', 'quantity', 'purchase_price', 'purchase_date']
            if not all(col in df.columns for col in required_columns):
                return jsonify({'error': f'CSV must contain columns: {", ".join(required_columns)}'}), 400

            holdings_to_insert = []
            for index, row in df.iterrows():
                holdings_to_insert.append({
                    'user_id': user_id,
                    'ticker': row['ticker'],
                    'quantity': row['quantity'],
                    'purchase_price': row['purchase_price'],
                    'purchase_date': row['purchase_date']
                })
            
            if holdings_to_insert:
                response = supabase.table('holding').insert(holdings_to_insert).execute()
                return jsonify({"message": "Portfolio imported", "holdings": response.data}), 200
            else:
                return jsonify({"message": "No holdings to import"}), 200

        except Exception as e:
            return jsonify({'error': f'Error processing CSV: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type, only CSV is supported'}), 400

@app.route('/holdings', methods=['POST'])
def add_holdings():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    data = request.get_json()
    if not isinstance(data, list):
        data = [data] # Ensure data is a list of holdings

    holdings_to_insert = []
    for holding in data:
        ticker = holding.get('ticker')
        quantity = holding.get('quantity')
        purchase_price = holding.get('purchase_price')
        purchase_date = holding.get('purchase_date')

        if not all([ticker, quantity, purchase_price, purchase_date]):
            return jsonify({'error': 'Each holding must contain ticker, quantity, purchase_price, and purchase_date'}), 400
        
        holdings_to_insert.append({
            'user_id': user_id,
            'ticker': ticker,
            'quantity': quantity,
            'purchase_price': purchase_price,
            'purchase_date': purchase_date
        })
    
    try:
        response = supabase.table('holding').insert(holdings_to_insert).execute()
        return jsonify({"message": "Holdings added", "holdings": response.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/target-allocation', methods=['POST'])
def set_target_allocation():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    data = request.get_json()
    data['user_id'] = user_id
    try:
        # Supabase upsert: try to update if exists, else insert
        response = supabase.table('target_allocation').upsert(data).execute()
        return jsonify({'message': 'Target allocation set successfully', 'data': response.data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/portfolio', methods=['GET'])
def get_portfolio(user_id):
    try:
        response = supabase.table('holding').select("*").eq("user_id", user_id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/prices/<ticker>', methods=['GET'])
def get_price_history_by_date(ticker):
    from_date_str = request.args.get('from')
    if not from_date_str:
        return jsonify({'error': 'from date is required'}), 400

    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format for "from". Use YYYY-MM-DD.'}), 400

    # Fetch historical prices from the 'price_history' table
    # Assuming 'date' column is stored as a string in 'YYYY-MM-DD' format or similar
    try:
        response = supabase.table('price_history') \
            .select("date, close") \
            .eq("ticker", ticker) \
            .gte("date", from_date_str) \
            .order("date", desc=False) \
            .execute()
        
        prices_data = response.data
        
        # Format the output as specified
        formatted_prices = []
        for item in prices_data:
            formatted_prices.append({
                "date": item['date'],
                "close": item['close']
            })

        return jsonify({
            "ticker": ticker,
            "prices": formatted_prices
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error fetching price history: {str(e)}'}), 500

@app.route('/api/prices/latest/<ticker>', methods=['GET'])
def get_latest_price_api(ticker):
    latest_price_obj = price_service.get_latest_price(ticker)
    if latest_price_obj is not None:
        return jsonify({'ticker': ticker, 'latest_price': latest_price_obj})
    else:
        return jsonify({'error': f'Could not retrieve latest price for {ticker}'}), 404


@app.route('/portfolio/snapshot', methods=['GET'])
def portfolio_snapshot():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    snapshot = get_portfolio_snapshot(user_id)
    return jsonify(snapshot)

@app.route('/api/user/<int:user_id>/historical-allocation', methods=['GET'])
def get_historical_allocation(user_id):
    try:
        historical_data = get_historical_portfolio_by_asset_class(user_id)
        return jsonify(historical_data)
    except Exception as e:
        return jsonify({'error': f'Error fetching historical allocation: {str(e)}'}), 500

@app.route('/portfolio/risk', methods=['GET'])
def portfolio_risk():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    # Fetch user's holdings
    holdings_data = supabase.table('holding').select("*").eq("user_id", user_id).execute().data
    
    if not holdings_data:
        return jsonify({"error": "No holdings found for this user."}), 404

    tickers = [h['ticker'] for h in holdings_data]
    
    # Fetch historical prices for all tickers
    price_history_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5) # Last 5 years of data
    
    for ticker in tickers:
        history = price_service.get_historical_prices(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            price_history_data[ticker] = df['close'] # Changed from 'Close' to 'close'
            
    # Filter out illiquid assets (those with no price history)
    liquid_tickers = [t for t in tickers if t in price_history_data]
    if not liquid_tickers:
        return jsonify({"error": "No liquid assets found for risk calculation. All assets are illiquid or have no price history."}), 500
    
    # Re-filter holdings to only include liquid assets
    holdings_data = [h for h in holdings_data if h['ticker'] in liquid_tickers]
    if not holdings_data:
        return jsonify({"error": "No liquid holdings found for this user after filtering."}), 404

    price_history_df = pd.DataFrame({t: price_history_data[t] for t in liquid_tickers}).dropna()
    
    if price_history_df.empty:
        return jsonify({"error": "Not enough overlapping historical price data for risk calculation after dropping NaNs."}), 500

    price_history_df = pd.DataFrame(price_history_data).dropna()

    # Calculate current weights (simplified - ideally from get_portfolio_snapshot)
    # For accurate risk metrics, weights should reflect the period of price history
    # For now, let's assume equal weights for simplicity or fetch from snapshot
    snapshot = get_portfolio_snapshot(user_id)
    current_portfolio_value = snapshot['total_value']
    current_weights = {}
    for item in snapshot['breakdown']:
        current_weights[item['ticker']] = item['value'] / current_portfolio_value if current_portfolio_value > 0 else 0
    
    # Align weights with the assets in price_history_df
    aligned_weights = np.array([current_weights.get(col, 0) for col in price_history_df.columns])
    
    # Normalize weights if they don't sum to 1 (e.g., if some assets had no price history)
    if np.sum(aligned_weights) > 0:
        aligned_weights = aligned_weights / np.sum(aligned_weights)
    else:
        # Fallback to equal weights if no valid weights can be formed
        aligned_weights = np.array([1/len(price_history_df.columns)] * len(price_history_df.columns))

    try:
        risk_metrics = calculate_risk_metrics(price_history_df, aligned_weights)
        return jsonify(risk_metrics)
    except Exception as e:
        return jsonify({"error": f"Error calculating risk metrics: {str(e)}"}), 500

@app.route('/recommend', methods=['POST'])
def recommend_assets():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    data = request.get_json()
    goals = data.get('goals')
    risk_level = data.get('risk_level')

    if not all([goals, risk_level]):
        return jsonify({'error': 'goals and risk_level are required'}), 400

    # Map risk_level (e.g., "moderate") to a numerical risk_tolerance for the engine
    # This is a simplified mapping; a more robust solution might use a dedicated service
    risk_tolerance_map = {
        "conservative": 0.05,
        "moderate": 0.10,
        "aggressive": 0.15
    }
    user_risk_tolerance = risk_tolerance_map.get(risk_level.lower(), 0.10) # Default to moderate

    # Fetch user's holdings (needed for generate_recommendations_mvp)
    holdings_data = supabase.table('holding').select("*").eq("user_id", user_id).execute().data
    
    if not holdings_data:
        # If no holdings, we can still recommend based on goals/risk, but the MVP engine needs a snapshot
        # For now, return an error or provide a default set of recommendations
        return jsonify({"error": "No holdings found for this user. Recommendations require an existing portfolio."}), 404

    tickers = [h['ticker'] for h in holdings_data]
    
    # Fetch historical prices for all tickers (needed for generate_recommendations_mvp)
    price_history_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5) # Last 5 years of data
    
    for ticker in tickers:
        history = price_service.get_historical_prices(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            price_history_data[ticker] = df['close'] # Changed from 'Close' to 'close'
            
    # Filter out illiquid assets (those with no price history)
    liquid_tickers = [t for t in tickers if t in price_history_data]
    if not liquid_tickers:
        return jsonify({"error": "No liquid assets found for recommendations. All assets are illiquid or have no price history."}), 500
    
    # Re-filter holdings to only include liquid assets for snapshot
    holdings_data = [h for h in holdings_data if h['ticker'] in liquid_tickers]
    if not holdings_data:
        return jsonify({"error": "No liquid holdings found for this user after filtering for recommendations."}), 404

    price_history_df = pd.DataFrame({t: price_history_data[t] for t in liquid_tickers}).dropna()

    if price_history_df.empty:
        return jsonify({"error": "Not enough overlapping historical price data for recommendations after dropping NaNs."}), 500

    price_history_df = pd.DataFrame(price_history_data).dropna()

    snapshot = get_portfolio_snapshot(user_id)

    try:
        recommendations = generate_recommendations_mvp(snapshot, user_risk_tolerance, price_history_df)
        
        # Format the output to match the desired structure
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                "ticker": rec.get('ticker'),
                "reason": rec.get('reason', 'Based on your goals and risk level.')
            })

        return jsonify({
            "recommended_assets": formatted_recommendations,
            "justification": f"Based on your {risk_level} risk tolerance and {goals} goals."
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error generating recommendations: {str(e)}"}), 500

@app.route('/rebalance/suggest', methods=['POST'])
def rebalance_suggest():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    data = request.get_json()
    target_allocation_input = data.get('target_allocation')
    if not target_allocation_input:
        return jsonify({'error': 'target_allocation is required in the request body'}), 400

    # Convert target_allocation_input to the format expected by the rebalancer
    # This assumes target_allocation_input is like {"stocks": 0.6, "bonds": 0.4}
    # and we need to map these to specific tickers.
    # For now, we'll use a simplified approach and assume target_allocation_input
    # directly maps to asset classes that can be used to derive ticker-level targets.
    
    rebalance_type = data.get('rebalance_type', 'deterministic') # 'deterministic' or 'cvxpy'
    min_trade_threshold = data.get('min_trade_threshold', 0.01) # Default to $0.01
    min_cash_reserve = data.get('min_cash_reserve', 0.0) # Default to $0.0
    fees_per_trade = data.get('fees_per_trade', 0.0) # Default to $0.0
    round_to_nearest_share = data.get('round_to_nearest_share', False)
    epsilon = data.get('epsilon', 0.01) # For cvxpy optimization

    # Fetch current portfolio snapshot
    snapshot = get_portfolio_snapshot(user_id)
    current_portfolio_value = snapshot['total_value']
    
    current_portfolio_dict = {}
    asset_prices = {}
    # Also collect all tickers for price history fetching
    all_tickers_in_portfolio = []
    for item in snapshot['breakdown']:
        current_portfolio_dict[item['ticker']] = {'amount': item['quantity'], 'price': item['latest_price']}
        asset_prices[item['ticker']] = item['latest_price']
        all_tickers_in_portfolio.append(item['ticker'])
    
    # Add cash to current portfolio if not already present
    # Assuming cash is part of the breakdown if it exists, otherwise initialize to 0
    if 'CASH' not in current_portfolio_dict:
        current_portfolio_dict['CASH'] = {'value': 0} # Or fetch actual cash balance

    # Fetch target allocation
    target_allocation_data = supabase.table('target_allocation').select("*").eq("user_id", user_id).limit(1).execute().data
    if not target_allocation_data:
        return jsonify({"error": "Target allocation not set for this user."}), 400
    
    target_alloc = target_allocation_data[0]
    target_weights = {
        'equities': target_alloc.get('equities', 0),
        'bonds': target_alloc.get('bonds', 0),
        'cash': target_alloc.get('cash', 0)
    }

    # Map current holdings to asset classes to get target weights per ticker
    # This is a crucial step that needs a proper mapping mechanism
    # For now, we'll use a simplified mapping or assume target_weights are per ticker
    # A more robust solution would involve a separate service/function to map tickers to asset classes
    # and then distribute the target asset class weights among the tickers in that class.
    
    # Let's use get_asset_class_mapping to map tickers to asset classes
    tickers = [h['ticker'] for h in holdings_data] # Ensure tickers list is available
    asset_class_mapping = get_asset_class_mapping(tickers)
    
    # Distribute target asset class weights to individual tickers
    final_target_weights_per_ticker = {}
    for item in snapshot['breakdown']:
        ticker = item['ticker']
        current_value = item['value']
        asset_class = asset_class_mapping.get(ticker)
        
        if asset_class and asset_class in target_weights and current_portfolio_value > 0: # Check total_value > 0 to avoid division by zero
            # Calculate the ticker's proportion within its current asset class
            # This is a simplification. A more robust approach would consider the value of assets within each class.
            # For now, we'll distribute target asset class weight proportionally to current value.
            
            # First, calculate current value per asset class
            current_value_per_asset_class = {'equities': 0, 'bonds': 0, 'cash': 0, 'crypto': 0, 'other': 0}
            for holding_item in snapshot['breakdown']:
                holding_asset_class = asset_class_mapping.get(holding_item['ticker'])
                if holding_asset_class in current_value_per_asset_class:
                    current_value_per_asset_class[holding_asset_class] += holding_item['value']
            
            if current_value_per_asset_class[asset_class] > 0:
                proportion_in_class = current_value / current_value_per_asset_class[asset_class]
                final_target_weights_per_ticker[ticker] = target_weights[asset_class] * proportion_in_class
            else:
                final_target_weights_per_ticker[ticker] = 0 # If no current value in class, target is 0 for this asset
        elif ticker == 'CASH':
            final_target_weights_per_ticker['CASH'] = target_weights.get('cash', 0)
        else:
            final_target_weights_per_ticker[ticker] = 0 # Default to 0 if no mapping or target

    # Ensure all tickers in current_portfolio_dict are in final_target_weights_per_ticker
    for ticker in current_portfolio_dict.keys():
        if ticker not in final_target_weights_per_ticker:
            final_target_weights_per_ticker[ticker] = 0
    
    # Normalize final_target_weights_per_ticker to sum to 1 (excluding CASH for now if it's a reserve)
    # The rebalancer function handles CASH as a regular asset.
    total_target_weight_sum = sum(final_target_weights_per_ticker.values())
    if total_target_weight_sum > 0:
        final_target_weights_per_ticker = {k: v / total_target_weight_sum for k, v in final_target_weights_per_ticker.items()}
    
    # Add CASH to the target weights if it's not already there and has a target
    if 'CASH' not in final_target_weights_per_ticker and 'cash' in target_weights:
        final_target_weights_per_ticker['CASH'] = target_weights['cash']

    try:
        if rebalance_type == 'deterministic':
            rebalance_result = deterministic_rebalance(
                current_portfolio=current_portfolio_dict,
                target_weights=final_target_weights_per_ticker,
                total_value=current_portfolio_value,
                min_trade_threshold=min_trade_threshold,
                min_cash_reserve=min_cash_reserve,
                fees_per_trade=fees_per_trade,
                round_to_nearest_share=round_to_nearest_share,
                asset_prices=asset_prices
            )
        elif rebalance_type == 'cvxpy':
            rebalance_result = cvxpy_rebalance(
                current_portfolio=current_portfolio_dict,
                target_weights=final_target_weights_per_ticker,
                total_value=current_portfolio_value,
                asset_prices=asset_prices,
                min_trade_threshold=min_trade_threshold,
                min_cash_reserve=min_cash_reserve,
                fees_per_trade=fees_per_trade,
                epsilon=epsilon
            )
        else:
            return jsonify({"error": "Invalid rebalance_type. Must be 'deterministic' or 'cvxpy'."}), 400
            
        return jsonify(rebalance_result)
    except Exception as e:
        return jsonify({"error": f"Error rebalancing portfolio: {str(e)}"}), 500

@app.route('/api/portfolio/mvo/<int:user_id>', methods=['POST'])
def portfolio_mvo(user_id):
    data = request.get_json()
    risk_free_rate = data.get('risk_free_rate', 0.01)
    target_return = data.get('target_return', None)
    max_equities_weight = data.get('max_equities_weight', None)
    max_bonds_weight = data.get('max_bonds_weight', None)
    max_cash_weight = data.get('max_cash_weight', None)

    # Fetch user's holdings to get tickers
    holdings_data = supabase.table('holding').select("*").eq("user_id", user_id).execute().data
    if not holdings_data:
        return jsonify({"error": "No holdings found for this user."}), 404
    
    tickers = [h['ticker'] for h in holdings_data]
    
    # Fetch historical prices for all tickers
    price_history_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5) # Last 5 years of data for MVO
    
    for ticker in tickers:
        history = price_service.get_historical_prices(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            price_history_data[ticker] = df['close'] # Changed from 'Close' to 'close'
            
    # Filter out illiquid assets (those with no price history)
    liquid_tickers = [t for t in tickers if t in price_history_data]
    if not liquid_tickers:
        return jsonify({"error": "No liquid assets found for MVO. All assets are illiquid or have no price history."}), 500
    
    # Re-filter holdings to only include liquid assets for MVO
    holdings_data = [h for h in holdings_data if h['ticker'] in liquid_tickers]
    if not holdings_data:
        return jsonify({"error": "No liquid holdings found for this user after filtering for MVO."}), 404

    price_history_df = pd.DataFrame({t: price_history_data[t] for t in liquid_tickers}).dropna()

    if price_history_df.empty:
        return jsonify({"error": "Not enough overlapping historical price data for MVO after dropping NaNs."}), 500

    price_history_df = pd.DataFrame(price_history_data).dropna()

    # Get asset class mapping for constraints
    asset_class_mapping = get_asset_class_mapping(tickers)

    try:
        mvo_result = markowitz_mvo(
            price_history=price_history_df,
            risk_free_rate=risk_free_rate,
            target_return=target_return,
            max_equities_weight=max_equities_weight,
            max_bonds_weight=max_bonds_weight,
            max_cash_weight=max_cash_weight,
            asset_class_mapping=asset_class_mapping
        )
        return jsonify(mvo_result)
    except Exception as e:
        return jsonify({"error": f"Error performing Markowitz MVO: {str(e)}"}), 500

@app.route('/backtest/run', methods=['POST'])
def backtest_run():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    data = request.get_json()
    strategy = data.get('strategy')
    from_date_str = data.get('from')
    to_date_str = data.get('to')

    if not all([strategy, from_date_str, to_date_str]):
        return jsonify({'error': 'strategy, from, and to dates are required'}), 400

    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    rebalance_frequency = data.get('rebalance_frequency', 'quarterly')
    drift_threshold = data.get('drift_threshold', 0.05)
    fees_per_trade = data.get('fees_per_trade', 0.0)
    min_trade_threshold = data.get('min_trade_threshold', 0.01)
    risk_free_rate = data.get('risk_free_rate', 0.01)
    
    # Target weights for the user's strategy
    target_allocation_data = supabase.table('target_allocation').select("*").eq("user_id", user_id).limit(1).execute().data
    if not target_allocation_data:
        return jsonify({"error": "Target allocation not set for this user."}), 400
    
    target_alloc = target_allocation_data[0]
    user_target_weights_asset_class = {
        'equities': target_alloc.get('equities', 0),
        'bonds': target_alloc.get('bonds', 0),
        'cash': target_alloc.get('cash', 0)
    }

    # Baseline weights (e.g., 60/40 stocks/bonds)
    # This needs to be defined based on common benchmarks or user preference
    # For simplicity, let's assume a fixed 60/40 for now, mapped to example tickers
    baseline_weights = {'AAPL': 0.3, 'GOOGL': 0.3, 'BND': 0.4} # Example baseline

    # MVO parameters for backtesting MVO strategy
    mvo_params = {
        'target_return': data.get('mvo_target_return', None),
        'max_equities_weight': data.get('mvo_max_equities_weight', None),
        'max_bonds_weight': data.get('mvo_max_bonds_weight', None),
        'max_cash_weight': data.get('mvo_max_cash_weight', None),
        # asset_class_mapping will be passed dynamically inside compare_strategies
    }

    # Fetch user's holdings to get initial portfolio and all tickers
    holdings_data = supabase.table('holding').select("*").eq("user_id", user_id).execute().data
    if not holdings_data:
        return jsonify({"error": "No holdings found for this user."}), 404
    
    initial_portfolio = {}
    all_tickers = []
    for h in holdings_data:
        ticker = h['ticker']
        quantity = h['quantity']
        # Fetch latest price for initial portfolio value calculation
        latest_price = price_service.get_latest_price(ticker)
        if latest_price is None:
            print(f"Warning: Could not get latest price for {ticker}. Skipping from initial portfolio.")
            continue
        initial_portfolio[ticker] = {'amount': quantity, 'price': latest_price}
        all_tickers.append(ticker)
    
    # Add CASH to initial portfolio if not present
    if 'CASH' not in initial_portfolio:
        initial_portfolio['CASH'] = {'value': 0} # Assume 0 cash if not explicitly held

    # Combine all tickers from user portfolio and baseline for price history fetching
    all_tickers_for_history = list(set(all_tickers) | set(baseline_weights.keys()))
    
    # Fetch historical prices for all relevant tickers
    price_history_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5) # Use 5 years for backtest period
    
    for ticker in all_tickers_for_history:
        history = price_service.get_historical_prices(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            price_history_data[ticker] = df['close'] # Changed from 'Close' to 'close'
            
    # Filter out illiquid assets (those with no price history)
    liquid_tickers_for_history = [t for t in all_tickers_for_history if t in price_history_data]
    if not liquid_tickers_for_history:
        return jsonify({"error": "No liquid assets found for backtesting. All assets are illiquid or have no price history."}), 500
    
    price_history_df = pd.DataFrame({t: price_history_data[t] for t in liquid_tickers_for_history}).dropna()

    if price_history_df.empty:
        return jsonify({"error": "Not enough overlapping historical price data for backtesting after dropping NaNs."}), 500

    price_history_df = pd.DataFrame(price_history_data).dropna()

    # Distribute user's asset class target weights to individual tickers for backtesting
    user_target_weights_ticker_level = {}
    user_asset_class_mapping = get_asset_class_mapping(all_tickers)
    
    # Calculate current value per asset class for user's portfolio
    current_value_per_asset_class = {'equities': 0, 'bonds': 0, 'cash': 0, 'crypto': 0, 'other': 0}
    for ticker, holding in initial_portfolio.items():
        if ticker == 'CASH':
            current_value_per_asset_class['cash'] += holding.get('value', 0)
        else:
            asset_class = user_asset_class_mapping.get(ticker)
            if asset_class in current_value_per_asset_class:
                current_value_per_asset_class[asset_class] += holding.get('amount', 0) * holding.get('price', 0)

    # Distribute target asset class weights proportionally to current values within each class
    for ticker in all_tickers:
        current_value = initial_portfolio.get(ticker, {}).get('amount', 0) * initial_portfolio.get(ticker, {}).get('price', 0)
        asset_class = user_asset_class_mapping.get(ticker)
        
        if asset_class and asset_class in user_target_weights_asset_class and current_value_per_asset_class[asset_class] > 0:
            proportion_in_class = current_value / current_value_per_asset_class[asset_class]
            user_target_weights_ticker_level[ticker] = user_target_weights_asset_class[asset_class] * proportion_in_class
        elif ticker == 'CASH':
            user_target_weights_ticker_level['CASH'] = user_target_weights_asset_class.get('cash', 0)
        else:
            user_target_weights_ticker_level[ticker] = 0

    # Normalize user_target_weights_ticker_level
    total_user_target_weight_sum = sum(user_target_weights_ticker_level.values())
    if total_user_target_weight_sum > 0:
        user_target_weights_ticker_level = {k: v / total_user_target_weight_sum for k, v in user_target_weights_ticker_level.items()}
    
    # Ensure CASH target is included if it has a target
    if 'CASH' not in user_target_weights_ticker_level and 'cash' in user_target_weights_asset_class:
        user_target_weights_ticker_level['CASH'] = user_target_weights_asset_class['cash']


    try:
        backtest_results = compare_strategies(
            price_history=price_history_df,
            initial_portfolio=initial_portfolio,
            target_weights=user_target_weights_ticker_level,
            baseline_weights=baseline_weights,
            rebalance_frequency=rebalance_frequency,
            drift_threshold=drift_threshold,
            fees_per_trade=fees_per_trade,
            min_trade_threshold=min_trade_threshold,
            risk_free_rate=risk_free_rate,
            mvo_params=mvo_params
        )
        
        report = generate_backtest_report(backtest_results)
        return jsonify(report)

    except Exception as e:
        return jsonify({"error": f"Error running backtest: {str(e)}"}), 500

@app.route('/report/latest', methods=['GET'])
def get_latest_report():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    # For demonstration, we'll generate a mock report.
    # In a real application, this would fetch actual report data,
    # potentially from a database or a generated file.
    
    # Example data for charts (these would be actual URLs to generated charts)
    charts = [
        f"/api/charts/portfolio_value_{user_id}.png",
        f"/api/charts/allocation_pie_{user_id}.png"
    ]

    # Example metrics (these would be fetched from analytics results)
    metrics = {
        "cagr": 0.11,
        "volatility": 0.15,
        "sharpe_ratio": 1.3
    }

    # Example summary (this would be dynamically generated)
    summary = "Your portfolio outperformed S&P 500 by 2.5% over the last year."

    return jsonify({
        "charts": charts,
        "metrics": metrics,
        "summary": summary
    }), 200

# Scheduler for daily price refresh
def refresh_all_prices():
    with app.app_context():
        # In a real application, you would fetch all unique tickers from user holdings
        # For now, let's use some mock tickers
        mock_tickers = ['AAPL', 'GOOGL', 'BND', 'BTC-USD']
        for ticker in mock_tickers:
            print(f"Refreshing latest price for {ticker}...")
            price_service.get_latest_price(ticker)
            # Also refresh historical data for the last 10 years
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365 * 10)).strftime('%Y-%m-%d')
            print(f"Refreshing historical data for {ticker} from {start_date} to {end_date}...")
            price_service.get_historical_prices(ticker, start_date, end_date)

if __name__ == '__main__':
    # db.create_all() # No longer using SQLAlchemy

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=refresh_all_prices, trigger="interval", days=1) # Run daily
    scheduler.start()

    # IMPORTANT: This application is for educational purposes only and does NOT execute real trades.
    # All rebalancing and recommendations are hypothetical.
    app.run(debug=True, use_reloader=False) # use_reloader=False to prevent duplicate jobs