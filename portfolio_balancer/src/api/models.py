# No longer using SQLAlchemy models directly, but keeping the structure for reference
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

class User:
    def __init__(self, id, email, created_at):
        self.id = id
        self.email = email
        self.created_at = created_at

class RiskProfile:
    def __init__(self, user_id, type, params):
        self.user_id = user_id
        self.type = type
        self.params = params

class TargetAllocation:
    def __init__(self, id, user_id, equities, bonds, cash):
        self.id = id
        self.user_id = user_id
        self.equities = equities
        self.bonds = bonds
        self.cash = cash

class Holding:
    def __init__(self, user_id, ticker, quantity, avg_cost):
        self.user_id = user_id
        self.ticker = ticker
        self.quantity = quantity
        self.avg_cost = avg_cost

class PriceHistory:
    def __init__(self, ticker, date, close):
        self.ticker = ticker
        self.date = date
        self.close = close
class LatestPrice:
    def __init__(self, ticker, price, as_of):
        self.ticker = ticker
        self.price = price
        self.as_of = as_of

class TargetAllocation:
    def __init__(self, user_id, ticker_or_class, weight):
        self.user_id = user_id
        self.ticker_or_class = ticker_or_class
        self.weight = weight

class RebalancePlan:
    def __init__(self, id, user_id, created_at, payload_json):
        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.payload_json = payload_json

class Recommendation:
    def __init__(self, id, user_id, created_at, payload_json):
        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.payload_json = payload_json