from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from models import CuplockVerticalCup
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from models import db, User, Admin, Product, Order, OrderItem
import os
import qrcode
import io
import base64
from utils import get_image_url
import random
from flask import abort
from werkzeug.security import generate_password_hash, check_password_hash

# from cuplock_routes import get_image_url
from flask import render_template, request
from models import Product, CuplockLedgerSize


# FIX: Import both datetime class and timedelta class
from datetime import datetime, timedelta 
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json
import uuid
from PIL import Image
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import text
from models import Product
# Import Cuplock blueprint
from cuplock_routes import cuplock_bp
from datetime import timezone
from zoneinfo import ZoneInfo
from werkzeug.utils import secure_filename
import uuid
import os

# Load environment variables from .env file
load_dotenv()

def ensure_columns_exist():
    """Add nullable columns if PostgreSQL schema is missing them."""
    with db.engine.connect() as conn:
        # Add is_active to products table
        conn.execute(text("""
            DO $$             BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='products' AND column_name='is_active'
                ) THEN
                    ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                    RAISE NOTICE 'Added is_active column to products table';
                END IF;
            END $$;
        """))
        conn.commit()
        
        # Add cuplock_type to products table
        conn.execute(text("""
            DO $$             BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='products' AND column_name='cuplock_type'
                ) THEN
                    ALTER TABLE products ADD COLUMN cuplock_type VARCHAR(50);
                    RAISE NOTICE 'Added cuplock_type column to products table';
                END IF;
            END $$;
        """))
        conn.commit()

        # Add is_active to cuplock_ledger_sizes table
        conn.execute(text("""
            DO $$             BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cuplock_ledger_sizes' AND column_name='is_active'
                ) THEN
                    ALTER TABLE cuplock_ledger_sizes ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                    RAISE NOTICE 'Added is_active column to cuplock_ledger_sizes table';
                END IF;
            END $$;
        """))
        conn.commit()

        # Add columns to cuplock_vertical_sizes table
        conn.execute(text("""
            DO $$             BEGIN
                -- weight column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cuplock_vertical_sizes' AND column_name='weight'
                ) THEN
                    ALTER TABLE cuplock_vertical_sizes ADD COLUMN weight NUMERIC(10,2);
                    RAISE NOTICE 'Added weight column to cuplock_vertical_sizes table';
                END IF;

                -- buy_price column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cuplock_vertical_sizes' AND column_name='buy_price'
                ) THEN
                    ALTER TABLE cuplock_vertical_sizes ADD COLUMN buy_price NUMERIC(10,2);
                    RAISE NOTICE 'Added buy_price column to cuplock_vertical_sizes table';
                END IF;

                -- rent_price column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cuplock_vertical_sizes' AND column_name='rent_price'
                ) THEN
                    ALTER TABLE cuplock_vertical_sizes ADD COLUMN rent_price NUMERIC(10,2);
                    RAISE NOTICE 'Added rent_price column to cuplock_vertical_sizes table';
                END IF;

                -- deposit column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cuplock_vertical_sizes' AND column_name='deposit'
                ) THEN
                    ALTER TABLE cuplock_vertical_sizes ADD COLUMN deposit NUMERIC(10,2);
                    RAISE NOTICE 'Added deposit column to cuplock_vertical_sizes table';
                END IF;

                -- is_active column
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cuplock_vertical_sizes' AND column_name='is_active'
                ) THEN
                    ALTER TABLE cuplock_vertical_sizes ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                    RAISE NOTICE 'Added is_active column to cuplock_vertical_sizes table';
                END IF;
            END $$;
        """))
        conn.commit()

def indian_format(number):
    x = str(int(number))
    if len(x) <= 3:
        return x
    last3 = x[-3:]
    rest = x[:-3]
    parts = []
    while len(rest) > 2:
        parts.append(rest[-2:])
        rest = rest[:-2]
    parts.append(rest)
    parts.reverse()
    return ",".join(parts) + "," + last3

app = Flask(__name__)

# Configure basic logging for debugging
import logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Set secret key and session configuration BEFORE any session operations
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Configure session properly to avoid cookie errors
app.config['SESSION_COOKIE_NAME'] = 'national_scaffolding_session'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) # FIX APPLIED

db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD', 'postgres')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'national_scaffolding')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff', 'ico', 'jfif', 'pjpeg', 'pjp', 'avif', 'heic', 'heif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))

mail = Mail(app)

# FIX: Initialize SQLAlchemy with Flask app
db.init_app(app)

# Register Jinja filters
app.jinja_env.filters['indian'] = indian_format


IST = ZoneInfo("Asia/Kolkata")

def utc_to_ist(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(filepath):
    """Validate a single image file and return diagnostic info.
    Returns a dict with keys: exists, readable, valid, format, size_bytes, dimensions, error
    """
    diagnostic = {
        'filepath': filepath,
        'exists': False,
        'readable': False,
        'valid': False,
        'format': None,
        'size_bytes': 0,
        'dimensions': None,
        'error': None
    }
    
    if not os.path.exists(filepath):
        diagnostic['error'] = 'File does not exist on disk'
        return diagnostic
    
    diagnostic['exists'] = True
    
    try:
        size = os.path.getsize(filepath)
        diagnostic['size_bytes'] = size
        diagnostic['readable'] = True
    except Exception as e:
        diagnostic['error'] = f'Cannot read file size: {str(e)}'
        return diagnostic
    
    try:
        with Image.open(filepath) as im:
            im.verify()
            diagnostic['valid'] = True
            diagnostic['format'] = im.format
    except Exception as e:
        diagnostic['valid'] = False
        diagnostic['error'] = f'Image validation failed: {str(e)}'
        return diagnostic
    
    try:
        with Image.open(filepath) as im:
            diagnostic['dimensions'] = f"{im.width}x{im.height}"
    except Exception as e:
        diagnostic['dimensions'] = 'Unable to read'
    
    return diagnostic


# ============================================================================
# ADMIN OTP FUNCTIONS
# ============================================================================

def send_admin_otp(admin_id):
    """Send OTP to admin email"""
    from models import AdminOTP
    
    otp = random.randint(100000, 999999)
    
    # Delete old OTPs for this admin
    AdminOTP.query.filter_by(admin_id=admin_id).delete()
    
    # Create new OTP entry
    otp_entry = AdminOTP(
        admin_id=admin_id,
        otp_hash=generate_password_hash(str(otp)),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        attempts=0
    )
    db.session.add(otp_entry)
    db.session.commit()
    
    # Send email
    try:
        admin_email = os.getenv("ADMIN_OTP_EMAIL")
        if not admin_email:
            app.logger.error("ADMIN_OTP_EMAIL not configured in .env")
            raise ValueError("Admin email not configured")
        
        msg = Message(
            subject="Admin Login OTP - National Scaffolding",
            recipients=[admin_email],
            body=f"Your OTP for admin login is: {otp}\n\nThis OTP is valid for 5 minutes.\n\nIf you did not request this, please ignore this email."
        )
        mail.send(msg)
        app.logger.info(f"OTP sent successfully to {admin_email}")
    except Exception as e:
        app.logger.error(f"Failed to send OTP email: {e}")
        raise


# ============================================================================
# ADMIN LOGIN WITH OTP
# ============================================================================
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            identifier = request.form.get('identifier')
            password = request.form.get('password')
            panel_type = request.form.get('panel_type')
            
            app.logger.info(f"Admin login attempt: {identifier}, panel: {panel_type}")
            
            if not panel_type:
                flash('Please select an admin panel', 'error')
                return render_template('admin_login.html')
            
            # Find admin
            admin = Admin.query.filter_by(
                username=identifier,
                panel_type=panel_type
            ).first()
            
            if not admin:
                app.logger.warning(f"Admin not found: {identifier}")
                flash('Invalid admin credentials or wrong panel selected', 'error')
                return render_template('admin_login.html')
            
            # Verify password
            if not admin.check_password(password):
                app.logger.warning(f"Wrong password for admin: {identifier}")
                flash('Invalid admin credentials or wrong panel selected', 'error')
                return render_template('admin_login.html')
            
            app.logger.info(f"Password verified for {identifier}, sending OTP...")
            
            # Password correct → Generate and send OTP
            try:
                send_admin_otp(admin.id)
                app.logger.info(f"OTP sent successfully to {os.getenv('ADMIN_OTP_EMAIL')}")
            except Exception as e:
                flash('Failed to send OTP. Please contact support.', 'error')
                app.logger.error(f"OTP send failed: {e}", exc_info=True)
                return render_template('admin_login.html')
            
            # Clear session and set OTP pending state
            session.clear()
            session['otp_admin_id'] = admin.id
            session['otp_verified'] = False
            session['panel_type'] = admin.panel_type
            session.permanent = True
            
            flash(f'OTP has been sent to {os.getenv("ADMIN_OTP_EMAIL")}', 'success')
            app.logger.info(f"Redirecting to OTP page for admin {identifier}")
            return redirect(url_for('admin_otp'))
            
        except Exception as e:
            app.logger.error(f"Admin login error: {e}", exc_info=True)
            flash('Login failed. Please try again.', 'error')
            return render_template('admin_login.html')
    
    return render_template('admin_login.html')


@app.route('/admin_otp', methods=['GET', 'POST'])
def admin_otp():
    """Handle OTP verification"""
    from models import AdminOTP
    
    admin_id = session.get('otp_admin_id')
    if not admin_id:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('admin_login'))
    
    admin = Admin.query.get(admin_id)
    if not admin:
        flash('Invalid session', 'error')
        return redirect(url_for('admin_login'))
    
    otp_entry = AdminOTP.query.filter_by(admin_id=admin_id).first()
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        
        # Check if OTP entry exists and is not expired
        if not otp_entry or otp_entry.expires_at < datetime.utcnow():
            if otp_entry:
                db.session.delete(otp_entry)
                db.session.commit()
            flash('OTP expired. Please login again.', 'error')
            return redirect(url_for('admin_login'))
        
        # Check attempts
        if otp_entry.attempts >= 3:
            db.session.delete(otp_entry)
            db.session.commit()
            flash('Too many failed attempts. Please login again.', 'error')
            return redirect(url_for('admin_login'))
        
        # Verify OTP
        if not check_password_hash(otp_entry.otp_hash, otp):
            otp_entry.attempts += 1
            db.session.commit()
            remaining = 3 - otp_entry.attempts
            flash(f'Invalid OTP. {remaining} attempts remaining.', 'error')
            return render_template('admin_otp.html', admin=admin)
        
        # OTP SUCCESS
        login_user(admin)
        session['user_type'] = 'admin'
        session['otp_verified'] = True
        session['panel_type'] = admin.panel_type
        session.permanent = True
        
        # Delete used OTP
        db.session.delete(otp_entry)
        db.session.commit()
        
        app.logger.info(f"Admin {admin.username} logged in successfully with OTP")
        
        # Redirect to appropriate panel
        if admin.panel_type == 'scaffolding':
            return redirect(url_for('admin_scaffoldings'))
        else:
            return redirect(url_for('admin_fabrication'))
    
    # Calculate time remaining
    time_remaining = None
    if otp_entry:
        time_remaining = int((otp_entry.expires_at - datetime.utcnow()).total_seconds())
        if time_remaining < 0:
            time_remaining = 0
    
    return render_template('admin_otp.html', admin=admin, time_remaining=time_remaining)


@app.route('/admin_resend_otp', methods=['POST'])
def admin_resend_otp():
    """Resend OTP to admin"""
    admin_id = session.get('otp_admin_id')
    if not admin_id:
        return jsonify({'success': False, 'message': 'Session expired'}), 401
    
    try:
        send_admin_otp(admin_id)
        return jsonify({'success': True, 'message': 'OTP resent successfully'})
    except Exception as e:
        app.logger.error(f"OTP resend failed: {e}")
        return jsonify({'success': False, 'message': 'Failed to resend OTP'}), 500


