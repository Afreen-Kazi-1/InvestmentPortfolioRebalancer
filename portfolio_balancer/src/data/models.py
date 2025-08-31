from portfolio_balancer.src.data.database import db
from datetime import datetime

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
    __table_args__ = (db.UniqueConstraint('ticker', 'date', name='_ticker_date_uc'),)

class LatestPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    as_of = db.Column(db.DateTime, default=datetime.utcnow)