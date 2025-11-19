from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from models import db, User, Admin, Product, Order, OrderItem
import os
import qrcode
import io
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json
import uuid
from PIL import Image

# Load environment variables from .env file
load_dotenv()

def calculate_price(product, customization):
    quantity = customization.get('quantity', 1)
    category = product.category
    deposit = 0
    
    if category == 'aluminium':
        purchase_type = customization.get('purchaseType', 'buy')
        width = str(customization.get('width', ''))
        height = str(customization.get('height', ''))
        
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_matrix = product.customization_options['pricing_matrix']
            if width in pricing_matrix and height in pricing_matrix[width]:
                price_data = pricing_matrix[width][height]
                
                if isinstance(price_data, dict):
                    if purchase_type == 'rent':
                        unit_price = price_data.get('rent')
                        if unit_price is None and 'buy' in price_data:
                            unit_price = price_data['buy'] * 0.2
                        deposit = price_data.get('deposit', product.deposit_amount if product.deposit_amount else 0)
                    else:
                        unit_price = price_data.get('buy', product.price)
                    
                    if purchase_type == 'rent':
                        deposit = price_data.get('deposit', product.deposit_amount if product.deposit_amount else 0)
                        
                    return {'price': unit_price, 'deposit': deposit}
                else:
                    buy_price = price_data
                    unit_price = (buy_price * 0.2) if purchase_type == 'rent' else buy_price
                    if purchase_type == 'rent':
                        deposit = product.deposit_amount if product.deposit_amount else 0
                    return {'price': unit_price, 'deposit': deposit}
        
        if purchase_type == 'rent':
            unit_price = product.rent_price if product.rent_price else product.price
            deposit = product.deposit_amount if product.deposit_amount else 0
        else:
            unit_price = product.price
        return {'price': unit_price, 'deposit': deposit}
    
    elif category == 'h-frames':
        purchase_type = customization.get('purchaseType', 'buy')
        
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_matrix = product.customization_options['pricing_matrix']
            quantity_key = str(quantity)
            
            if quantity_key in pricing_matrix:
                price_data = pricing_matrix[quantity_key]
                
                if isinstance(price_data, dict):
                    if purchase_type == 'rent':
                        unit_price = price_data.get('rent', product.rent_price if product.rent_price else product.price * 0.2)
                        deposit = price_data.get('deposit', product.deposit_amount if product.deposit_amount else 0)
                    else:
                        unit_price = price_data.get('buy', product.price)

                    if purchase_type == 'rent':
                        deposit = price_data.get('deposit', product.deposit_amount if product.deposit_amount else 0)
                        
                    return {'price': unit_price, 'deposit': deposit}
                else:
                    buy_price = price_data
                    unit_price = (buy_price * 0.2) if purchase_type == 'rent' else buy_price
                    if purchase_type == 'rent':
                        deposit = product.deposit_amount if product.deposit_amount else 0
                    return {'price': unit_price, 'deposit': deposit}
        
        if purchase_type == 'rent':
            unit_price = product.rent_price if product.rent_price else product.price
            deposit = product.deposit_amount if product.deposit_amount else 0
        else:
            unit_price = product.price
        return {'price': unit_price, 'deposit': deposit}
    
    elif category == 'cuplock':
        price_per_kg = 78
        weight = product.weight_per_unit if product.weight_per_unit else 5
        return {'price': price_per_kg * weight, 'deposit': 0}
    
    elif category == 'accessories':
        purchase_type = customization.get('purchaseType', 'buy')
        
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_matrix = product.customization_options['pricing_matrix']
            
            if isinstance(pricing_matrix, dict):
                if purchase_type == 'rent':
                    unit_price = pricing_matrix.get('rent', product.rent_price if product.rent_price else product.price * 0.2)
                    deposit = pricing_matrix.get('deposit', product.deposit_amount if product.deposit_amount else 0)
                else:
                    unit_price = pricing_matrix.get('buy', product.price)

                if purchase_type == 'rent':
                    deposit = pricing_matrix.get('deposit', product.deposit_amount if product.deposit_amount else 0)

                return {'price': unit_price, 'deposit': deposit}
            else:
                buy_price = pricing_matrix
                unit_price = (buy_price * 0.2) if purchase_type == 'rent' else buy_price
                if purchase_type == 'rent':
                    deposit = product.deposit_amount if product.deposit_amount else 0
                return {'price': unit_price, 'deposit': deposit}
        
        if purchase_type == 'rent':
            unit_price = product.rent_price if product.rent_price else product.price
            deposit = product.deposit_amount if product.deposit_amount else 0
        else:
            unit_price = product.price
        return {'price': unit_price, 'deposit': deposit}
    
    else:
        return {'price': product.price, 'deposit': 0}