def safe_float(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() == 'none':
            return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def validate_price(price_value, field_name='Price'):
    """
    Validate that a price is a valid positive number
    Returns: (is_valid, error_message)
    """
    if price_value is None or price_value == '':
        return False, f"{field_name} is required"
    
    try:
        price_float = float(price_value)
        if price_float <= 0:
            return False, f"{field_name} must be greater than 0"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"

# Updated calculate_price function to handle Cuplock
# ============================================================================
# COMPLETE calculate_price FUNCTION WITH CUPLOCK SUPPORT
# Replace your existing calculate_price function (around line 250) with this entire function
# ============================================================================
# ... (keep all your code from the top of the file up to the calculate_price function) ...

# ============================================================================
# CORRECTED calculate_price FUNCTION
def calculate_price(product, customization=None):
    """Calculate price for a product with customization"""
    try:
        if customization is None:
            customization = {}
            
        # Default price
        base_price = float(product.price or 0)
        
        # For fabrication products
        if product.product_type == 'fabrication':
            return {
                'price': base_price,
                'deposit': 0
            }
        
        # ✅ FOR VERTICAL CUPLOCK
        if product.category == 'cuplock' and product.cuplock_type == 'vertical':
            purchase_type = customization.get('purchase_type', 'buy')
            
            if purchase_type == 'buy':
                # Buy = size buy price + cup price
                size_label = customization.get('size')
                if size_label:
                    from models import CuplockVerticalSize
                    size = CuplockVerticalSize.query.filter_by(
                        product_id=product.id,
                        size_label=size_label,
                        is_active=True
                    ).first()
                    
                    if size:
                        base_price = float(size.buy_price or 0)
                
                cup_price = float(customization.get('cup_price', 0))
                return {
                    'price': base_price + cup_price,
                    'deposit': 0
                }
            else:
                # Rent = rent price from size + deposit
                size_label = customization.get('size')
                if size_label:
                    from models import CuplockVerticalSize
                    size = CuplockVerticalSize.query.filter_by(
                        product_id=product.id,
                        size_label=size_label,
                        is_active=True
                    ).first()
                    
                    if size:
                        return {
                            'price': float(size.rent_price or 0),
                            'deposit': float(size.deposit or 0)
                        }
                
                return {'price': 0, 'deposit': 0}
        
        # ✅ FIXED FOR LEDGER CUPLOCK
        if product.category == 'cuplock' and product.cuplock_type == 'ledger':
            purchase_type = customization.get('purchase_type', 'buy')
            
            # Get size_id - convert to int if string
            size_id = customization.get('size_id')
            if size_id:
                try:
                    size_id = int(size_id)
                except (ValueError, TypeError):
                    size_id = None
            
            if size_id:
                from models import CuplockLedgerSize
                size = CuplockLedgerSize.query.filter_by(
                    id=size_id,
                    is_active=True
                ).first()
                
                if size:
                    if purchase_type == 'buy':
                        return {
                            'price': float(size.buy_price or 0),
                            'deposit': 0
                        }
                    else:  # rent
                        return {
                            'price': float(size.rent_price or 0),
                            'deposit': float(size.deposit_amount or 0)
                        }
            
            # Fallback to product-level prices
            if purchase_type == 'buy':
                return {
                    'price': float(product.price or 0),
                    'deposit': 0
                }
            else:
                return {
                    'price': float(product.rent_price or 0),
                    'deposit': float(product.deposit_amount or 0)
                }
        
        # For aluminium
        if product.category == 'aluminium':
            purchase_type = customization.get('purchase_type', 'buy')
            unit_price = product.rent_price if purchase_type == 'rent' else base_price
            return {
                'price': unit_price,
                'deposit': product.deposit_amount if purchase_type == 'rent' else 0
            }
        
        # Default case for other products
        return {
            'price': base_price,
            'deposit': product.deposit_amount or 0
        }
        
    except Exception as e:
        app.logger.error(f"Price calculation error: {e}")
        return {
            'price': 0,
            'deposit': 0
        }

# ... (keep the rest of your app.py code, but make sure to REMOVE the HTML block at the very end) ...

# The following HTML block was at the end of your Python file and MUST BE DELETED:
#
# {% extends "base.html" %}
#
# {% block title %}National Scaffolding - Fabrications{% endblock %}
#
# ... (rest of the HTML code) ...
#
# COMPLETE product_detail ROUTE WITH CUPLOCK REDIRECT
# Replace your existing @app.route('/product/<int:product_id>') (around line 350) with this
# ============================================================================

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        # Ensure prior failures don't poison this request
        if db.session.is_active:
            db.session.rollback()

        product = Product.query.get_or_404(product_id)

        # ========== FABRICATION REDIRECT LOGIC (NEW) ==========
        if product.product_type == 'fabrication':
            return redirect(url_for('fabrication_detail', product_id=product_id))
            
        # ========== CUPLOCK REDIRECT LOGIC ==========
        if product.category == 'cuplock':
            # Redirect to specialized Cuplock product pages
            if product.cuplock_type == 'vertical':
                return redirect(url_for('cuplock.vertical_product_page', product_id=product_id))
            elif product.cuplock_type == 'ledger':
                return redirect(url_for('cuplock.ledger_product_page', product_id=product_id))
            
            # Fallback: If cuplock_type is not set properly, try to load sizes
            try:
                cuplock_prices = []
                if product.cuplock_type == 'vertical':
                    from models import CuplockVerticalSize
                    sizes = CuplockVerticalSize.query.filter_by(
                        product_id=product_id,
                        is_active=True
                    ).all()
                    
                    for size in sizes:
                        cuplock_prices.append({
                            'size_label': size.size_label,
                            'buy_price': float(size.buy_price or 0),
                            'rent_price': float(size.rent_price or 0),
                            'deposit': float(size.deposit or 0)
                        })
                        
                elif product.cuplock_type == 'ledger':
                    from models import CuplockLedgerSize
                    try:
                        sizes = CuplockLedgerSize.query.filter_by(
                            product_id=product_id,
                            is_active=True
                        ).all()
                    except Exception:
                        # Fallback for legacy tables missing is_active
                        sizes = CuplockLedgerSize.query.filter_by(product_id=product_id).all()
                    
                    for size in sizes:
                        cuplock_prices.append({
                            'size_label': size.size_label,
                            'buy_price': float(size.buy_price or 0),
                            'rent_price': float(size.rent_price or 0),
                            'deposit': float(size.deposit_amount or 0)
                        })

                # Set the first price as default
                if cuplock_prices:
                    product.price = cuplock_prices[0]['buy_price']
                    product.rent_price = cuplock_prices[0]['rent_price']
                    product.deposit_amount = cuplock_prices[0]['deposit']
                else:
                    product.price = 0
                    product.rent_price = 0
                    product.deposit_amount = 0
            except Exception as size_error:
                app.logger.error(f"Error loading Cuplock sizes: {size_error}")
                product.price = 0
                product.rent_price = 0
                product.deposit_amount = 0

        # ========== EXISTING LOGIC FOR OTHER PRODUCTS ==========
        return render_template('product_detail.html', product=product, cuplock_prices=cuplock_prices if product.category == 'cuplock' else [])

    except Exception as e:
        if db.session.is_active:
            db.session.rollback()
        app.logger.error(f"Error in product_detail: {e}", exc_info=True)
        flash('Error loading product details. Please try again.', 'error')
        return render_template('product_detail.html', product=None)
        
@app.before_request
def before_request():
    """Ensure each request starts with a clean session"""
    try:
        if db.session.is_active:
            db.session.rollback()
    except SQLAlchemyError:
        app.logger.warning("Session rollback failed before request; removing session")
        db.session.remove()

@app.teardown_request
def teardown_request(exception=None):
    """Clean up the database session after each request"""
    try:
        if exception and db.session.is_active:
            db.session.rollback()
    finally:
        db.session.remove()

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Remove the session at the end of the request or when the app shuts down"""
    db.session.remove()

@app.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    """Handle database errors by rolling back the session"""
    db.session.rollback()
    app.logger.error(f"Database error: {str(error)}")
    return "A database error occurred. Please try again later.", 500

# Register Cuplock blueprint
app.register_blueprint(cuplock_bp)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
        # Check if user_type is in session
        if 'user_type' in session and session.get('user_type') == 'admin':
            return Admin.query.get(user_id)
        return User.query.get(user_id)
    except (ValueError, TypeError):
        return None

# Create app context and initialize database
with app.app_context():
    try:
        ensure_columns_exist()
    except Exception as e:
        app.logger.error(f"Schema sync error: {e}")

    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"Database creation error: {e}")

def create_default_admins():
    """
    Create admin accounts ONLY if credentials are provided in .env file
    """
    with app.app_context():
        try:
            # Get admin credentials from environment
            scaffolding_user = os.environ.get('SCAFFOLDING_ADMIN_USER')
            scaffolding_pass = os.environ.get('SCAFFOLDING_ADMIN_PASS')
            fabrication_user = os.environ.get('FABRICATION_ADMIN_USER')
            fabrication_pass = os.environ.get('FABRICATION_ADMIN_PASS')
            
            app.logger.info(f"=== Creating Admins ===")
            app.logger.info(f"Scaffolding admin user: {scaffolding_user}")
            app.logger.info(f"Fabrication admin user: {fabrication_user}")
            
            # Create scaffolding admin if credentials exist
            if scaffolding_user and scaffolding_pass:
                admin_scaffolding = Admin.query.filter_by(username=scaffolding_user).first()
                if not admin_scaffolding:
                    admin_scaffolding = Admin(
                        username=scaffolding_user,
                        panel_type='scaffolding'
                    )
                    admin_scaffolding.set_password(scaffolding_pass)
                    db.session.add(admin_scaffolding)
                    app.logger.info(f"✅ Created scaffolding admin: {scaffolding_user}")
                else:
                    app.logger.info(f"ℹ️ Scaffolding admin already exists: {scaffolding_user}")
            else:
                app.logger.warning("⚠️ Scaffolding admin credentials not found in .env")
            
            # Create fabrication admin if credentials exist
            if fabrication_user and fabrication_pass:
                admin_fabrication = Admin.query.filter_by(username=fabrication_user).first()
                if not admin_fabrication:
                    admin_fabrication = Admin(
                        username=fabrication_user,
                        panel_type='fabrication'
                    )
                    admin_fabrication.set_password(fabrication_pass)
                    db.session.add(admin_fabrication)
                    app.logger.info(f"✅ Created fabrication admin: {fabrication_user}")
                else:
                    app.logger.info(f"ℹ️ Fabrication admin already exists: {fabrication_user}")
            else:
                app.logger.warning("⚠️ Fabrication admin credentials not found in .env")
            
            db.session.commit()
            app.logger.info("✅ Admin creation process completed")
            
        except Exception as e:
            app.logger.error(f"❌ Error creating admins: {e}")
            db.session.rollback()

# Add route to handle Chrome DevTools requests
@app.route('/.well-known/<path:path>')
def well_known(path):
    """Handle Chrome DevTools and other well-known requests"""
    if path == 'appspecific/com.chrome.devtools.json':
        # Return empty JSON for Chrome DevTools
        return jsonify({})
    # For other well-known paths, return 404
    return "", 404

# Welcome popup and home page routes
@app.route('/')
def index():
    """Render home page with welcome popup"""
    # Check if user is authenticated
    is_authenticated = current_user.is_authenticated
    
    # Get user type if authenticated
    user_type = session.get('user_type') if is_authenticated else None
    
    return render_template(
        'home.html', 
        current_user=current_user,
        is_authenticated=is_authenticated,
        user_type=user_type
    )

@app.route('/home')
def home():
    """Redirect to index to show welcome popup"""
    return redirect(url_for('index'))
# ... keep the rest of your app.py code unchanged ...
    # try:
    #     from cuplock_routes import get_image_url
        
    #     category = request.args.get('category', 'all')

    #     if category == 'all':
    #         products = Product.query.filter(
    #             Product.is_active == True
    #         ).all()
    #     else:
    #         category_map = {
    #             'aluminium': 'aluminium',
    #             'h-frames': 'h-frames',
    #             'cuplock': 'cuplock',
    #             'accessories': 'accessories'
    #         }

    #         db_category = category_map.get(category.lower(), category)

    #         products = Product.query.filter(
    #             Product.category == db_category,
    #             Product.is_active == True
    #         ).all()

    #     for product in products:
    #         product.display_image_url = get_image_url(product.image_url)

    #     return render_template(
    #         'national_scaffoldings.html',
    #         products=products,
    #         category=category
    #     )

    # except Exception as e:
    #     app.logger.error(f"Index route error: {e}", exc_info=True)
    #     return render_template(
    #         'national_scaffoldings.html',
    #         products=[],
    #         category='all'
    #     )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            full_name = request.form.get('full_name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            organization = request.form.get('organization')
            password = request.form.get('password')
            
            if not phone or not phone.isdigit() or len(phone) != 10:
                flash('Phone number must be exactly 10 digits', 'error')
                return redirect(url_for('register'))
            
            if phone[0] not in ['6', '7', '8', '9']:
                flash('Phone number must start with 6, 7, 8, or 9', 'error')
                return redirect(url_for('register'))
            
            phone = '+91' + phone
            
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('register'))
            
            if User.query.filter_by(phone=phone).first():
                flash('Phone number already registered', 'error')
                return redirect(url_for('register'))
            
            user = User(username=username, full_name=full_name, phone=phone, email=email, address=address, organization=organization)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Registration error: {e}")
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            identifier = request.form.get('identifier')
            password = request.form.get('password')

            # 🔹 1. CHECK ADMIN FIRST
            admin = Admin.query.filter_by(username=identifier).first()
            if admin and admin.check_password(password):
                login_user(admin)
                session['user_type'] = 'admin'
                session['panel_type'] = admin.panel_type
                session.permanent = True

                if admin.panel_type == 'scaffolding':
                    return redirect(url_for('admin_scaffoldings'))
                else:
                    return redirect(url_for('admin_fabrication'))

            # 🔹 2. CHECK NORMAL USER
            user = User.query.filter(
                (User.username == identifier) |
                (User.email == identifier) |
                (User.phone == identifier)
            ).first()

            if user and user.check_password(password):
                login_user(user)
                session['user_type'] = 'user'
                session['cart'] = session.get('cart', [])
                session.permanent = True
                return redirect(url_for('dashboard'))

            # 🔴 INVALID
            flash('Invalid credentials', 'error')

        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')

    return render_template('login.html')

  
# =================================================================
# PASTE THE FABRICATION_DETAIL FUNCTION HERE (at the top level)
# =================================================================
# =================================================================
# FABRICATION ROUTES
# =================================================================


@app.route('/logout')
@login_required
def logout():
    try:
        # Clear session completely
        session.clear()
        logout_user()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Logout error: {e}")
        return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Check if user is admin and redirect appropriately
        if session.get('user_type') == 'admin':
            panel_type = session.get('panel_type')
            if panel_type == 'scaffolding':
                return redirect(url_for('admin_scaffoldings'))
            elif panel_type == 'fabrication':
                return redirect(url_for('admin_fabrication'))
            # If panel_type is not set, default to scaffolding admin
            else:
                session['panel_type'] = 'scaffolding'
                return redirect(url_for('admin_scaffoldings'))
        
        # Regular user dashboard
        return render_template('dashboard.html')
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        return redirect(url_for('index'))
    
@app.route('/switch_admin_panel/<panel_type>')
@login_required
def switch_admin_panel(panel_type):
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        if panel_type in ['scaffolding', 'fabrication']:
            session['panel_type'] = panel_type
            
            if panel_type == 'scaffolding':
                return redirect(url_for('admin_scaffoldings'))
            else:
                return redirect(url_for('admin_fabrication'))
        else:
            flash('Invalid panel type', 'error')
            return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Switch admin panel error: {e}")
        return redirect(url_for('dashboard'))
    
@app.route('/cuplock-shop')
def cuplock_shop():
    """Display all cuplock products - both vertical and ledger"""
    try:
        # from cuplock_routes import get_image_url
        
        # Get vertical products
        vertical_products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        # Get ledger products
        ledger_products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='ledger',
            is_active=True
        ).all()
        
        # Debug logging
        app.logger.info(f"Cuplock Shop - Vertical: {len(vertical_products)}, Ledger: {len(ledger_products)}")
        
        # Add display_image_url to each product for template rendering
        for product in vertical_products:
            product.display_image_url = get_image_url(product.image_url)
        
        for product in ledger_products:
            product.display_image_url = get_image_url(product.image_url)
            app.logger.info(f"Ledger Product: {product.name}, Image: {product.display_image_url}")
        
        return render_template('cuplock_shop.html',
                             vertical_products=vertical_products,
                             ledger_products=ledger_products)
    except Exception as e:
        app.logger.error(f"Cuplock shop error: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return render_template('cuplock_shop.html', vertical_products=[], ledger_products=[])
        
# @app.route('/national_scaffoldings')
# def national_scaffoldings():
#     category = request.args.get('category', 'all')

#     allowed_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories']

#     products = Product.query.filter(
#         Product.is_active == True,
#         Product.category.in_(allowed_categories)
#     ).order_by(Product.id.desc()).all()

#     # Category filter
#     if category != 'all':
#         products = [p for p in products if p.category == category]

#     # IMAGE HANDLING
#     for product in products:
#         # Default image
#         product.display_image_url = 'images/no-image.png'

#         # CUPLOCK VERTICAL → image from size table
#         if product.category == 'cuplock' and product.cuplock_type == 'vertical':
#             try:
#                 from models import CuplockVerticalSize

#                 size = CuplockVerticalSize.query.filter_by(
#                     product_id=product.id,
#                     is_active=True
#                 ).first()

#                 if size:
#                     # 🔴 CHANGE THIS IF YOUR COLUMN NAME IS DIFFERENT
#                     if hasattr(size, 'image_url') and size.image_url:
#                         product.display_image_url = size.image_url

#             except Exception as e:
#                 print(f"❌ Vertical image error (product {product.id}):", e)

#         # ALL OTHER PRODUCTS
#         elif product.image_url:
#             images = [i.strip() for i in product.image_url.split(',') if i.strip()]
#             if images:
#                 product.display_image_url = images[0]

#     return render_template(
#         'national_scaffoldings.html',
#         products=products,
#         selected_category=category
#     )
# @app.route('/national_scaffoldings')
# def national_scaffoldings():
#     category = request.args.get('category', 'all')

#     allowed_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories']

#     products = Product.query.filter(
#         Product.is_active == True,
#         Product.category.in_(allowed_categories)
#     ).order_by(Product.id.desc()).all()

#     if category != 'all':
#         products = [p for p in products if p.category == category]

#     # ================= IMAGE + PRICE HANDLING =================
#     for product in products:

#         # ---------- DEFAULTS ----------
#         product.display_image_url = 'images/no-image.png'
#         product.display_price = 0   # 🔥 THIS IS IMPORTANT

#         # ---------- CUPLOCK ----------
#         if product.category == 'cuplock':

#             # ===== LEDGER =====
#             if product.cuplock_type == 'ledger':
#                 from models import CuplockLedgerSize

#                 size = CuplockLedgerSize.query.filter_by(
#                     product_id=product.id,
#                     is_active=True
#                 ).order_by(CuplockLedgerSize.buy_price).first()

#                 if size:
#                     product.display_price = float(size.buy_price or 0)

#                     if hasattr(size, 'image_url') and size.image_url:
#                         product.display_image_url = size.image_url

#             # ===== VERTICAL =====
#             elif product.cuplock_type == 'vertical':
#                 from models import CuplockVerticalSize

#                 size = CuplockVerticalSize.query.filter_by(
#                     product_id=product.id,
#                     is_active=True
#                 ).order_by(CuplockVerticalSize.buy_price).first()

#                 if size:
#                     product.display_price = float(size.buy_price or 0)

#                     if hasattr(size, 'image_url') and size.image_url:
#                         product.display_image_url = size.image_url

#         # ---------- NON-CUPLOCK ----------
#         else:
#             product.display_price = float(product.price or 0)

#             if product.image_url:
#                 images = [i.strip() for i in product.image_url.split(',') if i.strip()]
#                 if images:
#                     product.display_image_url = images[0]

#     return render_template(
#         'national_scaffoldings.html',
#         products=products,
#         selected_category=category
#     )
@app.route('/national_scaffoldings')
def national_scaffoldings():
    category = request.args.get('category', 'all')

    # Define scaffolding categories
    scaffolding_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories']

    query = Product.query.filter(
        Product.is_active == True,
        Product.category.in_(scaffolding_categories)  # Only scaffolding categories
    )

    if category != 'all':
        query = query.filter(Product.category == category)

    products = query.all()

    for product in products:
        product.display_image_url = get_image_url(product.image_url)

        # 🔹 DEFAULT PRICE
        product.display_price = product.price if product.price else 0

        # 🔥 LEDGER PRICE (MIN BUY PRICE)
        if product.category == 'cuplock' and product.cuplock_type == 'ledger':
            min_size = CuplockLedgerSize.query.filter_by(
                product_id=product.id,
                is_active=True
            ).order_by(CuplockLedgerSize.buy_price.asc()).first()

            product.display_price = min_size.buy_price if min_size else 0

    return render_template(
        'national_scaffoldings.html',
        products=products
    )



@app.route('/fix_old_fabrication_products')
def fix_old_fabrication_products():
    try:
        # Find products that might be fabrication products
        # Update these patterns based on what you find in debug_all_products
        possible_patterns = ['steel', 'aluminium', 'custom', 'parts']
        
        updated_count = 0
        for pattern in possible_patterns:
            products = Product.query.filter(
                Product.category == pattern,
                Product.is_active == True
            ).all()
            
            for product in products:
                product.category = 'fabrication'
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} products to category=fabrication'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)})
@app.route('/fabrication/<int:product_id>')
def fabrication_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)

        # ✅ FIX: Allow valid fabrication sub-categories (steel, custom, parts, etc.)
        valid_categories = ['steel', 'custom', 'parts', 'fabrication', 'fabrications']
        
        if product.category not in valid_categories or not product.is_active:
            flash('This product is not available.', 'warning')
            return redirect(url_for('fabrications'))

        product.price = float(product.price or 0)

        return render_template(
            'fabrication_detail.html',
            product=product
        )

    except Exception as e:
        print("🔥 FABRICATION DETAIL ERROR:", repr(e))
        flash('Error loading product details. Please try again.', 'error')
        return redirect(url_for('fabrications'))
@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    try:
        if session.get('user_type') == 'admin':
            return jsonify({
                'success': False,
                'message': 'Admins cannot purchase items'
            }), 403

        data = request.get_json() if request.is_json else request.form.to_dict()

        # Handle stringified JSON from forms
        if 'customization' in data and isinstance(data['customization'], str):
            try:
                data['customization'] = json.loads(data['customization'])
            except json.JSONDecodeError:
                data['customization'] = {}

        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        customization = data.get('customization', {})

        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'Invalid quantity'
            }), 400

        product = Product.query.get_or_404(product_id)

        app.logger.info(f"Adding to cart: Product={product.name}, Customization={customization}")

        # Calculate price using the updated calculate_price function
        price_data = calculate_price(product, customization)

        if not price_data or float(price_data.get('price', 0)) <= 0:
            return jsonify({
                'success': False,
                'message': 'Unable to calculate price'
            }), 400

        unit_price = float(price_data['price'])
        deposit = float(price_data.get('deposit', 0))

        # Create cart item with all necessary information
        cart_item = {
            'product_id': product.id,
            'product_name': product.name,
            'category': product.category,
            'product_type': product.product_type,
            'quantity': quantity,
            'unit_price': unit_price,
            'item_total': unit_price * quantity,
            'deposit': deposit,
            'item_deposit': deposit * quantity,
            'customization': customization,
            'image_url': product.image_url
        }

        # Get existing cart or create new one
        cart = session.get('cart', [])
        cart.append(cart_item)
        session['cart'] = cart
        session.modified = True

        app.logger.info(
            f"[CART] User {current_user.id} added {product.name} | "
            f"₹{unit_price} x {quantity} | Customization: {customization}"
        )

        return jsonify({
            'success': True,
            'cart_count': len(cart),
            'message': 'Product added to cart',
            'item': {
                'name': product.name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total': unit_price * quantity,
                'deposit': deposit * quantity
            }
        })

    except Exception as e:
        app.logger.error(f"Add to cart error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Error adding to cart'
        }), 500
        
@app.route('/cart')
@login_required
def cart():
    try:
        if session.get('user_type') == 'admin':
            flash('Admins cannot make purchases', 'warning')
            return redirect(url_for('admin_scaffoldings'))

        cart_items = session.get('cart', [])
        enriched_cart = []

        total_items_price = 0.0
        total_deposit = 0.0

        for item in cart_items:
            product = Product.query.get(item['product_id'])
            if not product:
                continue

            unit_price = float(item.get('unit_price', 0))
            item_total = float(item.get('item_total', 0))
            deposit = float(item.get('deposit', 0))
            item_deposit = float(item.get('item_deposit', 0))
            quantity = item.get('quantity', 1)
            customization = item.get('customization', {})

            total_items_price += item_total
            total_deposit += item_deposit

            enriched_cart.append({
                'product_name': product.name,
                'quantity': quantity,
                'unit_price': unit_price,
                'item_total': item_total,
                'deposit': deposit,
                'item_deposit': item_deposit,
                'customization': customization,
                'image_url': product.image_url
            })

        # ✅ GST LOGIC (ONLY HERE)
        GST_RATE = 0.18
        gst = round(total_items_price * GST_RATE, 2)

        # ✅ FINAL TOTAL
        total_with_gst = round(total_items_price + gst + total_deposit, 2)

        return render_template(
            'cart.html',
            cart_items=enriched_cart,
            total_before_gst=total_items_price,
            total_deposit=total_deposit,
            gst=gst,
            total_with_gst=total_with_gst
        )

    except Exception as e:
        app.logger.error(f"Cart error: {e}", exc_info=True)
        return render_template('cart.html', cart_items=[])


@app.route('/qr_scanner')
@login_required
def qr_scanner():
    """Payment page - reads stored prices"""
    try:
        if session.get('user_type') == 'admin':
            flash('Admins cannot make purchases', 'warning')
            return redirect(url_for('admin_scaffoldings'))
        
        cart_items = session.get('cart', [])
        
        if not cart_items:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('national_scaffoldings'))
        
        # Read stored values (never recalculate)
        total_items_price = 0.0
        total_deposit = 0.0
        
        for item in cart_items:
            product = Product.query.get(item['product_id'])
            if not product:
                continue
            
            item_total = float(item.get('item_total', 0))
            item_deposit = float(item.get('item_deposit', 0))
            
            total_items_price += item_total
            total_deposit += item_deposit
        
        # Validate totals
        if total_items_price <= 0:
            flash('Cart totals invalid. Please review your cart.', 'error')
            return redirect(url_for('cart'))
        
        gst = total_items_price * 0.18
        total_with_gst = total_items_price + total_deposit + gst
        
        # Generate QR code
        qr_data = f"upi://pay?pa=nationalscaffolding@phonepe&pn=The National Scaffolding&am={total_with_gst:.2f}&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        app.logger.info(
            f"[PAYMENT] User {current_user.id} | Total: ₹{total_with_gst:.2f}"
        )
        
        return render_template(
            'qr_scanner.html', 
            total=total_items_price,
            gst=gst,
            total_deposit=total_deposit,
            total_with_gst=total_with_gst,
            qr_code=qr_code_base64,
            cart_items=cart_items
        )
        
    except Exception as e:
        app.logger.error(f"QR scanner error: {e}", exc_info=True)
        flash('Error loading payment page', 'error')
        return redirect(url_for('cart'))

@app.route('/complete_order', methods=['POST'])
@login_required
def complete_order():
    try:
        data = request.get_json(silent=True) or {}
        transaction_id = str(data.get('transaction_id', '')).strip()

        GST_RATE = 0.18  # 18% GST

        # -------------------------------
        # VALIDATE TRANSACTION ID
        # -------------------------------
        if not transaction_id:
            return jsonify({
                'success': False,
                'message': 'Transaction ID is required'
            }), 400

        # Prevent duplicate transaction IDs
        existing = Order.query.filter_by(transaction_id=transaction_id).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Transaction ID already used'
            }), 400

        # -------------------------------
        # VALIDATE CART
        # -------------------------------
        cart = session.get('cart', [])
        if not cart:
            return jsonify({
                'success': False,
                'message': 'Cart is empty'
            }), 400

        # -------------------------------
        # RE-CALCULATE TOTAL (BACKEND ONLY)
        # -------------------------------
        subtotal = 0.0
        deposit_total = 0.0

        for item in cart:
            subtotal += float(item.get('item_total', 0))
            deposit_total += float(item.get('item_deposit', 0))

        gst_amount = subtotal * GST_RATE
        total_price = subtotal + gst_amount + deposit_total

        if total_price <= 0:
            return jsonify({
                'success': False,
                'message': 'Invalid order amount'
            }), 400

        # -------------------------------
        # CREATE ORDER (FINAL PAYABLE)
        # -------------------------------
        order = Order(
            user_id=current_user.id,
            total_price=total_price,        # ✅ includes GST + deposit
            status='pending_verification',
            transaction_id=transaction_id
        )

        db.session.add(order)
        db.session.flush()  # get order.id

        # -------------------------------
        # SAVE ORDER ITEMS
        # -------------------------------
        for item in cart:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.get('product_id'),
                product_name=item.get('product_name'),
                quantity=int(item.get('quantity', 1)),
                price=float(item.get('unit_price', 0))
            )
            db.session.add(order_item)

        db.session.commit()

        # -------------------------------
        # CLEAR CART (ONLY AFTER SUCCESS)
        # -------------------------------
        session.pop('cart', None)
        session.modified = True

        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'total_paid': round(total_price, 2),
            'gst': round(gst_amount, 2)
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error("Complete order failed", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Error completing order'
        }), 500

@app.route('/my_orders')
@login_required
def my_orders():
    try:
        if session.get('user_type') == 'admin':
            return redirect(url_for('admin_scaffoldings'))

        orders = Order.query.filter_by(user_id=current_user.id)\
            .order_by(Order.order_date.desc())\
            .all()

        # Convert UTC to IST for display
        for order in orders:
            order.display_time = utc_to_ist(order.order_date)

        return render_template('my_orders.html', orders=orders)

    except Exception as e:
        app.logger.error(f"My orders error: {e}", exc_info=True)
        return render_template('my_orders.html', orders=[])
    
@app.route('/remove_from_cart/<int:index>')
@login_required
def remove_from_cart(index):
    try:
        cart = session.get('cart', [])
        if 0 <= index < len(cart):
            cart.pop(index)
            session['cart'] = cart
            session.modified = True
        return redirect(url_for('cart'))
    except Exception as e:
        app.logger.error(f"Remove from cart error: {e}")
        return redirect(url_for('cart'))



    
@app.route('/admin/vertical/product/<int:product_id>/delete', methods=['POST'])
@login_required
def vertical_delete(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
    product = VerticalProduct.query.get_or_404(product_id)
    
    # Delete image files
    if product.image_url:
        image_paths = product.image_url.split(',')
        for image_path in image_paths:
            if image_path.strip():
                full_path = os.path.join(app.static_folder, image_path.strip())
                if os.path.exists(full_path):
                    os.remove(full_path)
    
    # Delete product from database
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})
    
@app.route('/admin/vertical/product/create', methods=['GET', 'POST'])
@login_required
def vertical_create():
    if session.get('user_type') != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Handle other form fields
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        cuplock_type = request.form.get('cuplock_type')
        
        # Handle multiple image uploads
        image_paths = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Create unique filename to avoid overwrites
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    # Store relative path for database
                    image_paths.append(f"uploads/{unique_filename}")
        
        # Join all image paths with comma
        image_url = ','.join(image_paths) if image_paths else None
        
        # Create product with all images
        product = VerticalProduct(
            name=name,
            description=description,
            category=category,
            cuplock_type=cuplock_type,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product created successfully! Now you can add sizes and configurations.', 'success')
        # FIXED: Redirect to edit page instead of list
        return redirect(url_for('cuplock.vertical_edit', product_id=product.id))
    
    return render_template('admin/vertical_create.html')

@app.route('/admin/vertical/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def vertical_edit(product_id):
    if session.get('user_type') != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
        
    product = VerticalProduct.query.get_or_404(product_id)
    
    if request.method == 'POST':
        # Handle other form fields
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.cuplock_type = request.form.get('cuplock_type')
        
        # Handle multiple image uploads
        if 'images' in request.files:
            files = request.files.getlist('images')
            new_image_paths = []
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Create unique filename to avoid overwrites
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    # Store relative path for database
                    new_image_paths.append(f"uploads/{unique_filename}")
            
            # Combine existing images with new ones
            if product.image_url:
                existing_images = product.image_url.split(',')
                all_images = existing_images + new_image_paths
            else:
                all_images = new_image_paths
            
            # Update image_url with all images
            product.image_url = ','.join(filter(None, all_images))
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        # Keep user on edit page after updating
        return redirect(url_for('cuplock_vertical_edit`', product_id=product_id))
    
    return render_template('admin/vertical_edit.html', product=product)

@app.route('/admin/complete_order/<int:order_id>', methods=['POST'])
@login_required
def admin_complete_order(order_id):
    """Admin marks an approved order as completed"""
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        order = Order.query.get_or_404(order_id)

        if order.status != 'approved':
            return jsonify({
                'success': False,
                'message': 'Only approved orders can be completed'
            }), 400

        order.status = 'completed'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Order marked as completed'
        })

    except Exception as e:
        app.logger.error(f"Admin complete order error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error completing order'}), 500

    
@app.route('/admin_scaffoldings')
@login_required
def admin_scaffoldings():
    try:
        # ✅ CHECK USER TYPE AND PANEL TYPE ONLY (NOT OTP YET)
        # OTP check is done during login flow, not here
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        
        if session.get('panel_type') != 'scaffolding':
            flash('Access denied. Wrong admin panel.', 'error')
            return redirect(url_for('admin_login'))
        
        # ✅ NOW CHECK OTP VERIFICATION
        if session.get('otp_verified') != True:
            flash('OTP verification required', 'error')
            return redirect(url_for('admin_login'))

        # ✅ SHOW ONLY ACTIVE NON-FABRICATION PRODUCTS
        products = Product.query.filter(
            Product.product_type != 'fabrication',
            Product.is_active == True
        ).order_by(Product.id.desc()).all()

        return render_template(
            'admin_scaffoldings.html',
            products=products
        )

    except Exception as e:
        app.logger.error(f"Admin scaffoldings error: {e}", exc_info=True)
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_scaffolding_product(product_id):
    """Edit scaffolding product"""
    try:
        if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
            return redirect(url_for('dashboard'))
        
        product = Product.query.get_or_404(product_id)
        
        if request.method == 'POST':
              # Update product details
              product.name = request.form.get('name', product.name)
              product.description = request.form.get('description', '')
              product.category = request.form.get('category', product.category)
              product.product_type = request.form.get('product_type', product.product_type or 'Aluminium Scaffolding')
              product.price = float(request.form.get('price', product.price))
              product.rent_price = float(request.form.get('rent_price', product.rent_price or 0))
              product.deposit_amount = float(request.form.get('deposit_amount', product.deposit_amount or 0))
              product.weight_per_unit = float(request.form.get('weight_per_unit', product.weight_per_unit or 0))
              
              db.session.commit()
              flash('Product updated successfully!', 'success')
              return redirect(url_for('admin_scaffoldings'))
        
        return render_template('edit_scaffolding_product.html', product=product)
    
    except Exception as e:
        app.logger.error(f"Error editing scaffolding product: {e}", exc_info=True)
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_scaffoldings'))


# ... your other imports ...
@app.route('/debug/cuplock_ledger/<int:product_id>')
def debug_cuplock_ledger(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        sizes = CuplockLedgerSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()
        
        sizes_data = []
        for s in sizes:
            sizes_data.append({
                'id': s.id,
                'label': s.size_label,
                'weight': float(s.weight_kg or 0),
                'buy_price': float(s.buy_price or 0),
                'rent_price': float(s.rent_price or 0),
                'deposit': float(s.deposit_amount or 0)
            })
        
        return jsonify({
            'product': {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'cuplock_type': product.cuplock_type
            },
            'sizes': sizes_data
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/cuplock_products')
def cuplock_products():
    """List all Cuplock products"""
    try:
        # from cuplock_routes import get_image_url
        
        vertical_products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()

        ledger_products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='ledger',
            is_active=True
        ).all()
        
        # Add display_image_url to each product for template rendering
        for product in vertical_products:
            product.display_image_url = get_image_url(product.image_url)
        
        for product in ledger_products:
            product.display_image_url = get_image_url(product.image_url)

        return render_template(
            'cuplock_products.html',
            vertical_products=vertical_products,
            ledger_products=ledger_products
        )
    except Exception as e:
        app.logger.error(f"Error loading cuplock products: {e}")
        flash('Error loading Cuplock products', 'error')
        return redirect(url_for('national_scaffoldings'))
    
@app.route('/admin_fabrication')
@login_required
def admin_fabrication():
    try:
        # ✅ CHECK USER TYPE AND PANEL TYPE ONLY (NOT OTP YET)
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        
        if session.get('panel_type') != 'fabrication':
            flash('Access denied. Wrong admin panel.', 'error')
            return redirect(url_for('admin_login'))
        
        # ✅ NOW CHECK OTP VERIFICATION
        if session.get('otp_verified') != True:
            flash('OTP verification required', 'error')
            return redirect(url_for('admin_login'))

        # ✅ ONLY TRUE FABRICATION CATEGORIES
        fabrication_only_categories = ['steel', 'custom', 'parts', 'fabrication', 'fabrications']
        
        products = Product.query.filter(
            Product.category.in_(fabrication_only_categories),
            Product.is_active == True
        ).order_by(Product.id.desc()).all()

        # Group products by category for display
        products_by_category = {}
        for product in products:
            cat = product.category or 'other'
            if cat not in products_by_category:
                products_by_category[cat] = []
            products_by_category[cat].append(product)

        return render_template(
            'admin_fabrication.html',
            products=products,
            products_by_category=products_by_category
        )

    except Exception as e:
        app.logger.error(f"Admin fabrication error: {e}", exc_info=True)
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin_orders')
@login_required
def admin_orders():
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        admin_username = current_user.username
        if admin_username == 'admin_scaffolding':
            orders = db.session.query(Order).join(OrderItem).join(Product).filter(Product.product_type == 'scaffolding').distinct().order_by(Order.order_date.desc()).all()
        elif admin_username == 'admin_fabrication':
            orders = db.session.query(Order).join(OrderItem).join(Product).filter(Product.product_type == 'fabrication').distinct().order_by(Order.order_date.desc()).all()
        else:
            orders = Order.query.order_by(Order.order_date.desc()).all()
        
        return render_template('admin_orders.html', orders=orders)
    except Exception as e:
        app.logger.error(f"Admin orders error: {e}")
        return render_template('admin_orders.html', orders=[])

@app.route('/admin_analytics')
@login_required
def admin_analytics():
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        orders = Order.query.all()
        monthly_data = {}
        yearly_data = {}
        category_data = {}
        
        for order in orders:
            month_key = order.order_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'revenue': 0, 'orders': 0}
            monthly_data[month_key]['revenue'] += float(order.total_price)
            monthly_data[month_key]['orders'] += 1
            
            year_key = order.order_date.strftime('%Y')
            if year_key not in yearly_data:
                yearly_data[year_key] = {'revenue': 0, 'orders': 0}
            yearly_data[year_key]['revenue'] += float(order.total_price)
            yearly_data[year_key]['orders'] += 1
            
            # Fix: Use OrderItem.query.filter_by() instead of order.items
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            for item in order_items:
                product = Product.query.get(item.product_id)
                if product:
                    category = product.category or 'Other'
                    if category not in category_data:
                        category_data[category] = {'revenue': 0, 'quantity': 0}
                    
                    price_data = calculate_price(product, item.customization or {})
                    unit_price = price_data['price']
                    category_data[category]['revenue'] += unit_price * item.quantity 
                    category_data[category]['quantity'] += item.quantity
        
        sorted_months = sorted(monthly_data.keys())
        total_revenue = sum(order.total_price for order in orders)
        total_orders = len(orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return render_template('admin_analytics.html', monthly_data=monthly_data, yearly_data=yearly_data, category_data=category_data, sorted_months=sorted_months, total_revenue=total_revenue, total_orders=total_orders, avg_order_value=avg_order_value)
    except Exception as e:
        app.logger.error(f"Admin analytics error: {e}")
        return render_template('admin_analytics.html', monthly_data={}, yearly_data={}, category_data={}, sorted_months=[], total_revenue=0, total_orders=0, avg_order_value=0)
@app.route('/admin_logout')
@login_required
def admin_logout():
    try:
        if session.get('user_type') == 'admin':
            # Clear all session data including OTP verification
            session.clear()
            logout_user()
            flash('Admin logged out successfully', 'success')
            return redirect(url_for('index'))
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Logout error: {e}")
        return redirect(url_for('dashboard'))
    

@app.route('/admin_add_fabrication_product', methods=['POST'])
def admin_add_fabrication_product():
    try:
        # Get form data
        name = request.form.get('name')
        price = request.form.get('price')
        category = request.form.get('category')  # steel, aluminium, etc.
        description = request.form.get('description')
        
        app.logger.info(f"Adding product: {name}, category: {category}")
        
        # Create new product - FIXED: Set product_type to 'fabrication'
        new_product = Product(
            name=name,
            price=price,
            category='fabrication',  # ALWAYS set to 'fabrication'
            product_type='fabrication',  # FIXED: This was missing!
            description=description,
            is_active=True
        )
        
        # Handle image uploads
        if 'product_images' in request.files:
            images = request.files.getlist('product_images')
            image_urls = []
            
            for image in images:
                if image and image.filename:
                    filename = secure_filename(image.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    image.save(image_path)
                    image_urls.append(f"uploads/{unique_filename}")
            
            if image_urls:
                new_product.image_url = ','.join(image_urls)
        
        # Save to database
        db.session.add(new_product)
        db.session.commit()
        
        app.logger.info(f"Added new fabrication product: {name}")
        return jsonify({'success': True, 'message': 'Product added successfully'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding fabrication product: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})
# @app.route('/admin_add_product', methods=['GET', 'POST'])
# @login_required
# def admin_add_product():
#     """Add new scaffolding product with cuplock support (FIXED)"""
#     try:
#         # Admin check
#         if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
#             return redirect(url_for('dashboard'))

#         # -------------------------------
#         # GET REQUEST
#         # -------------------------------
#         if request.method == 'GET':
#             return render_template('add_scaffolding_product.html')

#         # -------------------------------
#         # 1. READ FORM DATA (SAFE)
#         # -------------------------------
#         name = request.form.get('name')
#         description = request.form.get('description', '')
#         category = request.form.get('category')
#         cuplock_type = request.form.get('cuplock_type', '')
#         product_type = request.form.get('product_type', 'scaffolding')

#         price = safe_float(request.form.get('price')) or 0.0
#         rent_price = safe_float(request.form.get('rent_price')) or 0.0
#         deposit_amount = safe_float(request.form.get('deposit_amount')) or 0.0
#         weight_per_unit = safe_float(request.form.get('weight_per_unit')) or 0.0

#         app.logger.info(
#             f"[ADD PRODUCT] name={name}, category={category}, cuplock_type={cuplock_type}"
#         )

#         # -------------------------------
#         # 2. VALIDATION
#         # -------------------------------
#         if not name or not category:
#             flash('Product name and category are required', 'error')
#             return render_template('add_scaffolding_product.html')

#         if category == 'cuplock' and cuplock_type not in ['ledger', 'vertical']:
#             flash('Please select Cuplock type (Ledger or Vertical)', 'error')
#             return render_template('add_scaffolding_product.html')

#         # -------------------------------
#         # 3. LEDGER SAFETY
#         # -------------------------------
#         if category == 'cuplock' and cuplock_type == 'ledger':
#             price = 0.0
#             rent_price = 0.0
#             deposit_amount = 0.0

#         # -------------------------------
#         # 4. CREATE PRODUCT
#         # -------------------------------
#         product = Product(
#             name=name,
#             description=description,
#             category=category,
#             cuplock_type=cuplock_type if category == 'cuplock' else None,
#             product_type=product_type,
#             price=price,
#             rent_price=rent_price,
#             deposit_amount=deposit_amount,
#             weight_per_unit=weight_per_unit,
#             is_active=True
#         )

#         # -------------------------------
#         # 5. IMAGE UPLOAD
#         # -------------------------------
#         image_urls = []
#         uploaded_files = request.files.getlist('product_images')

#         if uploaded_files:
#             os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#             for file in uploaded_files:
#                 if file and file.filename and allowed_file(file.filename):
#                     filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
#                     filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                     file.save(filepath)
#                     image_urls.append(f"uploads/{filename}")

#         product.image_url = ','.join(image_urls) if image_urls else 'images/no-image.png'

#         db.session.add(product)
#         db.session.flush()  # get product.id

#         # -------------------------------
#         # 6. HANDLE CUPLOCK LEDGER SIZES
#         # -------------------------------
#                # ... inside admin_add_product function ...

#         # -------------------------------
#         # 6. HANDLE CUPLOCK LEDGER SIZES
#         # -------------------------------
#                # -------------------------------
#         # 8. REDIRECT
#         # -------------------------------
#         if category == 'cuplock' and cuplock_type == 'ledger':
#             flash('✅ Ledger product created! Please add or edit sizes.', 'success')
#             # ❌ THIS LINE IS CAUSING THE 404 ERROR:
#             return redirect(url_for('edit_ledger_sizes', product_id=product.id))

#         flash(f'✅ Product "{name}" created successfully!', 'success')
#         return redirect(url_for('admin_scaffoldings'))

#             # if size_count == 0:
#             #     flash('Ledger product created, but no sizes were added.', 'warning')

#         # -------------------------------
#         # 7. COMMIT
#         # -------------------------------
#         db.session.commit()

#         # -------------------------------
#         # 8. REDIRECT
#         # -------------------------------
#                # -------------------------------
#         # 8. REDIRECT
#         # -------------------------------
#         if category == 'cuplock' and cuplock_type == 'ledger':
#             flash('✅ Ledger product created! Please add or edit sizes.', 'success')
#             # ✅ FIXED: Redirect to the Cuplock Blueprint route (which exists)
#             return redirect(url_for('cuplock.ledger_edit', product_id=product.id))

#         flash(f'✅ Product "{name}" created successfully!', 'success')
#         return redirect(url_for('admin_scaffoldings'))

#     except Exception as e:
#         db.session.rollback()
#         app.logger.error(f"admin_add_product error: {e}", exc_info=True)
#         flash(f'Error creating product: {str(e)}', 'error')
#         return render_template('add_scaffolding_product.html')



@app.route('/admin_add_product', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    """Add new scaffolding product with cuplock support (FIXED)"""
    try:
        # Admin check
        if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
            return redirect(url_for('dashboard'))

        # -------------------------------
        # GET REQUEST
        # -------------------------------
        if request.method == 'GET':
            return render_template('add_scaffolding_product.html')

        # -------------------------------
        # 1. READ FORM DATA (SAFE)
        # -------------------------------
        name = request.form.get('name')
        description = request.form.get('description', '')
        category = request.form.get('category')
        cuplock_type = request.form.get('cuplock_type', '')
        product_type = request.form.get('product_type', 'scaffolding')

        price = safe_float(request.form.get('price')) or 0.0
        rent_price = safe_float(request.form.get('rent_price')) or 0.0
        deposit_amount = safe_float(request.form.get('deposit_amount')) or 0.0
        weight_per_unit = safe_float(request.form.get('weight_per_unit')) or 0.0

        app.logger.info(
            f"[ADD PRODUCT] name={name}, category={category}, cuplock_type={cuplock_type}"
        )

        # -------------------------------
        # 2. VALIDATION
        # -------------------------------
        if not name or not category:
            flash('Product name and category are required', 'error')
            return render_template('add_scaffolding_product.html')

        if category == 'cuplock' and cuplock_type not in ['ledger', 'vertical']:
            flash('Please select Cuplock type (Ledger or Vertical)', 'error')
            return render_template('add_scaffolding_product.html')

        # -------------------------------
        # 3. LEDGER SAFETY
        # -------------------------------
        if category == 'cuplock' and cuplock_type == 'ledger':
            price = 0.0
            rent_price = 0.0
            deposit_amount = 0.0

        # -------------------------------
        # 4. CREATE PRODUCT
        # -------------------------------
        product = Product(
            name=name,
            description=description,
            category=category,
            cuplock_type=cuplock_type if category == 'cuplock' else None,
            product_type=product_type,
            price=price,
            rent_price=rent_price,
            deposit_amount=deposit_amount,
            weight_per_unit=weight_per_unit,
            is_active=True
        )

        # -------------------------------
        # 5. IMAGE UPLOAD
        # -------------------------------
        image_urls = []
        uploaded_files = request.files.getlist('product_images')

        if uploaded_files:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            for file in uploaded_files:
                if file and file.filename and allowed_file(file.filename):
                    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_urls.append(f"uploads/{filename}")

        product.image_url = ','.join(image_urls) if image_urls else 'images/no-image.png'

        db.session.add(product)
        db.session.flush()  # get product.id

        # -------------------------------
        # 6. HANDLE CUPLOCK LEDGER SIZES (FIXED)
        # -------------------------------
        if category == 'cuplock' and cuplock_type == 'ledger':
            from models import CuplockLedgerSize

            index = 1
            size_count = 0

            while True:
                size_name = request.form.get(f'size_name_{index}')
                if not size_name:
                    break

                # ✅ FIX 1: Truncate size_name to 50 characters to prevent DB error
                if len(size_name) > 50:
                    size_name = size_name[:50]
                    app.logger.warning(f"Size name truncated to 50 chars: {size_name}")

                ledger_size = CuplockLedgerSize(
                    product_id=product.id,
                    size_label=size_name,
                    buy_price=safe_float(request.form.get(f'size_price_{index}')) or 0.0,
                    rent_price=safe_float(request.form.get(f'size_rent_price_{index}')) or 0.0,
                    deposit_amount=safe_float(request.form.get(f'size_deposit_{index}')) or 0.0,
                    weight_kg=safe_float(request.form.get(f'size_weight_{index}')) or 0.0,
                    is_active=True
                )

                db.session.add(ledger_size)
                size_count += 1
                index += 1

            if size_count == 0:
                flash('Ledger product created, but no sizes were added.', 'warning')

        # -------------------------------
        # 7. COMMIT
        # -------------------------------
        db.session.commit()

        # -------------------------------
        # 8. REDIRECT (FIXED)
        # -------------------------------
        if category == 'cuplock' and cuplock_type == 'ledger':
            flash('✅ Ledger product created! Please add or edit sizes.', 'success')
            # ✅ FIX 2: Redirect to the Blueprint route (cuplock.ledger_edit) instead of the local broken route
            return redirect(url_for('cuplock.ledger_edit', product_id=product.id))

        flash(f'✅ Product "{name}" created successfully!', 'success')
        return redirect(url_for('admin_scaffoldings'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"admin_add_product error: {e}", exc_info=True)
        flash(f'Error creating product: {str(e)}', 'error')
        return render_template('add_scaffolding_product.html')
@app.route('/check_categories')
def check_categories():
    try:
        # Get all unique categories
        categories = db.session.query(Product.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        # Count products in each category
        category_counts = {}
        for cat in categories:
            count = Product.query.filter_by(category=cat).count()
            category_counts[cat] = count
        
        return jsonify({
            'categories': categories,
            'counts': category_counts
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug_all_products')
def debug_all_products():
    try:
        # Get all products with their details
        products = Product.query.all()
        
        # Group products by category
        by_category = {}
        for p in products:
            cat = p.category or 'NULL'
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'product_type': p.product_type,
                'is_active': p.is_active
            })
        
        # Get all unique categories
        categories = list(by_category.keys())
        
        return jsonify({
            'total_products': len(products),
            'categories': categories,
            'products_by_category': by_category
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/debug_products')
def debug_products():
    try:
        # Get all products
        all_products = Product.query.all()
        
        # Get products with category = 'fabrication'
        fabrication_products = Product.query.filter_by(category='fabrication').all()
        
        # Get all unique categories
        categories = db.session.query(Product.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        debug_info = {
            'total_products': len(all_products),
            'fabrication_products': len(fabrication_products),
            'all_categories': categories,
            'sample_products': []
        }
        
        # Get sample of products with their details
        for p in all_products[:5]:
            debug_info['sample_products'].append({
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'product_type': p.product_type,
                'is_active': p.is_active
            })
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)})
    
# ============================================
# DEBUG AND FIX ROUTES FOR FABRICATION
# Add these to your app.py
# ============================================
@app.route('/debug_fabrication_vs_scaffolding')
def debug_fabrication_vs_scaffolding():
    """Debug route to see the separation between fabrication and scaffolding"""
    try:
        scaffolding_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories']
        
        all_products = Product.query.filter(Product.is_active == True).all()
        
        fabrication_products = []
        scaffolding_products = []
        
        for product in all_products:
            if product.category in scaffolding_categories:
                scaffolding_products.append({
                    'id': product.id,
                    'name': product.name,
                    'category': product.category
                })
            else:
                fabrication_products.append({
                    'id': product.id,
                    'name': product.name,
                    'category': product.category
                })
        
        return jsonify({
            'total_active_products': len(all_products),
            'fabrication_products': fabrication_products,
            'scaffolding_products': scaffolding_products,
            'fabrication_categories': list(set(p['category'] for p in fabrication_products)),
            'scaffolding_categories_found': list(set(p['category'] for p in scaffolding_products))
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/debug_fabrication_products')
def debug_fabrication_products():
    """Check all products in database"""
    try:
        all_products = Product.query.all()
        
        by_category = {}
        for p in all_products:
            cat = p.category or 'NULL'
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'product_type': p.product_type,
                'is_active': p.is_active,
                'price': float(p.price) if p.price else 0
            })
        
        return jsonify({
            'total_products': len(all_products),
            'products_by_category': by_category,
            'fabrication_count': len([p for p in all_products if p.category == 'fabrication']),
            'active_fabrication_count': len([p for p in all_products if p.category == 'fabrication' and p.is_active]),
            'all_categories': list(by_category.keys())
        })
    except Exception as e:
        return jsonify({'error': str(e)})


# Replace your existing fabrications route with this one
@app.route('/fabrications')
def fabrications():
    try:
        # Get category filter from URL
        category_filter = request.args.get('category', 'all')
        
        app.logger.info(f"Fabrications route - Category filter: {category_filter}")
        
        # IMPORTANT: Exclude scaffolding categories from fabrication
        scaffolding_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories']
        
        # Base query - ONLY fabrication products (exclude scaffolding)
        query = Product.query.filter(
            Product.category.notin_(scaffolding_categories),  # FIXED: removed 'a' -> notin_
            Product.is_active == True
        )
        
        # Apply subcategory filter if specified
        if category_filter != 'all':
            query = query.filter(Product.category == category_filter)
        
        products = query.order_by(Product.id.desc()).all()
        
        app.logger.info(f"Found {len(products)} fabrication products")
        
        # Log what categories we actually found
        found_categories = set()
        for product in products:
            found_categories.add(product.category)
        app.logger.info(f"Categories found: {list(found_categories)}")
        
        return render_template(
            'fabrications.html',
            products=products,
            category=category_filter
        )
        
    except Exception as e:
        app.logger.error(f"Fabrications route error: {e}", exc_info=True)
        return render_template(
            'fabrications.html',
            products=[],
            category='all'
        )

# Replace the duplicate function with this one
@app.route('/fix_fabrication_categories')
def fix_fabrication_categories():
    """Fix products that should be fabrication"""
    try:
        # Define patterns that should be fabrication
        fabrication_patterns = ['steel', 'aluminium', 'custom', 'parts', 'fabrications']
        
        updated_count = 0
        updated_products = []
        
        # Check products with category matching fabrication patterns
        for pattern in fabrication_patterns:
            products = Product.query.filter(
                Product.category == pattern,
                Product.is_active == True
            ).all()
            
            for product in products:
                old_category = product.category
                product.category = 'fabrication'
                updated_count += 1
                updated_products.append({
                    'id': product.id,
                    'name': product.name,
                    'old_category': old_category,
                    'new_category': 'fabrication'
                })
        
        if updated_count > 0:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Updated {updated_count} products to category=fabrication',
                'updated_products': updated_products
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No products found to update. You may need to create fabrication products manually.',
                'hint': 'Go to admin panel and add products with category=fabrication'
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)})


@app.route('/create_test_fabrication_products')
def create_test_fabrication_products():
    """Create sample fabrication products for testing"""
    try:
        test_products = [
            {
                'name': 'Steel Gate',
                'price': 5000.00,
                'category': 'fabrication',
                'product_type': 'steel',
                'description': 'Custom steel gate fabrication',
                'image_url': 'images/no-image.png'
            },
            {
                'name': 'Aluminium Window Frame',
                'price': 3000.00,
                'category': 'fabrication',
                'product_type': 'aluminium',
                'description': 'Custom aluminium window frames',
                'image_url': 'images/no-image.png'
            },
            {
                'name': 'Custom Steel Structure',
                'price': 15000.00,
                'category': 'fabrication',
                'product_type': 'custom',
                'description': 'Custom steel structure fabrication',
                'image_url': 'images/no-image.png'
            }
        ]
        
        created_products = []
        for prod_data in test_products:
            # Check if already exists
            existing = Product.query.filter_by(name=prod_data['name']).first()
            if not existing:
                new_product = Product(
                    name=prod_data['name'],
                    price=prod_data['price'],
                    category=prod_data['category'],
                    product_type=prod_data['product_type'],
                    description=prod_data['description'],
                    image_url=prod_data['image_url'],
                    is_active=True
                )
                db.session.add(new_product)
                created_products.append(prod_data['name'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created_products)} test fabrication products',
            'created_products': created_products
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)})
    
# DEBUG ROUTE - Add this temporarily to check your data


@app.route('/debug_form_submission', methods=['GET', 'POST'])
def debug_form_submission():
    """A simple route to show what data the server receives on form submission."""
    if request.method == 'POST':
        print("="*20)
        print("DEBUGGING FORM SUBMISSION")
        print("="*20)
        
        print("--- Form Data ---")
        for key, value in request.form.items():
            print(f"{key}: {value}")
        
        print("\n--- Files Data ---")
        for key, file in request.files.items():
            print(f"{key}: {file.filename}")
        
        print("="*20)
        return "Data received. Check your server console/terminal."

    return "This is a debugging route. Submit your form to see the data received."

@app.route('/admin/product/<int:product_id>/edit_ledger_sizes', methods=['GET', 'POST'])
@login_required
def edit_ledger_sizes(product_id):
    """Edit cuplock ledger product sizes"""
    try:
        if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
            return redirect(url_for('dashboard'))
        
        product = Product.query.get_or_404(product_id)
        
        # Verify this is a cuplock ledger product
        if product.category != 'cuplock' or product.cuplock_type != 'ledger':
            flash('This page is only for Cuplock Ledger products', 'error')
            return redirect(url_for('admin_scaffoldings'))
        
        # Import CuplockLedgerSize model
        from models import CuplockLedgerSize
        
        if request.method == 'POST':
            # Handle form submission to update sizes
            size_ids = request.form.getlist('size_id')
            size_names = request.form.getlist('size_name')
            size_prices = request.form.getlist('size_price')
            size_rent_prices = request.form.getlist('size_rent_price')
            size_deposits = request.form.getlist('size_deposit')
            size_weights = request.form.getlist('size_weight')
            size_active = request.form.getlist('size_active')
            
            # Update existing sizes
            for i, size_id in enumerate(size_ids):
                if size_id:  # Existing size
                    size = CuplockLedgerSize.query.get(size_id)
                    if size:
                        size.size_label = size_names[i]
                        size.buy_price = float(size_prices[i])
                        size.rent_price = float(size_rent_prices[i])
                        size.deposit_amount = float(size_deposits[i])
                        size.weight_kg = float(size_weights[i])
                        size.is_active = 'active' in size_active
            
            # Handle new sizes
            new_size_names = request.form.getlist('new_size_name')
            new_size_prices = request.form.getlist('new_size_price')
            new_size_rent_prices = request.form.getlist('new_size_rent_price')
            new_size_deposits = request.form.getlist('new_size_deposit')
            new_size_weights = request.form.getlist('new_size_weight')
            
            for i, size_name in enumerate(new_size_names):
                if size_name.strip():  # Only add if name is not empty
                    new_size = CuplockLedgerSize(
                        product_id=product.id,
                        size_label=size_name,
                        buy_price=float(new_size_prices[i]),
                        rent_price=float(new_size_rent_prices[i]),
                        deposit_amount=float(new_size_deposits[i]),
                        weight_kg=float(new_size_weights[i]),
                        is_active=True
                    )
                    db.session.add(new_size)
            
            db.session.commit()
            flash('Product sizes updated successfully!', 'success')
            return redirect(url_for('admin_scaffoldings'))
        
        # GET request - show edit form
        sizes = CuplockLedgerSize.query.filter_by(product_id=product_id).all()
        
        return render_template('edit_ledger_sizes.html', product=product, sizes=sizes)
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error editing ledger sizes: {e}", exc_info=True)
        flash(f'Error updating sizes: {str(e)}', 'error')
        return redirect(url_for('admin_scaffoldings'))

@app.route('/admin/ledger_size/<int:size_id>/delete', methods=['POST'])
@login_required
def delete_ledger_size(size_id):
    """Delete a cuplock ledger size"""
    try:
        if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        from models import CuplockLedgerSize
        size = CuplockLedgerSize.query.get_or_404(size_id)
        
        product_id = size.product_id
        size_name = size.size_label
        
        db.session.delete(size)
        db.session.commit()
        
        flash(f'Size "{size_name}" deleted successfully', 'success')
        return redirect(url_for('edit_ledger_sizes', product_id=product_id))
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting ledger size: {e}", exc_info=True)
        flash(f'Error deleting size: {str(e)}', 'error')
        return redirect(url_for('admin_scaffoldings'))

@app.route('/admin_update_product/<int:product_id>', methods=['POST'])
@login_required
def admin_update_product(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False}), 403
        
        product = Product.query.get_or_404(product_id)
        existing_json = request.form.get('existing_image_urls')
        existing_list = []
        try:
            if existing_json:
                existing_list = json.loads(existing_json)
        except Exception:
            existing_list = []

        # Determine which existing images will be removed (but do NOT delete yet)
        current_list = [u for u in (product.image_url or '').split(',') if u.strip()]
        removed_old_images = [img for img in current_list if img not in existing_list]

        new_urls = []
        saved_new_filepaths = []
        uploaded_files = request.files.getlist('product_images') if request.files else []
        if uploaded_files:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            for file in uploaded_files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_name = f"{uuid.uuid4().hex}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                    try:
                        file.save(filepath)
                        saved_new_filepaths.append(filepath)
                        new_urls.append(f"uploads/{unique_name}")
                        app.logger.info(f"Saved uploaded file for update product {product_id}: {filepath}")
                    except Exception as e:
                        app.logger.error(f"Error saving uploaded file: {e}")

            # Validate new files are present and valid images before deleting old ones
            for p in saved_new_filepaths:
                try:
                    if not os.path.exists(p):
                        raise FileNotFoundError(p)
                    with Image.open(p) as im:
                        im.verify()
                except Exception as e:
                    # cleanup any new files that were saved
                    for q in saved_new_filepaths:
                        try:
                            if os.path.exists(q):
                                os.remove(q)
                        except Exception:
                            pass
                    app.logger.error(f"Uploaded image validation failed for product update {product_id}: {e}")
                    return jsonify({'success': False, 'message': 'One or more uploaded images are invalid or corrupted. Please try different files.'}), 500

        # All new files validated — safe to delete removed old images
        for img in removed_old_images:
            # Convert relative path to full filesystem path
            old_image_path = os.path.join('static', img) if not img.startswith('static') else img
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    app.logger.info(f"Removed old image file for product {product_id}: {old_image_path}")
                except Exception as e:
                    app.logger.warning(f"Error removing old file {old_image_path}: {e}")

        merged_urls = existing_list + new_urls
        product.image_url = ','.join(merged_urls) if merged_urls else 'images/no-image.png'

        
        product.name = request.form.get('name')
        new_price = safe_float(request.form.get('price'))
        if new_price is not None:
            product.price = new_price
        
        new_rent_price = safe_float(request.form.get('rent_price'))
        if new_rent_price is not None:
            product.rent_price = new_rent_price
        elif request.form.get('rent_price') == '':
            product.rent_price = None
        
        new_deposit = safe_float(request.form.get('deposit_amount'))
        if new_deposit is not None:
            product.deposit_amount = new_deposit
        elif request.form.get('deposit_amount') == '':
            product.deposit_amount = None
        
        new_weight = safe_float(request.form.get('weight_per_unit'))
        if new_weight is not None:
            product.weight_per_unit = new_weight
        elif request.form.get('weight_per_unit') == '':
            product.weight_per_unit = None
        
        product.description = request.form.get('description', '')
        product.category = request.form.get('category')
        
        # Validate price if provided
        if request.form.get('price'):
            price_valid, price_error = validate_price(request.form.get('price'), 'Price')
            if not price_valid:
                db.session.rollback()
                return jsonify({'success': False, 'message': price_error}), 400

        pricing_matrix_str = request.form.get('pricing_matrix')
        if pricing_matrix_str is not None:
            try:
                pricing_matrix_data = json.loads(pricing_matrix_str)
                product.customization_options = product.customization_options or {}
                product.customization_options['pricing_matrix'] = pricing_matrix_data
                flag_modified(product, 'customization_options')
            except Exception as e:
                app.logger.error(f"Error parsing pricing matrix for product {product_id}: {e}")
        
        # FIX: Add database commit here
        try:
            db.session.commit()
            app.logger.info(f"Product {product_id} updated. image_url={product.image_url}")
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating product {product_id}: {e}")
            return jsonify({'success': False, 'message': 'Failed to update product'}), 500
    except Exception as e:
        app.logger.error(f"Admin update product error: {e}")
        return jsonify({'success': False, 'message': 'Error updating product'}), 500

@app.route('/admin_get_product_pricing/<int:product_id>')
@login_required
def admin_get_product_pricing(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        product = Product.query.get_or_404(product_id)
        pricing = {}
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing = product.customization_options['pricing_matrix']
        
        return jsonify({'success': True, 'pricing_matrix': pricing})
    except Exception as e:
        app.logger.error(f"Admin get product pricing error: {e}")
        return jsonify({'success': False, 'message': 'Error getting pricing'}), 500

@app.route('/debug/images')
def debug_images_page():
    return render_template('debug_images.html')


@app.route('/debug/all_products')
def debug_all_products_images():
    """Debug route to see all products and their images - FIXED"""
    try:
        products = Product.query.all()
        result = []
        
        for product in products:
            images = []
            if product.image_url:
                # Split on comma and filter empty/whitespace entries
                images = [img.strip() for img in product.image_url.split(',') if img.strip()]
            
            result.append({
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'image_url': product.image_url,
                'images': images,
                'image_count': len(images)
            })
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Debug all products error: {e}")
        return jsonify({'error': str(e)})

@app.route('/debug/product/<int:product_id>/images')
def debug_product_images_detail(product_id):
    """Debug route to see exactly what images are stored"""
    try:
        product = Product.query.get_or_404(product_id)
        
        debug_info = {
            'product_id': product_id,
            'product_name': product.name,
            'raw_image_url': product.image_url,
            'images': []
        }
        
        if product.image_url:
            images = [img.strip() for img in product.image_url.split(',') if img.strip()]
            debug_info['images'] = images
            debug_info['image_count'] = len(images)
            
            # Check if files exist
            for img in images:
                filepath = img.replace('/static/', 'static/')
                exists = os.path.exists(filepath)
                debug_info[f'{img}_exists'] = exists
        else:
            debug_info['image_count'] = 0
            debug_info['message'] = 'No images set for this product'
        
        return jsonify(debug_info)
    except Exception as e:
        app.logger.error(f"Debug product images detail error: {e}")
        return jsonify({'error': str(e)})

@app.route('/debug/product_images/<int:product_id>')
def debug_product_images(product_id):
    """Debug route to check image paths for a specific product"""
    try:
        product = Product.query.get_or_404(product_id)
        
        debug_info = {
            'product_id': product_id,
            'product_name': product.name,
            'raw_image_url': product.image_url,
            'display_image_url': getattr(product, 'display_image_url', None)
        }
        
        # Check if files exist
        if product.image_url:
            images = [img.strip() for img in product.image_url.split(',') if img.strip()]
            debug_info['images'] = images
            debug_info['image_count'] = len(images)
            
            # Check if files exist
            for img in images:
                # Try different path formats
                path_variants = [
                    os.path.join(app.static_folder, img),
                    os.path.join(app.static_folder, img.lstrip('/')),
                    os.path.join(app.root_path, 'static', img),
                    os.path.join(app.root_path, 'static', img.lstrip('/'))
                ]
                
                debug_info[f'{img}_paths'] = path_variants
                debug_info[f'{img}_exists'] = [os.path.exists(p) for p in path_variants]
                
                # If image starts with uploads/, check that path too
                if img.startswith('uploads/'):
                    upload_path = os.path.join(app.static_folder, img)
                    debug_info[f'{img}_upload_path'] = upload_path
                    debug_info[f'{img}_upload_exists'] = os.path.exists(upload_path)
        else:
            debug_info['image_count'] = 0
            debug_info['message'] = 'No images set for this product'
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/product/<int:product_id>/images')
def api_product_images(product_id):
    """API endpoint to get product images - useful for debugging"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        if not product.image_url:
            return jsonify({
                'success': True,
                'product_id': product_id,
                'product_name': product.name,
                'images': [],
                'image_count': 0
            })
        
        images = [url.strip() for url in product.image_url.split(',') if url.strip()]
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'product_name': product.name,
            'images': images,
            'image_count': len(images),
            'raw_image_url': product.image_url
        })
    except Exception as e:
        app.logger.error(f"API product images error: {e}")
        return jsonify({'error': str(e)})

