from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer', nullable=False)  # 'customer' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reservations = db.relationship('Reservation', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'Hot Drinks', 'Cold Drinks', 'Snacks', 'Desserts'
    image_url = db.Column(db.String(200), nullable=True)  # URL or local file path
    is_available = db.Column(db.Boolean, default=True, nullable=False)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    slot_in = db.Column(db.String(10), nullable=False)
    slot_out = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Active', nullable=False)  # 'Active', 'Released'
    guests = db.Column(db.Integer, nullable=False)
    special_requests = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string representation of ordered items
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='Pending', nullable=False)  # 'Pending', 'Paid'
    order_status = db.Column(db.String(20), default='Pending', nullable=False)  # 'Pending', 'Preparing', 'Completed'
    transaction_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CafeLocation(db.Model):
    __tablename__ = 'cafe_locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    map_url = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
