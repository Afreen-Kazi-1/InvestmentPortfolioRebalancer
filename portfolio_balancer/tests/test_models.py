import unittest
from flask import Flask
from portfolio_balancer.src.data.database import db
from portfolio_balancer.src.data.models import User, RiskProfile, TargetAllocation, Holding, PriceHistory, LatestPrice
from datetime import datetime, date

class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_model(self):
        with self.app.app_context():
            user = User(username='testuser', password='hashedpassword')
            db.session.add(user)
            db.session.commit()
            self.assertIsNotNone(user.id)
            self.assertEqual(user.username, 'testuser')

    def test_risk_profile_model(self):
        with self.app.app_context():
            user = User(username='testuser', password='hashedpassword')
            db.session.add(user)
            db.session.commit()

            risk_profile = RiskProfile(user_id=user.id, age=30, horizon='long', drawdown='moderate', goal='retirement')
            db.session.add(risk_profile)
            db.session.commit()
            self.assertIsNotNone(risk_profile.id)
            self.assertEqual(risk_profile.user.username, 'testuser')

    def test_target_allocation_model(self):
        with self.app.app_context():
            user = User(username='testuser', password='hashedpassword')
            db.session.add(user)
            db.session.commit()

            target_allocation = TargetAllocation(user_id=user.id, equities=0.6, bonds=0.3, cash=0.1)
            db.session.add(target_allocation)
            db.session.commit()
            self.assertIsNotNone(target_allocation.id)
            self.assertEqual(target_allocation.equities, 0.6)

    def test_holding_model(self):
        with self.app.app_context():
            user = User(username='testuser', password='hashedpassword')
            db.session.add(user)
            db.session.commit()

            holding = Holding(user_id=user.id, ticker='AAPL', quantity=10, avg_cost=150.0)
            db.session.add(holding)
            db.session.commit()
            self.assertIsNotNone(holding.id)
            self.assertEqual(holding.ticker, 'AAPL')

    def test_price_history_model(self):
        with self.app.app_context():
            price_history = PriceHistory(ticker='AAPL', date=date(2023, 1, 1), close_price=170.0)
            db.session.add(price_history)
            db.session.commit()
            self.assertIsNotNone(price_history.id)
            self.assertEqual(price_history.close_price, 170.0)

    def test_latest_price_model(self):
        with self.app.app_context():
            latest_price = LatestPrice(ticker='AAPL', price=175.0, as_of=datetime.utcnow())
            db.session.add(latest_price)
            db.session.commit()
            self.assertIsNotNone(latest_price.id)
            self.assertEqual(latest_price.price, 175.0)

if __name__ == '__main__':
    unittest.main()