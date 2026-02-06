from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ===========================
# USERS
# ===========================

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text)
    organization = db.Column(db.String(200))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship(
        'Order',
        backref='user',
        cascade='all, delete-orphan'
    )


# ===========================
# ADMINS (PLAIN PASSWORD)
# ===========================

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # plain text
    panel_type = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('username', 'panel_type', name='unique_username_panel'),
    )

    def check_password(self, password):
        return self.password_hash == password


# ===========================
# ADMIN OTP
# ===========================

class AdminOTP(db.Model):
    __tablename__ = 'admin_otps'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='CASCADE'), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('Admin', backref='otps')


# ===========================
# PRODUCTS
# ===========================

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    product_type = db.Column(db.String(50), nullable=False)
    customization_options = db.Column(db.JSON)
    rent_price = db.Column(db.Numeric(10, 2))
    deposit_amount = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(500))
    weight_per_unit = db.Column(db.Numeric(10, 2))
    cuplock_type = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vertical_sizes = db.relationship(
        'CuplockVerticalSize',
        backref='product',
        cascade='all, delete-orphan'
    )

    ledger_sizes = db.relationship(
        'CuplockLedgerSize',
        backref='product',
        cascade='all, delete-orphan'
    )

    order_items = db.relationship(
        'OrderItem',
        backref='product',
        cascade='all, delete-orphan'
    )


# ===========================
# CUPLOCK VERTICAL SIZES
# ===========================

class CuplockVerticalSize(db.Model):
    __tablename__ = 'cuplock_vertical_sizes'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    size_label = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Numeric(10, 2))
    buy_price = db.Column(db.Numeric(10, 2))
    rent_price = db.Column(db.Numeric(10, 2))
    deposit = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cups = db.relationship(
        'CuplockVerticalCup',
        back_populates='size',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.UniqueConstraint('product_id', 'size_label', name='unique_vertical_size'),
    )


# ===========================
# CUPLOCK LEDGER SIZES
# ===========================

class CuplockLedgerSize(db.Model):
    __tablename__ = 'cuplock_ledger_sizes'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    size_label = db.Column(db.String(50), nullable=False)
    weight_kg = db.Column(db.Numeric(10, 2))
    buy_price = db.Column(db.Numeric(10, 2))
    rent_price = db.Column(db.Numeric(10, 2))
    deposit_amount = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('product_id', 'size_label', name='unique_ledger_size'),
    )


# ===========================
# CUPLOCK VERTICAL CUPS
# ===========================

class CuplockVerticalCup(db.Model):
    __tablename__ = 'cuplock_vertical_cups'

    id = db.Column(db.Integer, primary_key=True)
    vertical_size_id = db.Column(
        db.Integer,
        db.ForeignKey('cuplock_vertical_sizes.id', ondelete='CASCADE'),
        nullable=False
    )

    cup_count = db.Column(db.Integer, nullable=False)
    cup_image_url = db.Column(db.String(255))
    weight_kg = db.Column(db.Numeric(10, 2))
    buy_price = db.Column(db.Numeric(10, 2))
    rent_price = db.Column(db.Numeric(10, 2))
    deposit_amount = db.Column(db.Numeric(10, 2))
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    size = db.relationship('CuplockVerticalSize', back_populates='cups')

    __table_args__ = (
        db.UniqueConstraint('vertical_size_id', 'cup_count', name='unique_vertical_cup'),
    )


# ===========================
# ORDERS
# ===========================

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending_verification')
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2))
    payment_time = db.Column(db.DateTime)

    items = db.relationship(
        'OrderItem',
        backref='order',
        cascade='all, delete-orphan'
    )


# ===========================
# ORDER ITEMS
# ===========================

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    customization = db.Column(db.JSON)

    @property
    def total_price(self):
        return self.quantity * self.price
