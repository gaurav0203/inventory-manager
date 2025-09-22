from flask_login import UserMixin
from extensions import db
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")  

    transactions = db.relationship("Transaction", backref="user", lazy=True)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)  # Stock Keeping Unit
    category = db.Column(db.String(50))
    purchase_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)

    transactions = db.relationship("Transaction", backref="product", lazy = True)

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), default = -1)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    change_type = db.Column(db.String(128), nullable=False)  # "in" or "out"
    quantity = db.Column(db.Integer, default = -1)
    purchase_price = db.Column(db.Float,default = -1.0)
    selling_price = db.Column(db.Float,default = -1.0)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