app = Flask(__name__)

# Configure basic logging for debugging
import logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

if not os.environ.get('SESSION_SECRET'):
    os.environ['SESSION_SECRET'] = 'dev-secret-key-change-in-production'

app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET')

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

def send_order_confirmation_email(user, order, order_items):
    if not app.config['MAIL_USERNAME']:
        return
    
    try:
        items_html = ""
        for item in order_items:
            price_data = calculate_price(Product.query.get(item.product_id), item.customization or {})
            unit_price = price_data['price']
            item_total = unit_price * item.quantity
            
            items_html += f"""
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 15px; color: #333;">{item.product_name}</td>
                <td style="padding: 15px; text-align: center; color: #333;">{item.quantity}</td>
                <td style="padding: 15px; text-align: center; color: #333;">₹{unit_price:.2f}</td>
                <td style="padding: 15px; text-align: right; color: #333;">₹{item_total:.2f}</td>
            </tr>
            """
        
        msg = Message(
            subject='Order Confirmation - The National Scaffolding',
            recipients=[user.email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>body {{ font-family: 'Poppins', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a8a, #d4af37); padding: 30px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
            .content {{ padding: 30px; }}
            .order-details {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .order-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .order-table th {{ background-color: #1e3a8a; color: #ffffff; padding: 12px; text-align: left; }}
            .order-table td {{ padding: 15px; color: #333; }}
            .total-row {{ background-color: #1e3a8a; color: #ffffff; font-weight: bold; }}
            .footer {{ background-color: #1e3a8a; color: #ffffff; padding: 20px; text-align: center; font-size: 14px; }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header"><h1>✓ Order Confirmed!</h1><p style="color: #ffffff; margin: 10px 0 0;">Thank you for your order</p></div>
                <div class="content">
                    <h2 style="color: #1e3a8a;">Dear {user.full_name or user.username},</h2>
                    <p style="color: #555; line-height: 1.6;">Thank you for choosing The National Scaffolding! Your order has been successfully placed and confirmed.</p>
                    <div class="order-details">
                        <h3 style="color: #1e3a8a;">Order Details</h3>
                        <p style="margin: 5px 0; color: #555;"><strong>Order ID:</strong> #{order.id}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Order Date:</strong> {order.order_date.strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Transaction ID:</strong> <span style="font-family: monospace; background-color: #e8f5e9; padding: 3px 8px; border-radius: 4px;">{order.transaction_id}</span></p>
                        <p style="margin: 5px 0; color: #555;"><strong>Total Amount:</strong> <span style="color: #4CAF50; font-size: 18px; font-weight: bold;">₹{order.total_price:.2f}</span></p>
                    </div>
                    <h3 style="color: #1e3a8a;">Order Items</h3>
                    <table class="order-table">
                        <thead><tr><th style="padding: 15px;">Product</th><th style="padding: 15px; text-align: center;">Quantity</th><th style="padding: 15px; text-align: center;">Unit Price</th><th style="padding: 15px; text-align: right;">Item Total</th></tr></thead>
                        <tbody>{items_html}
                            <tr class="total-row"><td colspan="3" style="padding: 15px; text-align: right;">Total Amount:</td><td style="padding: 15px; text-align: right;">₹{order.total_price:.2f}</td></tr>
                        </tbody>
                    </table>
                    <p style="color: #555; margin-top: 30px; line-height: 1.6;">We will process your order shortly. You can view your order status anytime by logging into your account and visiting the "My Orders" section.</p>
                    <p style="color: #555; margin-top: 20px;">If you have any questions, please don't hesitate to contact us.</p>
                </div>
                <div class="footer"><p style="margin: 0;">© 2025 The National Scaffolding. All rights reserved.</p><p style="margin: 10px 0 0;">Quality scaffolding solutions for your construction needs</p></div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Error sending customer email: {e}")

def send_admin_notification_email(order, user, order_items):
    if not app.config['MAIL_USERNAME']:
        return
    
    admin_email = os.environ.get('ADMIN_EMAIL', app.config['MAIL_DEFAULT_SENDER'])
    
    try:
        items_text = ""
        for item in order_items:
            price_data = calculate_price(Product.query.get(item.product_id), item.customization or {})
            unit_price = price_data['price']
            items_text += f"- {item.product_name} x {item.quantity} @ ₹{unit_price:.2f} = ₹{(unit_price * item.quantity):.2f}\n"
        
        msg = Message(
            subject=f'🔔 New Order #{order.id} - The National Scaffolding',
            recipients=[admin_email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>body {{ font-family: 'Poppins', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #d4af37, #1e3a8a); padding: 30px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
            .content {{ padding: 30px; }}
            .alert-box {{ background-color: #fff3cd; border-left: 4px solid #d4af37; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .customer-info {{ background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .order-items {{ background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ background-color: #1e3a8a; color: #ffffff; padding: 20px; text-align: center; font-size: 14px; }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header"><h1>🔔 New Order Received!</h1><p style="color: #ffffff; margin: 10px 0 0;">Order #{order.id}</p></div>
                <div class="content">
                    <div class="alert-box"><p style="margin: 0; color: #856404; font-weight: bold;">⚠️ Action Required: Please verify payment and process this order</p></div>
                    <h3 style="color: #1e3a8a;">Order Information</h3>
                    <p style="color: #555;"><strong>Order ID:</strong> #{order.id}</p>
                    <p style="color: #555;"><strong>Order Date:</strong> {order.order_date.strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p style="color: #555;"><strong>Transaction ID:</strong> <span style="font-family: monospace; background-color: #e8f5e9; padding: 3px 8px; border-radius: 4px;">{order.transaction_id}</span></p>
                    <p style="color: #555;"><strong>Total Amount:</strong> <span style="color: #4CAF50; font-size: 20px; font-weight: bold;">₹{order.total_price:.2f}</span> (incl. 18% GST)</p>
                    <div class="customer-info">
                        <h3 style="color: #1e3a8a;">Customer Details</h3>
                        <p style="color: #555;"><strong>Name:</strong> {user.full_name or user.username}</p>
                        <p style="color: #555;"><strong>Email:</strong> {user.email}</p>
                        <p style="color: #555;"><strong>Phone:</strong> {user.phone or 'N/A'}</p>
                        {f'<p style="margin: 5px 0; color: #555;"><strong>Address:</strong> {user.address}</p>' if user.address else ''}
                        {f'<p style="margin: 5px 0; color: #555;"><strong>Organization:</strong> {user.organization}</p>' if user.organization else ''}
                    </div>
                    <div class="order-items">
                        <h3 style="color: #1e3a8a;">Order Items</h3>
                        <pre style="background-color: #ffffff; padding: 10px; border-radius: 4px; overflow-x: auto; color: #333;">{items_text}</pre>
                    </div>
                    <p style="color: #555; margin-top: 20px;"><strong>Next Steps:</strong></p>
                    <ol style="color: #555; line-height: 1.8;">
                        <li>Verify transaction ID in your PhonePe account</li>
                        <li>Confirm the amount matches: ₹{order.total_price:.2f}</li>
                        <li>Process the order and prepare items for delivery</li>
                        <li>Contact the customer if needed</li>
                    </ol>
                </div>
                <div class="footer"><p style="margin: 0;">The National Scaffolding - Admin Dashboard</p><p style="margin: 10px 0; font-size: 12px;">Log in to the admin panel to view full order details</p></div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Error sending admin email: {e}")

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if session.get('user_type') == 'admin':
        return Admin.query.get(int(user_id))
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

def create_default_admins():
    with app.app_context():
        admin_scaffolding = Admin.query.filter_by(username='admin_scaffolding').first()
        admin_fabrication = Admin.query.filter_by(username='admin_fabrication').first()
        
        if not admin_scaffolding:
            admin_scaffolding = Admin(username='admin_scaffolding', panel_type='scaffolding')
            admin_scaffolding.set_password('admin123')
            db.session.add(admin_scaffolding)
        
        if not admin_fabrication:
            admin_fabrication = Admin(username='admin_fabrication', panel_type='fabrication')
            admin_fabrication.set_password('admin123')
            db.session.add(admin_fabrication)
        
        db.session.commit()

create_default_admins()

@app.route('/')
def index():
    category = request.args.get('category', 'all')
    if category == 'all':
        products = Product.query.filter_by(product_type='scaffolding').all()
    else:
        products = Product.query.filter_by(product_type='scaffolding', category=category).all()
    return render_template('national_scaffoldings.html', products=products, category=category)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        if identifier in ['admin_scaffolding', 'admin_fabrication']:
            panel_type = 'scaffolding' if identifier == 'admin_scaffolding' else 'fabrication'
            admin = Admin.query.filter_by(username=identifier, panel_type=panel_type).first()
            if admin and admin.check_password(password):
                login_user(admin)
                session['user_type'] = 'admin'
                session['panel_type'] = admin.panel_type
                
                if admin.panel_type == 'scaffolding':
                    return redirect(url_for('admin_scaffoldings'))
                else:
                    return redirect(url_for('admin_fabrication'))
            else:
                flash('Invalid admin credentials', 'error')
                return render_template('login.html')
        
        user = User.query.filter((User.username == identifier) | (User.email == identifier) | (User.phone == identifier)).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_type'] = 'user'
            session['cart'] = session.get('cart', [])
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        panel_type = request.form.get('panel_type')
        
        if not panel_type:
            flash('Please select an admin panel', 'error')
            return render_template('admin_login.html')
        
        user = Admin.query.filter_by(username=identifier, panel_type=panel_type).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_type'] = 'admin'
            session['panel_type'] = user.panel_type
            if user.panel_type == 'scaffolding':
                return redirect(url_for('admin_scaffoldings'))
            else:
                return redirect(url_for('admin_fabrication'))
        
        flash('Invalid admin credentials or wrong panel selected', 'error')
    
    return render_template('admin_login.html')
@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_type') == 'admin':
        return redirect(url_for('admin_scaffoldings'))
    return render_template('dashboard.html')

@app.route('/national_scaffoldings')
def national_scaffoldings():
    category = request.args.get('category', 'all')
    if category == 'all':
        products = Product.query.filter_by(product_type='scaffolding').all()
    else:
        products = Product.query.filter_by(product_type='scaffolding', category=category).all()
    return render_template('national_scaffoldings.html', products=products, category=category)

@app.route('/fabrications')
def fabrications():
    products = Product.query.filter_by(product_type='fabrication').all()
    return render_template('fabrications.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart - FIXED for both JSON and form data"""
    if session.get('user_type') == 'admin':
        return jsonify({'success': False, 'message': 'Admins cannot purchase items'}), 403
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
        
        # Convert customization from string to dict if needed
        if 'customization' in data and isinstance(data['customization'], str):
            try:
                data['customization'] = json.loads(data['customization'])
            except json.JSONDecodeError:
                data['customization'] = {}
    
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    customization = data.get('customization', {})
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive integer'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    customization['quantity'] = quantity
    
    if product.category == 'h-frames' and quantity >= 100:
        return jsonify({
            'success': False, 
            'message': 'For orders of 100+ pieces, please contact us directly at sales@nationalscaffolding.com'
        }), 400
    
    price_data = calculate_price(product, customization)
    if price_data is None:
        return jsonify({'success': False, 'message': 'Cannot calculate price for this configuration'}), 400
    
    cart = session.get('cart', [])
    cart_item = {
        'product_id': product_id, 
        'product_name': product.name, 
        'quantity': quantity, 
        'customization': customization,
        'image_url': product.image_url  # Added this line for cart display
    }
    cart.append(cart_item)
    session['cart'] = cart
    session.modified = True
    
    app.logger.info(f"User {current_user.id} added product {product_id} to cart. Cart size: {len(cart)}")
    
    return jsonify({
        'success': True, 
        'cart_count': len(cart),
        'message': 'Product added to cart successfully'
    }), 200

@app.route('/cart')
@login_required
def cart():
    """Cart page - FIXED for better handling"""
    if session.get('user_type') == 'admin':
        flash('Admins cannot make purchases', 'warning')
        return redirect(url_for('admin_scaffoldings'))
    
    cart_items = session.get('cart', [])
    enriched_cart = []
    total_items_price = 0
    total_deposit = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            price_data = calculate_price(product, item['customization'])
            if price_data is not None:
                unit_price = price_data['price']
                deposit = price_data['deposit']
                item_price = unit_price * item['quantity']
                item_deposit = deposit * item['quantity'] if deposit > 0 else 0
                
                total_items_price += item_price
                total_deposit += item_deposit
                
                custom_info = item['customization']
                if 'purchaseType' not in custom_info:
                    custom_info['purchaseType'] = 'buy'
                
                enriched_item = {
                    'product_name': product.name, 
                    'quantity': item['quantity'], 
                    'unit_price': unit_price, 
                    'deposit': deposit,
                    'item_total': item_price, 
                    'item_deposit': item_deposit, 
                    'customization': custom_info, 
                    'image_url': product.image_url
                }
                enriched_cart.append(enriched_item)
    
    total_before_gst = total_items_price + total_deposit
    gst = total_items_price * 0.18
    total_with_gst = total_before_gst + gst
    
    return render_template(
        'cart.html', 
        cart_items=enriched_cart, 
        total_before_gst=total_items_price, 
        total_deposit=total_deposit, 
        gst=gst, 
        total_with_gst=total_with_gst
    )

@app.route('/remove_from_cart/<int:index>')
@login_required
def remove_from_cart(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/qr_scanner')
@login_required
def qr_scanner():
    """QR Scanner page - FIXED route without .html extension"""
    if session.get('user_type') == 'admin':
        flash('Admins cannot make purchases', 'warning')
        return redirect(url_for('admin_scaffoldings'))
    
    cart_items = session.get('cart', [])
    
    if not cart_items:
        flash('Your cart is empty. Please add items before proceeding to payment.', 'warning')
        return redirect(url_for('national_scaffoldings'))
    
    total_items_price = 0
    total_deposit = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            price_data = calculate_price(product, item['customization'])
            if price_data is not None:
                total_items_price += price_data['price'] * item['quantity']
                total_deposit += price_data['deposit'] * item['quantity'] if price_data['deposit'] > 0 else 0
    
    gst = total_items_price * 0.18
    total_with_gst = total_items_price + gst + total_deposit
    
    # Generate QR code for payment
    qr_data = f"upi://pay?pa=nationalscaffolding@phonepe&pn=The National Scaffolding&am={total_with_gst:.2f}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template(
        'qr_scanner.html', 
        total=total_items_price, 
        gst=gst, 
        total_deposit=total_deposit, 
        total_with_gst=total_with_gst, 
        qr_code=qr_code_base64,
        cart_items=cart_items
    )

@app.route('/complete_order', methods=['POST'])
@login_required
def complete_order():
    """Complete order after payment - FIXED"""
    if session.get('user_type') == 'admin':
        return jsonify({'success': False, 'message': 'Admins cannot place orders'}), 403
    
    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    data = request.json or {}
    transaction_id = data.get('transaction_id', '').strip()
    
    if not transaction_id or len(transaction_id) < 8:
        return jsonify({
            'success': False, 
            'message': 'Valid Transaction ID is required (minimum 8 characters)'
        }), 400
    
    existing_order = Order.query.filter_by(transaction_id=transaction_id).first()
    if existing_order:
        return jsonify({
            'success': False, 
            'message': 'This Transaction ID has already been used. Each purchase requires a unique payment. Please make a new payment and enter a new Transaction ID.'
        }), 400
    
    total_items_price = 0
    total_deposit = 0
    order_items_list = []
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            price_data = calculate_price(product, item['customization'])
            if price_data is not None:
                unit_price = price_data['price']
                deposit = price_data['deposit']
                total_items_price += unit_price * item['quantity']
                total_deposit += deposit * item['quantity'] if deposit > 0 else 0
                
                order_items_list.append({
                    'product': product, 
                    'quantity': item['quantity'], 
                    'unit_price': unit_price, 
                    'customization': item.get('customization', {})
                })
    
    gst = total_items_price * 0.18
    total_with_gst = total_items_price + gst + total_deposit
    
    order = Order(
        user_id=current_user.id, 
        total_price=total_with_gst, 
        status='pending_verification', 
        transaction_id=transaction_id, 
        amount_paid=0
    )
    db.session.add(order)
    db.session.flush()
    
    final_order_items = []
    for item_data in order_items_list:
        order_item = OrderItem(
            order_id=order.id, 
            product_id=item_data['product'].id, 
            product_name=item_data['product'].name,
            quantity=item_data['quantity'], 
            price=item_data['unit_price'], 
            customization=item_data['customization']
        )
        db.session.add(order_item)
        final_order_items.append(order_item)

    db.session.commit()
    
    # Clear cart after successful order
    session['cart'] = []
    session.modified = True
    
    # Send confirmation emails
    try:
        send_order_confirmation_email(current_user, order, final_order_items)
        send_admin_notification_email(order, current_user, final_order_items)
    except Exception as e:
        app.logger.error(f"Error sending order emails: {e}")
    
    return jsonify({
        'success': True, 
        'order_id': order.id,
        'message': 'Order placed successfully!'
    }), 200

@app.route('/my_orders')
@login_required
def my_orders():
    if session.get('user_type') == 'admin':
        return redirect(url_for('admin_scaffoldings'))
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/admin_scaffoldings')
@login_required
def admin_scaffoldings():
    if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
        return redirect(url_for('dashboard'))
    products = Product.query.filter_by(product_type='scaffolding').all()
    return render_template('admin_scaffoldings.html', products=products)

@app.route('/admin_fabrication')
@login_required
def admin_fabrication():
    if session.get('user_type') != 'admin' or session.get('panel_type') != 'fabrication':
        return redirect(url_for('dashboard'))
    products = Product.query.filter_by(product_type='fabrication').all()
    return render_template('admin_fabrication.html', products=products)

@app.route('/admin_orders')
@login_required
def admin_orders():
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

@app.route('/admin_analytics')
@login_required
def admin_analytics():
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
        
        for item in order.items:
            category = item.product.category or 'Other'
            if category not in category_data:
                category_data[category] = {'revenue': 0, 'quantity': 0}
            
            price_data = calculate_price(item.product, item.customization or {})
            unit_price = price_data['price']
            category_data[category]['revenue'] += unit_price * item.quantity 
            category_data[category]['quantity'] += item.quantity
    
    sorted_months = sorted(monthly_data.keys())
    total_revenue = sum(order.total_price for order in orders)
    total_orders = len(orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    return render_template('admin_analytics.html', monthly_data=monthly_data, yearly_data=yearly_data, category_data=category_data, sorted_months=sorted_months, total_revenue=total_revenue, total_orders=total_orders, avg_order_value=avg_order_value)

@app.route('/admin_logout')
@login_required
def admin_logout():
    if session.get('user_type') == 'admin':
        session.clear()
        logout_user()
        flash('Admin logged out successfully', 'success')
        return redirect(url_for('national_scaffoldings'))
    return redirect(url_for('dashboard'))

@app.route('/admin_add_product', methods=['POST'])
@login_required
def admin_add_product():
    if session.get('user_type') != 'admin':
        return jsonify({'success': False}), 403
    
    image_urls = []
    saved_filepaths = []
    uploaded_files = request.files.getlist('product_images') if request.files else []

    # Save uploads first and validate files exist on disk before creating DB record
    if uploaded_files:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                try:
                    file.save(filepath)
                    saved_filepaths.append(filepath)
                    image_urls.append(f"/static/uploads/{unique_name}")
                    app.logger.info(f"Saved uploaded file for new product: {filepath}")
                except Exception as e:
                    app.logger.error(f"Error saving uploaded file: {e}")

        # Validate saved files exist
        for p in saved_filepaths:
            try:
                if not os.path.exists(p):
                    raise FileNotFoundError(p)
                with Image.open(p) as im:
                    im.verify()
            except Exception as e:
                for q in saved_filepaths:
                    try:
                        if os.path.exists(q):
                            os.remove(q)
                    except Exception:
                        pass
                app.logger.error(f"Uploaded image validation failed for new product: {e}")
                return jsonify({'success': False, 'message': 'One or more uploaded images are invalid or corrupted. Please try different files.'}), 500

    # Join with comma - NO SPACES
    image_url_string = ",".join(image_urls) if image_urls else None
    
    # DEBUG LOG
    app.logger.info(f"Creating product with images: {image_url_string}")

    # Create product
    product = Product(
        name=request.form.get('name'),
        price=safe_float(request.form.get('price')) or 0.0,
        description=request.form.get('description', ''),
        category=request.form.get('category'),
        product_type=request.form.get('product_type'),
        customization_options=None,
        rent_price=safe_float(request.form.get('rent_price')),
        deposit_amount=safe_float(request.form.get('deposit_amount')),
        image_url=image_url_string,
        weight_per_unit=safe_float(request.form.get('weight_per_unit'))
    )

    db.session.add(product)
    db.session.flush()

    pricing_matrix_str = request.form.get('pricing_matrix')
    if pricing_matrix_str:
        try:
            pm = json.loads(pricing_matrix_str)
            product.customization_options = product.customization_options or {}
            product.customization_options['pricing_matrix'] = pm
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(product, 'customization_options')
        except Exception as e:
            app.logger.error('Failed to parse pricing_matrix: %s', e)

    db.session.commit()

    app.logger.info(f"New product created id={product.id} image_url={product.image_url}")
    return jsonify({'success': True, 'product_id': product.id})

# In app.py, fix the admin_update_product function:

@app.route('/admin_update_product/<int:product_id>', methods=['POST'])
@login_required
def admin_update_product(product_id):
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
                    new_urls.append(f"/static/uploads/{unique_name}")
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
        old_image_path = img.replace('/static/', 'static/')
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                app.logger.info(f"Removed old image file for product {product_id}: {old_image_path}")
            except Exception as e:
                app.logger.warning(f"Error removing old file {old_image_path}: {e}")

    merged_urls = existing_list + new_urls
    product.image_url = ','.join(merged_urls) if merged_urls else None
    
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
    
    pricing_matrix_str = request.form.get('pricing_matrix')
    if pricing_matrix_str is not None:
        try:
            pricing_matrix_data = json.loads(pricing_matrix_str)
            product.customization_options = product.customization_options or {}
            product.customization_options['pricing_matrix'] = pricing_matrix_data
            from sqlalchemy.orm.attributes import flag_modified
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

@app.route('/admin_get_product_pricing/<int:product_id>')
@login_required
def admin_get_product_pricing(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    pricing = {}
    if product.customization_options and 'pricing_matrix' in product.customization_options:
        pricing = product.customization_options['pricing_matrix']
    
    return jsonify({'success': True, 'pricing_matrix': pricing})

@app.route('/debug/images')
def debug_images_page():
    return render_template('debug_images.html')

@app.route('/debug/product_images/<int:product_id>')
def debug_product_images(product_id):
    """Debug route to see exactly what images are stored"""
    product = Product.query.get_or_404(product_id)
    
    debug_info = {
        'product_id': product_id,
        'product_name': product.name,
        'raw_image_url': product.image_url,
        'images': []
    }
    
    if product.image_url:
        images = [img.strip() for img in product.image_url.split(',')]
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

@app.route('/debug/all_products')
def debug_all_products():
    """Debug route to see all products and their images - FIXED"""
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

@app.route('/debug/product/<int:product_id>/images')
def debug_product_images_detail(product_id):
    """Debug route to see exactly what images are stored"""
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

@app.route('/debug_product_images/<int:product_id>')
def debug_product_images_simple(product_id):
    """Lightweight debugging endpoint to return stored image URLs for a product.
    Accessible without login to make quick checks easier while debugging locally.
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    images = [u for u in (product.image_url or '').split(',') if u.strip()]
    return jsonify({'success': True, 'product_id': product_id, 'image_url': product.image_url, 'images': images})

@app.route('/api/product/<int:product_id>/images')
def api_product_images(product_id):
    """API endpoint to get product images - useful for debugging"""
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

@app.route('/admin_image_diagnostics')
@login_required
def admin_image_diagnostics():
    """Admin endpoint to check image health across all products.
    Returns detailed diagnostics for every image stored in the system.
    """
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

@app.route('/admin_image_diagnostics/product/<int:product_id>')
@login_required
def admin_image_diagnostics_product(product_id):
    """Admin endpoint to check image health for a specific product.
    Returns detailed diagnostics for all images of that product.
    """
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

@app.route('/admin_update_pricing_matrix/<int:product_id>', methods=['POST'])
@login_required
def admin_update_pricing_matrix(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    
    if not product.customization_options:
        product.customization_options = {}
    
    data = request.json
    pricing_matrix = data.get('pricing_matrix', {})
    
    product.customization_options['pricing_matrix'] = pricing_matrix
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(product, 'customization_options')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Pricing matrix updated successfully'})

@app.route('/admin_remove_photo/<int:product_id>', methods=['POST'])
@login_required
def admin_remove_photo(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({'success': False, 'message': 'No image_url provided'}), 400

    current = [u for u in (product.image_url or '').split(',') if u.strip()]
    if image_url in current:
        old_image_path = image_url.replace('/static/', 'static/')
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                app.logger.info(f"Removed image file: {old_image_path}")
            except Exception as e:
                app.logger.error(f"Error removing file: {e}")

        current.remove(image_url)
        product.image_url = ','.join(current) if current else None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Photo removed successfully'})

    return jsonify({'success': False, 'message': 'Image not found on product'}), 404

@app.route('/admin_delete_product/<int:product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False}), 403
    
    product = Product.query.get_or_404(product_id)
    
    if product.image_url:
        image_paths = product.image_url.split(',')
        for img_path in image_paths:
            old_image_path = img_path.strip().replace('/static/', 'static/')
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    app.logger.info(f"Deleted image file: {old_image_path}")
                except Exception as e:
                    app.logger.error(f"Error removing file: {e}")
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin_pricing_matrix/<int:product_id>')
@login_required
def admin_pricing_matrix(product_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    product = Product.query.get_or_404(product_id)
    
    if product.category not in ['aluminium', 'h-frames', 'accessories']:
        flash('Pricing matrix customization is only available for Aluminium, H-Frames, and Accessories products', 'warning')
        return redirect(url_for('admin_scaffoldings'))
    
    pricing_matrix = product.customization_options.get('pricing_matrix', {}) if product.customization_options else {}
    
    return render_template('admin_pricing_matrix.html', product=product, pricing_matrix=pricing_matrix)

@app.route('/admin_aluminium_pricing')
@login_required
def admin_aluminium_pricing():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    aluminium_products = Product.query.filter_by(category='aluminium').all()
    pricing_data = {}
    for product in aluminium_products:
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_data[str(product.id)] = product.customization_options['pricing_matrix']
    
    return render_template('admin_aluminium_pricing.html', aluminium_products=aluminium_products, pricing_data=pricing_data)

@app.route('/admin_update_aluminium_pricing', methods=['POST'])
@login_required
def admin_update_aluminium_pricing():
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
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(product, 'customization_options')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Aluminium pricing updated successfully'})

@app.route('/admin_hframes_pricing')
@login_required
def admin_hframes_pricing():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    hframe_products = Product.query.filter_by(category='h-frames').all()
    pricing_data = {}
    for product in hframe_products:
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_data[str(product.id)] = product.customization_options['pricing_matrix']
    
    return render_template('admin_hframes_pricing.html', hframe_products=hframe_products, pricing_data=pricing_data)

@app.route('/admin_update_hframes_pricing', methods=['POST'])
@login_required
def admin_update_hframes_pricing():
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
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(product, 'customization_options')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'H-Frames pricing updated successfully'})

@app.route('/admin_accessories_pricing')
@login_required
def admin_accessories_pricing():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    accessory_products = Product.query.filter_by(category='accessories').all()
    pricing_data = {}
    for product in accessory_products:
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_data[str(product.id)] = product.customization_options['pricing_matrix']
    
    return render_template('admin_accessories_pricing.html', accessory_products=accessory_products, pricing_data=pricing_data)

@app.route('/admin_update_accessories_pricing', methods=['POST'])
@login_required
def admin_update_accessories_pricing():
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
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(product, 'customization_options')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Accessories pricing updated successfully'})

@app.route('/download-backup')
def download_backup():
    backup_path = '/home/runner/workspace/PROJECT_BACKUP.tar.gz'
    if os.path.exists(backup_path):
        return send_file(backup_path, as_attachment=True, download_name='national-scaffolding-backup.tar.gz', mimetype='application/gzip')
    else:
        return "Backup file not found. Please contact support.", 404

@app.route('/verify_payment/<int:order_id>', methods=['POST'])
@login_required
def verify_payment(order_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    order = Order.query.get_or_404(order_id)
    data = request.json or {}
    action = data.get('action')
    
    if action == 'approve':
        try:
            amount_paid = float(data.get('amount_paid', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid amount format. Please enter a valid number.'})
        
        if amount_paid <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero.'})
        
        if amount_paid < order.total_price:
            return jsonify({'success': False, 'message': f'Amount paid (₹{amount_paid:.2f}) is less than required (₹{order.total_price:.2f})'})
        
        order.amount_paid = amount_paid
        order.status = 'completed'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payment verified and order approved'})
    
    elif action == 'reject':
        order.status = 'rejected'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order rejected'})
    
    return jsonify({'success': False, 'message': 'Invalid action'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)