@app.route('/admin_image_diagnostics')
@login_required
def admin_image_diagnostics():
    """Admin endpoint to check image health across all products.
    Returns detailed diagnostics for every image stored in the system.
    """
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        products = Product.query.all()
        diagnostics = {
            'total_products': len(products),
            'products': [],
            'summary': {
                'total_images': 0,
                'valid_images': 0,
                'missing_images': 0,
                'corrupted_images': 0,
                'total_size_mb': 0
            }
        }
        
        for product in products:
            if not product.image_url:
                continue
            
            images = [u for u in product.image_url.split(',') if u.strip()]
            if not images:
                continue
            
            product_diag = {
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'images': []
            }
            
            for img_url in images:
                filepath = img_url.replace('/static/', 'static/')
                img_info = validate_image_file(filepath)
                product_diag['images'].append(img_info)
                
                diagnostics['summary']['total_images'] += 1
                if img_info['valid']:
                    diagnostics['summary']['valid_images'] += 1
                elif not img_info['exists']:
                    diagnostics['summary']['missing_images'] += 1
                else:
                    diagnostics['summary']['corrupted_images'] += 1
                
                diagnostics['summary']['total_size_mb'] += img_info['size_bytes'] / (1024 * 1024)
            
            diagnostics['products'].append(product_diag)
        
        diagnostics['summary']['total_size_mb'] = round(diagnostics['summary']['total_size_mb'], 2)
        
        return jsonify({'success': True, 'data': diagnostics})
    except Exception as e:
        app.logger.error(f"Admin image diagnostics error: {e}")
        return jsonify({'success': False, 'message': 'Error running diagnostics'}), 500

