from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from portfolio_balancer.src.api.price_service import price_service

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    risk_profile = db.relationship('RiskProfile', backref='user', uselist=False)
    target_allocation = db.relationship('TargetAllocation', backref='user', uselist=False)
    holdings = db.relationship('Holding', backref='user', lazy=True)

class RiskProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    horizon = db.Column(db.String(50), nullable=False)
    drawdown = db.Column(db.String(50), nullable=False)
    goal = db.Column(db.String(50), nullable=False)

class TargetAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equities = db.Column(db.Float, nullable=False)
    bonds = db.Column(db.Float, nullable=False)
    cash = db.Column(db.Float, nullable=False)

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    avg_cost = db.Column(db.Float, nullable=False)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    # Ensure unique combination of ticker and date
    __table_args__ = (db.UniqueConstraint('ticker', 'date', name='_ticker_date_uc'),)

@app.route('/api/risk-profile', methods=['POST'])
def create_risk_profile():
    data = request.get_json()
    # For now, we'll just print the data.
    # In a real application, you would save this to the database.
    print(data)
    return jsonify({'message': 'Risk profile created successfully'}), 201

@app.route('/api/portfolio', methods=['POST'])
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

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    # In a real application, you would fetch this from the database
    mock_holdings = [
        {'id': 1, 'ticker': 'AAPL', 'quantity': 10, 'avg_cost': 150.0},
        {'id': 2, 'ticker': 'GOOGL', 'quantity': 5, 'avg_cost': 2800.0},
        {'id': 3, 'ticker': 'BND', 'quantity': 20, 'avg_cost': 85.0},
    ]
    return jsonify(mock_holdings)

@app.route('/api/prices/history/<ticker>', methods=['GET'])
def get_price_history(ticker):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400
    
    history = price_service.get_historical_prices(ticker, start_date, end_date)
    return jsonify(history)

@app.route('/api/prices/latest/<ticker>', methods=['GET'])
def get_latest_price_api(ticker):
    latest_price = price_service.get_latest_price(ticker)
    if latest_price is not None:
        return jsonify({'ticker': ticker, 'latest_price': latest_price})
    else:
        return jsonify({'error': f'Could not retrieve latest price for {ticker}'}), 404

from portfolio_balancer.src.api.services import get_portfolio_snapshot

@app.route('/api/portfolio/snapshot/<int:user_id>', methods=['GET'])
def portfolio_snapshot(user_id):
    snapshot = get_portfolio_snapshot(user_id)
    return jsonify(snapshot)

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
    with app.app_context():
        db.create_all()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=refresh_all_prices, trigger="interval", days=1) # Run daily
    scheduler.start()

    app.run(debug=True, use_reloader=False) # use_reloader=False to prevent duplicate jobs