from flask import Blueprint, jsonify, request
from portfolio_balancer.src.api.price_service import price_service
from portfolio_balancer.src.api.services import get_portfolio_snapshot
from portfolio_balancer.src.data.database import db
from portfolio_balancer.src.data.models import User, RiskProfile, TargetAllocation, Holding, PriceHistory, LatestPrice
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/risk-profile', methods=['POST'])
def create_risk_profile():
    data = request.get_json()
    # For now, we'll just print the data.
    # In a real application, you would save this to the database.
    print(data)
    return jsonify({'message': 'Risk profile created successfully'}), 201

@api_bp.route('/portfolio', methods=['POST'])
def add_portfolio():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.endswith('.csv'):
            # Process CSV file
            # For now, just print the filename
            print(f"Received CSV file: {file.filename}")
            return jsonify({'message': 'CSV received'}), 200
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    else:
        data = request.get_json()
        # Process manual entry
        # For now, just print the data
        print(f"Received manual entry: {data}")
        return jsonify({'message': 'Manual entry received'}), 200

@api_bp.route('/portfolio', methods=['GET'])
def get_portfolio():
    # In a real application, you would fetch this from the database
    mock_holdings = [
        {'id': 1, 'ticker': 'AAPL', 'quantity': 10, 'avg_cost': 150.0},
        {'id': 2, 'ticker': 'GOOGL', 'quantity': 5, 'avg_cost': 2800.0},
        {'id': 3, 'ticker': 'BND', 'quantity': 20, 'avg_cost': 85.0},
    ]
    return jsonify(mock_holdings)

@api_bp.route('/prices/history/<ticker>', methods=['GET'])
def get_price_history(ticker):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400
    
    history = price_service.get_historical_prices(ticker, start_date, end_date)
    return jsonify(history)

@api_bp.route('/prices/latest/<ticker>', methods=['GET'])
def get_latest_price_api(ticker):
    latest_price = price_service.get_latest_price(ticker)
    if latest_price is not None:
        return jsonify({'ticker': ticker, 'latest_price': latest_price})
    else:
        return jsonify({'error': f'Could not retrieve latest price for {ticker}'}), 404

@api_bp.route('/portfolio/snapshot/<int:user_id>', methods=['GET'])
def portfolio_snapshot(user_id):
    snapshot = get_portfolio_snapshot(user_id)
    return jsonify(snapshot)

@api_bp.route('/rebalance/suggest/<int:user_id>', methods=['GET'])
def rebalance_suggest(user_id):
    suggestion = suggest_rebalance(user_id)
    return jsonify(suggestion)