@app.route('/admin_image_diagnostics/product/<int:product_id>')
@login_required
def admin_image_diagnostics_product(product_id):
    """Admin endpoint to check image health for a specific product.
    Returns detailed diagnostics for all images of that product.
    """
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        if not product.image_url:
            return jsonify({
                'success': True,
                'product_id': product_id,
                'product_name': product.name,
                'images': [],
                'summary': {
                    'total_images': 0,
                    'valid_images': 0,
                    'missing_images': 0,
                    'corrupted_images': 0,
                    'total_size_mb': 0
                }
            })
        
        images = [u for u in product.image_url.split(',') if u.strip()]
        diagnostics = {
            'success': True,
            'product_id': product_id,
            'product_name': product.name,
            'category': product.category,
            'images': [],
            'summary': {
                'total_images': len(images),
                'valid_images': 0,
                'missing_images': 0,
                'corrupted_images': 0,
                'total_size_mb': 0
            }
        }
        
        for img_url in images:
            filepath = img_url.replace('/static/', 'static/')
            img_info = validate_image_file(filepath)
            diagnostics['images'].append(img_info)
            
            if img_info['valid']:
                diagnostics['summary']['valid_images'] += 1
            elif not img_info['exists']:
                diagnostics['summary']['missing_images'] += 1
            else:
                diagnostics['summary']['corrupted_images'] += 1
            
            diagnostics['summary']['total_size_mb'] += img_info['size_bytes'] / (1024 * 1024)
        
        diagnostics['summary']['total_size_mb'] = round(diagnostics['summary']['total_size_mb'], 2)
        
        return jsonify(diagnostics)
    except Exception as e:
        app.logger.error(f"Admin image diagnostics product error: {e}")
        return jsonify({'success': False, 'message': 'Error running product diagnostics'}), 500

