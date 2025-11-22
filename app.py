from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from models import db, User, Admin, Product, Order, OrderItem
import os
import qrcode
import io
import base64
# FIX: Import both datetime class and timedelta class
from datetime import datetime, timedelta 
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json
import uuid
from PIL import Image

# Load environment variables from .env file
load_dotenv()

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


# Add these routes to your app.py file

# Updated calculate_price function to handle Cuplock
def calculate_price(product, customization):
    """Enhanced calculate_price function with Cuplock support"""
    quantity = customization.get('quantity', 1)
    category = product.category
    deposit = 0
    
    if category == 'aluminium':
        # Existing aluminium logic remains the same
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
        # Existing h-frames logic remains the same
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
        # NEW: Cuplock pricing logic
        cuplock_type = customization.get('cuplockType', 'vertical')
        purchase_type = customization.get('purchaseType', 'rent')
        size = customization.get('size', '')
        
        if not product.customization_options or 'pricing_matrix' not in product.customization_options:
            # Fallback to default pricing
            return {'price': product.price, 'deposit': 0}
        
        pricing_matrix = product.customization_options['pricing_matrix']
        
        if purchase_type == 'rent':
            # Rent pricing
            if 'rent' in pricing_matrix and size in pricing_matrix['rent']:
                unit_price = pricing_matrix['rent'][size].get('price', 0)
                return {'price': unit_price, 'deposit': 0}
        else:
            # Buy pricing
            if 'buy' in pricing_matrix and size in pricing_matrix['buy']:
                buy_data = pricing_matrix['buy'][size]
                
                if cuplock_type == 'vertical':
                    # For vertical, need cup configuration
                    cup_config = customization.get('cupConfig', '')
                    if cup_config and cup_config in buy_data:
                        config_data = buy_data[cup_config]
                        weight_kg = config_data.get('weight_kg', 0)
                        price_per_kg = config_data.get('price_per_kg', 78)
                        unit_price = weight_kg * price_per_kg
                        return {'price': unit_price, 'deposit': 0}
                else:
                    # For ledger, just weight-based
                    weight_kg = buy_data.get('weight_kg', 0)
                    price_per_kg = buy_data.get('price_per_kg', 78)
                    unit_price = weight_kg * price_per_kg
                    return {'price': unit_price, 'deposit': 0}
        
        # Fallback
        return {'price': product.price, 'deposit': 0}
    
    elif category == 'accessories':
        # Existing accessories logic remains the same
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


# New route for Cuplock pricing management
@app.route('/admin_cuplock_pricing')
@login_required
def admin_cuplock_pricing():
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))
        
        # Get all cuplock products
        cuplock_products = Product.query.filter_by(category='cuplock').all()
        
        return render_template('admin_cuplock_pricing.html', cuplock_products=cuplock_products)
    except Exception as e:
        app.logger.error(f"Admin cuplock pricing error: {e}")
        return redirect(url_for('admin_scaffoldings'))


