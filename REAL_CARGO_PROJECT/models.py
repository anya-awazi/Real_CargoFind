from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False) # 'customer', 'driver', 'admin'
    
    # Driver specific fields
    vehicle_type = db.Column(db.String(50)) # 'bike', 'car', 'van', 'truck'
    vehicle_id = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False) # Admin approval
    
    # Location tracking
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    
    # Relationships
    deliveries_as_customer = db.relationship('Delivery', backref='customer', foreign_keys='Delivery.customer_id')
    deliveries_as_driver = db.relationship('Delivery', backref='driver', foreign_keys='Delivery.driver_id')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    wallet = db.relationship('Wallet', backref='user', uselist=False)
    payout_requests = db.relationship('PayoutRequest', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    pickup_location = db.Column(db.String(200), nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    
    dropoff_location = db.Column(db.String(200), nullable=False)
    dropoff_lat = db.Column(db.Float)
    dropoff_lng = db.Column(db.Float)
    
    goods_description = db.Column(db.Text, nullable=False)
    pickup_time = db.Column(db.DateTime, default=datetime.utcnow)
    special_instructions = db.Column(db.Text)
    weight = db.Column(db.Float)
    vehicle_type = db.Column(db.String(50)) # Type of vehicle required
    
    distance_km = db.Column(db.Float)
    estimated_time = db.Column(db.String(50))
    total_cost = db.Column(db.Float)
    
    status = db.Column(db.String(50), default='Pending') 
    # Statuses: Pending, Accepted, Picked Up, In Transit, Traffic Delay, Delivered, Cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Payment fields
    payment_status = db.Column(db.String(20), default='Unpaid') # Unpaid, Paid
    payment_method = db.Column(db.String(50)) # MoMo, Orange, Cash
    
    # Review
    rating = db.Column(db.Integer)
    feedback = db.Column(db.Text)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(100))

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    total_earned = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PayoutRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False) # MoMo, Orange
    status = db.Column(db.String(20), default='Pending') # Pending, Processed, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