@app.route('/admin_update_pricing_matrix/<int:product_id>', methods=['POST'])
@login_required
def admin_update_pricing_matrix(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        product = Product.query.get_or_404(product_id)
        
        if not product.customization_options:
            product.customization_options = {}
        
        data = request.json
        pricing_matrix = data.get('pricing_matrix', {})
        
        product.customization_options['pricing_matrix'] = pricing_matrix
        
        flag_modified(product, 'customization_options')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pricing matrix updated successfully'})
    except Exception as e:
        app.logger.error(f"Admin update pricing matrix error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating pricing matrix'}), 500

@app.route('/admin_remove_photo/<int:product_id>', methods=['POST'])
@login_required
def admin_remove_photo(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        product = Product.query.get_or_404(product_id)
        data = request.get_json() or {}
        image_url = data.get('image_url')

        if not image_url:
            return jsonify({'success': False, 'message': 'No image_url provided'}), 400

        current = [u for u in (product.image_url or '').split(',') if u.strip()]
        if image_url in current:
            old_image_path = os.path.join(app.static_folder, image_url)
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    app.logger.info(f"Removed image file: {old_image_path}")
                except Exception as e:
                    app.logger.error(f"Error removing file: {e}")

            current.remove(image_url)
            product.image_url = ','.join(current) if current else 'images/no-image.png'

            db.session.commit()
            return jsonify({'success': True, 'message': 'Photo removed successfully'})

        return jsonify({'success': False, 'message': 'Image not found on product'}), 404
    except Exception as e:
        app.logger.error(f"Admin remove photo error: {e}")
        return jsonify({'success': False, 'message': 'Error removing photo'}), 500

@app.route('/admin_delete_product/<product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
        
        try:
            product_id_int = int(product_id)
        except ValueError:
            app.logger.error(f"Invalid product ID format received for deletion: {product_id}")
            return jsonify({'success': False, 'message': 'Invalid product ID format'}), 400

        app.logger.info(f"Attempting to delete product with ID: {product_id_int}")
        
        product = Product.query.get(product_id_int)
        if not product:
            app.logger.error(f"Product with ID {product_id_int} not found")
            return jsonify({'success': False, 'message': f'Product with ID {product_id_int} not found'}), 404
        
        product_name = product.name
        app.logger.info(f"Found product: {product_name} (ID: {product.id})")
        
        # Delete associated images
        if product.image_url:
            image_paths = product.image_url.split(',')
            for img_path in image_paths:
                old_image_path = img_path.strip().replace('/static/', 'static/')
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                        app.logger.info(f"Deleted image file: {old_image_path}")
                    except Exception as e:
                        app.logger.error(f"Error removing file {old_image_path}: {e}")
        
        # Delete product (This action now triggers CASCADE DELETE in database)
        product.is_active = False
        db.session.commit()
        
        app.logger.info(f"Successfully deleted product: {product_name} (ID: {product.id}) and its associated order items.")
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        log_message = f"Critical Error deleting product {product_id}. Exception: {str(e)}"
        app.logger.error(log_message, exc_info=True)
        
        return jsonify({
            'success': False, 
            'message': f'A severe server error occurred while deleting product: {str(e)}'
        }), 500

@app.route('/admin_pricing_matrix/<int:product_id>')
@login_required
def admin_pricing_matrix(product_id):
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        product = Product.query.get_or_404(product_id)
        
        if product.category not in ['aluminium', 'h-frames', 'accessories']:
            flash('Pricing matrix customization is only available for Aluminium, H-Frames, and Accessories products', 'warning')
            return redirect(url_for('admin_scaffoldings'))
        
        pricing_matrix = product.customization_options.get('pricing_matrix', {}) if product.customization_options else {}
        
        return render_template('admin_pricing_matrix.html', product=product, pricing_matrix=pricing_matrix)
    except Exception as e:
        app.logger.error(f"Admin pricing matrix error: {e}")
        return redirect(url_for('admin_scaffoldings'))

@app.route('/admin_aluminium_pricing')
@login_required
def admin_aluminium_pricing():
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        aluminium_products = Product.query.filter_by(category='aluminium').all()
        pricing_data = {}
        for product in aluminium_products:
            if product.customization_options and 'pricing_matrix' in product.customization_options:
                pricing_data[str(product.id)] = product.customization_options['pricing_matrix']
        
        return render_template('admin_aluminium_pricing.html', aluminium_products=aluminium_products, pricing_data=pricing_data)
    except Exception as e:
        app.logger.error(f"Admin aluminium pricing error: {e}")
        return redirect(url_for('admin_scaffoldings'))

@app.route('/admin_update_aluminium_pricing', methods=['POST'])
@login_required
def admin_update_aluminium_pricing():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.json
        pricing_data = data.get('pricing_data', {})
        
        for product_id, pricing_matrix in pricing_data.items():
            product = Product.query.get(int(product_id))
            if product and product.category == 'aluminium':
                if not product.customization_options:
                    product.customization_options = {}
                
                product.customization_options['pricing_matrix'] = pricing_matrix
                
                flag_modified(product, 'customization_options')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Aluminium pricing updated successfully'})
    except Exception as e:
        app.logger.error(f"Admin update aluminium pricing error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating aluminium pricing'}), 500

@app.route('/admin_hframes_pricing')
@login_required
def admin_hframes_pricing():
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        hframe_products = Product.query.filter_by(category='h-frames').all()
        pricing_data = {}
        for product in hframe_products:
            if product.customization_options and 'pricing_matrix' in product.customization_options:
                pricing_data[str(product.id)] = product.customization_options['pricing_matrix']
        
        return render_template('admin_hframes_pricing.html', hframe_products=hframe_products, pricing_data=pricing_data)
    except Exception as e:
        app.logger.error(f"Admin hframes pricing error: {e}")
        return redirect(url_for('admin_scaffoldings'))

@app.route('/admin_update_hframes_pricing', methods=['POST'])
@login_required
def admin_update_hframes_pricing():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.json
        pricing_data = data.get('pricing_data', {})
        
        for product_id, pricing_matrix in pricing_data.items():
            product = Product.query.get(int(product_id))
            if product and product.category == 'h-frames':
                if not product.customization_options:
                    product.customization_options = {}
                
                product.customization_options['pricing_matrix'] = pricing_matrix
                
                flag_modified(product, 'customization_options')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'H-Frames pricing updated successfully'})
    except Exception as e:
        app.logger.error(f"Admin update hframes pricing error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating hframes pricing'}), 500

@app.route('/admin_accessories_pricing')
@login_required
def admin_accessories_pricing():
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        accessory_products = Product.query.filter_by(category='accessories').all()
        pricing_data = {}
        for product in accessory_products:
            if product.customization_options and 'pricing_matrix' in product.customization_options:
                pricing_data[str(product.id)] = product.customization_options['pricing_matrix']
        
        return render_template('admin_accessories_pricing.html', accessory_products=accessory_products, pricing_data=pricing_data)
    except Exception as e:
        app.logger.error(f"Admin accessories pricing error: {e}")
        return redirect(url_for('admin_scaffoldings'))

@app.route('/admin_update_accessories_pricing', methods=['POST'])
@login_required
def admin_update_accessories_pricing():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.json
        pricing_data = data.get('pricing_data', {})
        
        for product_id, price_info in pricing_data.items():
            product = Product.query.get(int(product_id))
            if product and product.category == 'accessories':
                if not product.customization_options:
                    product.customization_options = {}
                
                product.customization_options['pricing_matrix'] = price_info
                
                flag_modified(product, 'customization_options')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Accessories pricing updated successfully'})
    except Exception as e:
        app.logger.error(f"Admin update accessories pricing error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating accessories pricing'}), 500

@app.route('/download-backup')
def download_backup():
    try:
        backup_path = '/home/runner/workspace/PROJECT_BACKUP.tar.gz'
        if os.path.exists(backup_path):
            return send_file(backup_path, as_attachment=True, download_name='national-scaffolding-backup.tar.gz', mimetype='application/gzip')
        else:
            return "Backup file not found. Please contact support.", 404
    except Exception as e:
        app.logger.error(f"Download backup error: {e}")
        return "Backup file not found. Please contact support.", 404

@app.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    """Display order details page"""
    try:
        order = Order.query.get_or_404(order_id)
        # Check authorization - admin can view any order, users can only view their own
        if session.get('user_type') == 'admin' or current_user.id == order.user_id:
            return render_template('order_details.html', order=order)
        return redirect(url_for('admin_orders'))
    except Exception as e:
        app.logger.error(f"Order details error: {e}")
        return redirect(url_for('admin_orders'))

@app.route('/verify_payment/<int:order_id>', methods=['POST'])
@login_required
def verify_payment(order_id):
    """FIXED: Admin verify payment - requires EXACT amount match"""
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        order = Order.query.get_or_404(order_id)
        data = request.json or {}
        action = data.get('action')
        
        if action == 'approve':
            # Get the amount paid from admin input
            amount_paid_str = data.get('amount_paid', '')
            
            # Validate that amount was provided
            if not amount_paid_str or str(amount_paid_str).strip() == '':
                return jsonify({
                    'success': False, 
                    'message': 'Please enter the amount paid by the customer'
                }), 400
            
            # Convert to float and validate
            try:
                amount_paid = float(amount_paid_str)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False, 
                    'message': 'Invalid amount format. Please enter a valid number.'
                }), 400
            
            # Validate amount is positive
            if amount_paid <= 0:
                return jsonify({
                    'success': False, 
                    'message': 'Amount must be greater than zero.'
                }), 400
            
            # CRITICAL FIX: Require EXACT match (not greater than or equal)
            # Round both values to 2 decimal places to avoid floating point comparison issues
            amount_paid_rounded = round(amount_paid, 2)
            order_total_rounded = round(float(order.total_price), 2)
            
            if amount_paid_rounded != order_total_rounded:
                return jsonify({
                    'success': False, 
                    'message': f'Payment verification failed: Amount paid (₹{amount_paid_rounded:.2f}) does not match order total (₹{order_total_rounded:.2f}). Please verify the exact amount with the customer.'
                }), 400
            
            # Amount matches exactly - approve the order
            order.amount_paid = amount_paid_rounded
            order.status = 'completed'
            db.session.commit()
            
            app.logger.info(f"Order {order_id} approved by admin {current_user.username}. Amount verified: ₹{amount_paid_rounded:.2f}")
            
            return jsonify({
                'success': True, 
                'message': f'Payment verified! Order #{order_id} approved for ₹{amount_paid_rounded:.2f}'
            })
        
        elif action == 'reject':
            # Get optional rejection reason
            reason = data.get('reason', 'Payment verification failed')
            
            order.status = 'rejected'
            db.session.commit()
            
            app.logger.info(f"Order {order_id} rejected by admin {current_user.username}. Reason: {reason}")
            
            return jsonify({
                'success': True, 
                'message': f'Order #{order_id} has been rejected'
            })
        
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
    except Exception as e:
        app.logger.error(f"Verify payment error for order {order_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Error verifying payment. Please try again.'
        }), 500

# Add a new route to check if payment is in progress
@app.route('/check_payment_status')
@login_required
def check_payment_status():
    """
    Always allow users to place new orders.
    Multiple pending orders are allowed.
    Admin verification is handled per order.
    """
    return jsonify({'payment_in_progress': False})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)