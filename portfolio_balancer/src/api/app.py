from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from portfolio_balancer.src.data.database import db
from portfolio_balancer.src.data.models import User, RiskProfile, TargetAllocation, Holding, PriceHistory, LatestPrice
from portfolio_balancer.src.api.price_service import price_service
from portfolio_balancer.src.api.services import get_portfolio_snapshot
from portfolio_balancer.src.tasks.celery_app import make_celery

load_dotenv() # Load environment variables from .env file

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/portfolio_balancer_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Celery configuration
    app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://redis:6379/0')

    db.init_app(app)
    celery = make_celery(app)

    from portfolio_balancer.src.api.routes import api_bp
    app.register_blueprint(api_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')