# New route to update cuplock pricing
@app.route('/admin_update_cuplock_pricing/<int:product_id>', methods=['POST'])
@login_required
def admin_update_cuplock_pricing(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        product = Product.query.get_or_404(product_id)
        
        if product.category != 'cuplock':
            return jsonify({'success': False, 'message': 'Product is not a cuplock product'}), 400
        
        data = request.json
        pricing_matrix = data.get('pricing_matrix', {})
        
        # Update the product's customization options
        if not product.customization_options:
            product.customization_options = {}
        
        product.customization_options['pricing_matrix'] = pricing_matrix
        
        # Also update the cuplock_type field if it exists
        cuplock_type = pricing_matrix.get('cuplock_type', 'vertical')
        product.cuplock_type = cuplock_type
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(product, 'customization_options')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cuplock pricing updated successfully'})
    except Exception as e:
        app.logger.error(f"Admin update cuplock pricing error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating cuplock pricing'}), 500


# New route to upload cup images
@app.route('/admin_upload_cup_image', methods=['POST'])
@login_required
def admin_upload_cup_image():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_cup_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            
            image_url = f"/static/uploads/{unique_name}"
            
            return jsonify({'success': True, 'image_url': image_url})
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
    except Exception as e:
        app.logger.error(f"Upload cup image error: {e}")
        return jsonify({'success': False, 'message': 'Error uploading image'}), 500


# Add link to admin scaffoldings page for cuplock pricing
# Add this button to your admin_scaffoldings.html template:
"""
<button class="btn-primary" onclick="window.location.href='{{ url_for('admin_cuplock_pricing') }}'">
    Manage Cuplock Pricing
</button>
"""


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
                    <p style="color: #555; margin-top: 30px; line-height: 1.6;">We will process your order shortly. You can view your order status anytime by logging into your account and visiting "My Orders" section.</p>
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
                        <li>Confirm amount matches: ₹{order.total_price:.2f}</li>
                        <li>Process order and prepare items for delivery</li>
                        <li>Contact customer if needed</li>
                    </ol>
                </div>
                <div class="footer"><p style="margin: 0;">The National Scaffolding - Admin Dashboard</p><p style="margin: 10px 0; font-size: 12px;">Log in to admin panel to view full order details</p></div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Error sending admin email: {e}")

# Initialize database and login manager BEFORE app context
db.init_app(app)
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
        db.create_all()
    except Exception as e:
        app.logger.error(f"Database creation error: {e}")

def create_default_admins():
    with app.app_context():
        try:
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
        except Exception as e:
            app.logger.error(f"Error creating default admins: {e}")
            db.session.rollback()

create_default_admins()

@app.route('/')
def index():
    try:
        category = request.args.get('category', 'all')
        if category == 'all':
            products = Product.query.filter_by(product_type='scaffolding').all()
        else:
            products = Product.query.filter_by(product_type='scaffolding', category=category).all()
        return render_template('national_scaffoldings.html', products=products, category=category)
    except Exception as e:
        app.logger.error(f"Index route error: {e}")
        return render_template('national_scaffoldings.html', products=[], category='all')

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
            
            if identifier in ['admin_scaffolding', 'admin_fabrication']:
                panel_type = 'scaffolding' if identifier == 'admin_scaffolding' else 'fabrication'
                admin = Admin.query.filter_by(username=identifier, panel_type=panel_type).first()
                if admin and admin.check_password(password):
                    login_user(admin)
                    session['user_type'] = 'admin'
                    session['panel_type'] = admin.panel_type  # Ensure panel_type is set
                    session.permanent = True  # Make session permanent
                    
                    if admin.panel_type == 'scaffolding':
                        return redirect(url_for('admin_scaffoldings'))
                    else:
                        return redirect(url_for('admin_fabrication'))
                else:
                    flash('Invalid admin credentials', 'error')
                    return render_template('login.html')
            
            # Regular user login logic remains the same
            user = User.query.filter((User.username == identifier) | (User.email == identifier) | (User.phone == identifier)).first()
            if user and user.check_password(password):
                login_user(user)
                session['user_type'] = 'user'
                session['cart'] = session.get('cart', [])
                session.permanent = True  # Make session permanent
                return redirect(url_for('dashboard'))
            
            flash('Invalid credentials', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
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
                session.permanent = True  # Make session permanent
                
                if user.panel_type == 'scaffolding':
                    return redirect(url_for('admin_scaffoldings'))
                else:
                    return redirect(url_for('admin_fabrication'))
            
            flash('Invalid admin credentials or wrong panel selected', 'error')
        except Exception as e:
            app.logger.error(f"Admin login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('admin_login.html')

@app.route('/fabrications')
def fabrications():
    try:
        products = Product.query.filter_by(product_type='fabrication').all()
        return render_template('fabrications.html', products=products)
    except Exception as e:
        app.logger.error(f"Fabrications route error: {e}")
        return render_template('fabrications.html', products=[])

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
    
@app.route('/national_scaffoldings')
def national_scaffoldings():
    try:
        category = request.args.get('category', 'all')
        if category == 'all':
            products = Product.query.filter_by(product_type='scaffolding').all()
        else:
            products = Product.query.filter_by(product_type='scaffolding', category=category).all()
        return render_template('national_scaffoldings.html', products=products, category=category)
    except Exception as e:
        app.logger.error(f"National scaffoldings error: {e}")
        return render_template('national_scaffoldings.html', products=[], category='all')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return render_template('product_detail.html', product=product)
    except Exception as e:
        app.logger.error(f"Product detail error: {e}")
        return render_template('product_detail.html', product=None)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart - FIXED for both JSON and form data"""
    try:
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
    except Exception as e:
        app.logger.error(f"Add to cart error: {e}")
        return jsonify({'success': False, 'message': 'Error adding to cart'}), 500

@app.route('/cart')
@login_required
def cart():
    """Cart page - FIXED for better handling"""
    try:
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
    except Exception as e:
        app.logger.error(f"Cart error: {e}")
        return render_template('cart.html', cart_items=[])

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

@app.route('/qr_scanner')
@login_required
def qr_scanner():
    """QR Scanner page - FIXED route without .html extension"""
    try:
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
    except Exception as e:
        app.logger.error(f"QR scanner error: {e}")
        return redirect(url_for('national_scaffoldings'))

    
@app.route('/my_orders')
@login_required
def my_orders():
    try:
        if session.get('user_type') == 'admin':
            return redirect(url_for('admin_scaffoldings'))
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
        return render_template('my_orders.html', orders=orders)
    except Exception as e:
        app.logger.error(f"My orders error: {e}")
        return render_template('my_orders.html', orders=[])


@app.route('/admin/complete_order/<int:order_id>', methods=['POST'])
@login_required
def admin_complete_order(order_id):
    """Admin function to mark an order as completed"""
    try:
        # Check if user is admin
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Check if order is in approved status
        if order.status != 'approved':
            return jsonify({'success': False, 'message': 'Only approved orders can be completed'}), 400
        
        # Update order status to completed
        order.status = 'completed'
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Order marked as completed successfully'
        })
    except Exception as e:
        app.logger.error(f"Admin complete order error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error completing order'}), 500
    
@app.route('/admin_scaffoldings')
@login_required
def admin_scaffoldings():
    try:
        if session.get('user_type') != 'admin' or session.get('panel_type') != 'scaffolding':
            return redirect(url_for('dashboard'))
        products = Product.query.filter_by(product_type='scaffolding').all()
        return render_template('admin_scaffoldings.html', products=products)
    except Exception as e:
        app.logger.error(f"Admin scaffoldings error: {e}")
        return render_template('admin_scaffoldings.html', products=[])

@app.route('/admin_fabrication')
@login_required
def admin_fabrication():
    try:
        if session.get('user_type') != 'admin' or session.get('panel_type') != 'fabrication':
            return redirect(url_for('dashboard'))
        products = Product.query.filter_by(product_type='fabr1ication').all()
        return render_template('admin_fabrication.html', products=products)
    except Exception as e:
        app.logger.error(f"Admin fabrication error: {e}")
        return render_template('admin_fabrication.html', products=[])

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
            session.clear()
            logout_user()
            flash('Admin logged out successfully', 'success')
            return redirect(url_for('national_scaffoldings'))
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Admin logout error: {e}")
        return redirect(url_for('dashboard'))

@app.route('/admin_add_product', methods=['POST'])
@login_required
def admin_add_product():
    try:
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
    except Exception as e:
        app.logger.error(f"Admin add product error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error adding product'}), 500

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

@app.route('/debug/product_images/<int:product_id>')
def debug_product_images(product_id):
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
    except Exception as e:
        app.logger.error(f"Debug product images error: {e}")
        return jsonify({'error': str(e)})

@app.route('/debug/all_products')
def debug_all_products():
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

@app.route('/debug_product_images/<int:product_id>')
def debug_product_images_simple(product_id):
    """Lightweight debugging endpoint to return stored image URLs for a product.
    Accessible without login to make quick checks easier while debugging locally.
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        images = [u for u in (product.image_url or '').split(',') if u.strip()]
        return jsonify({'success': True, 'product_id': product_id, 'image_url': product.image_url, 'images': images})
    except Exception as e:
        app.logger.error(f"Debug product images simple error: {e}")
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
        
        from sqlalchemy.orm.attributes import flag_modified
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
        db.session.delete(product)
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
                
                from sqlalchemy.orm.attributes import flag_modified
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
                
                from sqlalchemy.orm.attributes import flag_modified
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
                
                from sqlalchemy.orm.attributes import flag_modified
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

@app.route('/verify_payment/<int:order_id>', methods=['POST'])
@login_required
def verify_payment(order_id):
    try:
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
    except Exception as e:
        app.logger.error(f"Verify payment error: {e}")
        return jsonify({'success': False, 'message': 'Error verifying payment'}), 500

# Add a new route to check if payment is in progress
# (All your existing imports and helper functions like calculate_price, indian_format, etc. remain here)
# ... (Keep all the code from your original app.py up to the check_payment_status function) ...

# --- START OF CORRECTED ROUTES ---

@app.route('/check_payment_status')
@login_required
def check_payment_status():
    """Check if user has a payment in progress"""
    try:
        if session.get('user_type') == 'admin':
            return jsonify({'payment_in_progress': False})
        
        fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
        
        # Use a try-except block to handle potential database schema issues
        try:
            recent_orders = Order.query.filter(
                Order.user_id == current_user.id,
                Order.order_date >= fifteen_minutes_ago,
                Order.status.in_(['pending_verification', 'payment_initiated'])
            ).all()
        except Exception as db_error:
            # If a query fails (e.g., due to a missing column), log it and rollback the session
            app.logger.error(f"Database query failed in check_payment_status: {db_error}")
            db.session.rollback()
            # As a safe fallback, assume no payment is in progress
            return jsonify({'payment_in_progress': False})
        
        return jsonify({'payment_in_progress': len(recent_orders) > 0})
    except Exception as e:
        app.logger.error(f"Check payment status error: {e}")
        return jsonify({'payment_in_progress': False})

@app.route('/complete_order', methods=['POST'])
@login_required
def complete_order():
    """Complete order after payment - FIXED"""
    try:
        if session.get('user_type') == 'admin':
            return jsonify({'success': False, 'message': 'Admins cannot place orders'}), 403
        
        cart_items = session.get('cart', [])
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        data = request.json or {}
        transaction_id = data.get('transaction_id', '').strip()
        
        if not transaction_id or len(transaction_id) < 12:
            return jsonify({
                'success': False, 
                'message': 'Valid Transaction ID is required (minimum 12 characters)'
            }), 400
        
        # Check if transaction ID already exists using raw SQL to avoid column issues
        try:
            result = db.session.execute(
                db.text("SELECT id FROM orders WHERE transaction_id = :transaction_id"),
                {"transaction_id": transaction_id}
            ).fetchone()
            
            if result:
                return jsonify({
                    'success': False, 
                    'message': 'This Transaction ID has already been used. Each purchase requires a unique payment. Please make a new payment and enter a new Transaction ID.'
                }), 400
        except Exception as e:
            app.logger.error(f"Error checking transaction ID: {e}")
            return jsonify({
                'success': False, 
                'message': 'Error validating transaction ID. Please try again.'
            }), 500
        
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
        
        # Create order without payment_time field
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
    except Exception as e:
        app.logger.error(f"Complete order error: {e}")
        # Rollback the transaction to handle the InFailedSqlTransaction error
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error placing order. Please try again.'}), 500


        from app import app
from models import db
import os

def add_payment_time_column():
    with app.app_context():
        try:
            # Check if the column already exists
            result = db.session.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = 'payment_time'
            """)).fetchone()
            
            if not result:
                # Add the payment_time column if it doesn't exist
                db.session.execute(db.text("""
                    ALTER TABLE orders 
                    ADD COLUMN payment_time TIMESTAMP
                """))
                db.session.commit()
                print("Added payment_time column to orders table")
            else:
                print("payment_time column already exists")
                
        except Exception as e:
            print(f"Error adding payment_time column: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_payment_time_column()

# --- END OF CORRECTED ROUTES ---


# (Keep all the remaining routes from your original app.py, e.g., my_orders, admin_*, etc.)
# ...



if __name__ == '__main__':
    app.jinja_env.filters['indian'] = indian_format
    app.run(host='0.0.0.0', port=5001, debug=True)