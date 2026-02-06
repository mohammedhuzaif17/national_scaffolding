from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ===========================
# ADMINS (PLAIN PASSWORD - NOT RECOMMENDED FOR PRODUCTION)
# ===========================

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    panel_type = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('username', 'panel_type', name='unique_username_panel'),
    )

    def set_password(self, password):
        """Store password as plain text (NOT RECOMMENDED for production)"""
        self.password_hash = password

    def check_password(self, password):
        """Check plain text password"""
        return self.password_hash == password


# ===========================
# ADMIN OTP
# ===========================

class AdminOTP(db.Model):
    __tablename__ = 'admin_otps'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(
        db.Integer,
        db.ForeignKey('admins.id', ondelete='CASCADE'),
        nullable=False
    )
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    rent_price = db.Column(db.Numeric(10, 2))
    deposit_amount = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(500))
    cuplock_type = db.Column(db.String(50))
    weight_per_unit = db.Column(db.Numeric(10, 2))
    customization_options = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ===========================
# CUPLOCK VERTICAL SIZE
# ===========================

class CuplockVerticalSize(db.Model):
    __tablename__ = 'cuplock_vertical_size'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )
    size_label = db.Column(db.String(50), nullable=False)
    buy_price = db.Column(db.Numeric(10, 2))
    rent_price = db.Column(db.Numeric(10, 2))
    deposit = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # NO RELATIONSHIP - Access cups via query when needed


# ===========================
# CUPLOCK VERTICAL CUPS
# ===========================

class CuplockVerticalCup(db.Model):
    __tablename__ = 'cuplock_vertical_cups'

    id = db.Column(db.Integer, primary_key=True)
    vertical_size_id = db.Column(
        db.Integer,
        db.ForeignKey('cuplock_vertical_size.id', ondelete='CASCADE'),
        nullable=False
    )
    cup_count = db.Column(db.Integer, nullable=False)
    cup_image_url = db.Column(db.String(255), nullable=True)
    weight_kg = db.Column(db.Float, default=0.0)
    buy_price = db.Column(db.Numeric(10, 2), default=0.0)
    rent_price = db.Column(db.Numeric(10, 2), default=0.0)
    deposit_amount = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    size = db.relationship('CuplockVerticalSize', backref='cups')


# ===========================
# CUPLOCK LEDGER SIZE
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
    buy_price = db.Column(db.Numeric(10, 2))
    rent_price = db.Column(db.Numeric(10, 2))
    deposit_amount = db.Column(db.Numeric(10, 2))
    weight_kg = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    total_price = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(50), default='pending_verification')
    transaction_id = db.Column(db.String(100))
    amount_paid = db.Column(db.Numeric(10, 2))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2))
    customization = db.Column(db.JSON)

    