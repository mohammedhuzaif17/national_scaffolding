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

# Load environment variables from .env file
load_dotenv()

def calculate_price(product, customization):
    quantity = customization.get('quantity', 1)
    category = product.category
    
    if category == 'aluminium':
        purchase_type = customization.get('purchaseType', 'buy')
        width = str(customization.get('width', ''))
        height = str(customization.get('height', ''))
        
        # Try to get price from pricing matrix in database
        if product.customization_options and 'pricing_matrix' in product.customization_options:
            pricing_matrix = product.customization_options['pricing_matrix']
            if width in pricing_matrix and height in pricing_matrix[width]:
                buy_price = pricing_matrix[width][height]
                # Rent price is 20% of buy price
                unit_price = (buy_price * 0.2) if purchase_type == 'rent' else buy_price
                return unit_price
        
        # Fallback to base price if no matrix or combination not found
        if purchase_type == 'rent':
            unit_price = product.rent_price if product.rent_price else product.price
        else:
            unit_price = product.price
        return unit_price
    
    elif category == 'h-frames':
        discount_rate = 0
        if quantity >= 100:
            return None
        elif quantity >= 50:
            discount_rate = 0.12
        elif quantity >= 30:
            discount_rate = 0.10
        elif quantity >= 20:
            discount_rate = 0.075
        elif quantity >= 10:
            discount_rate = 0.05
        unit_price = product.price * (1 - discount_rate)
        return unit_price
    
    elif category == 'cuplock':
        price_per_kg = 78
        weight = product.weight_per_unit if product.weight_per_unit else 5
        return price_per_kg * weight
    
    else:
        return product.price

app = Flask(__name__)

if not os.environ.get('SESSION_SECRET'):
    raise RuntimeError("SESSION_SECRET environment variable is required for security. Please set it in your environment.")

app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))

mail = Mail(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_order_confirmation_email(user, order, order_items):
    """Send order confirmation email to customer"""
    if not app.config['MAIL_USERNAME']:
        return
    
    try:
        items_html = ""
        for item in order_items:
            items_html += f"""
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 15px; color: #333;">{item.product_name}</td>
                <td style="padding: 15px; text-align: center; color: #333;">{item.quantity}</td>
                <td style="padding: 15px; text-align: right; color: #333;">₹{item.price:.2f}</td>
                <td style="padding: 15px; text-align: right; color: #4CAF50; font-weight: bold;">₹{(item.price * item.quantity):.2f}</td>
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
            <style>
                body {{ font-family: 'Poppins', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3a8a, #d4af37); padding: 30px; text-align: center; }}
                .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
                .content {{ padding: 30px; }}
                .order-details {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .order-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .order-table th {{ background-color: #1e3a8a; color: #ffffff; padding: 12px; text-align: left; }}
                .footer {{ background-color: #1e3a8a; color: #ffffff; padding: 20px; text-align: center; font-size: 14px; }}
                .total-row {{ background-color: #1e3a8a; color: #ffffff; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Order Confirmed!</h1>
                    <p style="color: #ffffff; margin: 10px 0 0 0;">Thank you for your order</p>
                </div>
                <div class="content">
                    <h2 style="color: #1e3a8a;">Dear {user.full_name or user.username},</h2>
                    <p style="color: #555; line-height: 1.6;">Thank you for choosing The National Scaffolding! Your order has been successfully placed and confirmed.</p>
                    
                    <div class="order-details">
                        <h3 style="color: #1e3a8a; margin-top: 0;">Order Details</h3>
                        <p style="margin: 5px 0; color: #555;"><strong>Order ID:</strong> #{order.id}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Order Date:</strong> {order.order_date.strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Transaction ID:</strong> <span style="font-family: monospace; background-color: #e8f5e9; padding: 3px 8px; border-radius: 4px;">{order.transaction_id}</span></p>
                        <p style="margin: 5px 0; color: #555;"><strong>Total Amount:</strong> <span style="color: #4CAF50; font-size: 18px; font-weight: bold;">₹{order.total_price:.2f}</span></p>
                    </div>
                    
                    <h3 style="color: #1e3a8a;">Order Items</h3>
                    <table class="order-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th style="text-align: center;">Quantity</th>
                                <th style="text-align: right;">Unit Price</th>
                                <th style="text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                            <tr class="total-row">
                                <td colspan="3" style="padding: 15px; text-align: right;">Total Amount (incl. 18% GST):</td>
                                <td style="padding: 15px; text-align: right;">₹{order.total_price:.2f}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <p style="color: #555; margin-top: 30px; line-height: 1.6;">We will process your order shortly. You can view your order status anytime by logging into your account and visiting the "My Orders" section.</p>
                    
                    <p style="color: #555; margin-top: 20px;">If you have any questions, please don't hesitate to contact us.</p>
                </div>
                <div class="footer">
                    <p style="margin: 0;">© 2025 The National Scaffolding. All rights reserved.</p>
                    <p style="margin: 10px 0 0 0;">Quality scaffolding solutions for your construction needs</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
    except Exception as e:
        print(f"Error sending customer email: {e}")

def send_admin_notification_email(order, user, order_items):
    """Send new order notification to admin"""
    if not app.config['MAIL_USERNAME']:
        return
    
    admin_email = os.environ.get('ADMIN_EMAIL', app.config['MAIL_DEFAULT_SENDER'])
    
    try:
        items_text = ""
        for item in order_items:
            items_text += f"- {item.product_name} x {item.quantity} @ ₹{item.price:.2f} = ₹{(item.price * item.quantity):.2f}\n"
        
        msg = Message(
            subject=f'🔔 New Order #{order.id} - The National Scaffolding',
            recipients=[admin_email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Poppins', Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #d4af37, #1e3a8a); padding: 30px; text-align: center; }}
                .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
                .content {{ padding: 30px; }}
                .alert-box {{ background-color: #fff3cd; border-left: 4px solid #d4af37; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .customer-info {{ background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .order-items {{ background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ background-color: #1e3a8a; color: #ffffff; padding: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 New Order Received!</h1>
                    <p style="color: #ffffff; margin: 10px 0 0 0;">Order #{order.id}</p>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <p style="margin: 0; color: #856404; font-weight: bold;">⚠️ Action Required: Please verify the payment and process this order</p>
                    </div>
                    
                    <h3 style="color: #1e3a8a;">Order Information</h3>
                    <p style="color: #555;"><strong>Order ID:</strong> #{order.id}</p>
                    <p style="color: #555;"><strong>Order Date:</strong> {order.order_date.strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p style="color: #555;"><strong>Transaction ID:</strong> <span style="font-family: monospace; background-color: #e8f5e9; padding: 3px 8px; border-radius: 4px;">{order.transaction_id}</span></p>
                    <p style="color: #555;"><strong>Total Amount:</strong> <span style="color: #4CAF50; font-size: 20px; font-weight: bold;">₹{order.total_price:.2f}</span> (incl. 18% GST)</p>
                    
                    <div class="customer-info">
                        <h3 style="color: #1e3a8a; margin-top: 0;">Customer Details</h3>
                        <p style="margin: 5px 0; color: #555;"><strong>Name:</strong> {user.full_name or user.username}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Email:</strong> {user.email}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>Phone:</strong> {user.phone or 'N/A'}</p>
                        {f'<p style="margin: 5px 0; color: #555;"><strong>Address:</strong> {user.address}</p>' if user.address else ''}
                        {f'<p style="margin: 5px 0; color: #555;"><strong>Organization:</strong> {user.organization}</p>' if user.organization else ''}
                    </div>
                    
                    <div class="order-items">
                        <h3 style="color: #1e3a8a; margin-top: 0;">Order Items</h3>
                        <pre style="background-color: #ffffff; padding: 10px; border-radius: 4px; overflow-x: auto; color: #333;">{items_text}</pre>
                    </div>
                    
                    <p style="color: #555; margin-top: 20px;"><strong>Next Steps:</strong></p>
                    <ol style="color: #555; line-height: 1.8;">
                        <li>Verify the transaction ID in your PhonePe account</li>
                        <li>Confirm the amount matches: ₹{order.total_price:.2f}</li>
                        <li>Process the order and prepare items for delivery</li>
                        <li>Contact customer if needed</li>
                    </ol>
                </div>
                <div class="footer">
                    <p style="margin: 0;">The National Scaffolding - Admin Dashboard</p>
                    <p style="margin: 10px 0 0 0; font-size: 12px;">Log in to admin panel to view full order details</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
    except Exception as e:
        print(f"Error sending admin email: {e}")

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

@app.route('/')
def index():
    category = request.args.get('category', 'all')
    
    if category == 'all':
        products = Product.query.filter_by(product_type='scaffolding').all()
    else:
        products = Product.query.filter_by(product_type='scaffolding', category=category).all()
    
    return render_template('landing.html', products=products, category=category)

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
        
        user = User(
            username=username,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
            organization=organization
        )
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
        
        # Check if this is an admin login attempt
        if identifier in ['admin_scaffolding', 'admin_fabrication']:
            # Determine panel type from username
            panel_type = 'scaffolding' if identifier == 'admin_scaffolding' else 'fabrication'
            
            # Check admin credentials
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
        
        # Regular user login
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.phone == identifier)
        ).first()
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
    if session.get('user_type') == 'admin':
        return jsonify({'success': False, 'message': 'Admins cannot purchase items'})
    
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    customization = data.get('customization', {})
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive integer'})
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid quantity'})
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})
    
    customization['quantity'] = quantity
    
    if product.category == 'h-frames' and quantity >= 100:
        return jsonify({'success': False, 'message': 'For orders of 100+ pieces, please contact us directly at sales@nationalscaffolding.com'})
    
    unit_price = calculate_price(product, customization)
    if unit_price is None:
        return jsonify({'success': False, 'message': 'Cannot calculate price for this configuration'})
    
    cart = session.get('cart', [])
    
    cart_item = {
        'product_id': product_id,
        'product_name': product.name,
        'quantity': quantity,
        'customization': customization
    }
    
    cart.append(cart_item)
    session['cart'] = cart
    
    return jsonify({'success': True, 'cart_count': len(cart)})

@app.route('/cart')
@login_required
def cart():
    if session.get('user_type') == 'admin':
        return redirect(url_for('admin_scaffoldings'))
    
    cart_items = session.get('cart', [])
    
    enriched_cart = []
    total = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            unit_price = calculate_price(product, item['customization'])
            if unit_price is not None:
                item_total = unit_price * item['quantity']
                total += item_total
                
                enriched_item = {
                    'product_name': product.name,
                    'quantity': item['quantity'],
                    'unit_price': unit_price,
                    'item_total': item_total,
                    'customization': item['customization'],
                    'image_url': product.image_url
                }
                enriched_cart.append(enriched_item)
    
    return render_template('cart.html', cart_items=enriched_cart, total=total)

@app.route('/remove_from_cart/<int:index>')
@login_required
def remove_from_cart(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
    
    return redirect(url_for('cart'))

@app.route('/qr_scanner')
@login_required
def qr_scanner():
    if session.get('user_type') == 'admin':
        return redirect(url_for('admin_scaffoldings'))
    
    cart_items = session.get('cart', [])
    total = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            unit_price = calculate_price(product, item['customization'])
            if unit_price is not None:
                total += unit_price * item['quantity']
    
    gst = total * 0.18
    total_with_gst = total + gst
    
    qr_data = f"upi://pay?pa=nationalscaffolding@phonepe&pn=The National Scaffolding&am={total_with_gst:.2f}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('qr_scanner.html', total=total, gst=gst, total_with_gst=total_with_gst, qr_code=qr_code_base64)

@app.route('/complete_order', methods=['POST'])
@login_required
def complete_order():
    if session.get('user_type') == 'admin':
        return jsonify({'success': False, 'message': 'Admins cannot place orders'})
    
    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'})
    
    data = request.json or {}
    transaction_id = data.get('transaction_id', '').strip()
    
    if not transaction_id or len(transaction_id) < 8:
        return jsonify({'success': False, 'message': 'Valid Transaction ID is required (minimum 8 characters)'})
    
    existing_order = Order.query.filter_by(transaction_id=transaction_id).first()
    if existing_order:
        return jsonify({'success': False, 'message': 'This Transaction ID has already been used. Each purchase requires a unique payment. Please make a new payment and enter the new Transaction ID.'})
    
    total = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            unit_price = calculate_price(product, item['customization'])
            if unit_price is not None:
                total += unit_price * item['quantity']
    
    gst = total * 0.18
    total_with_gst = total + gst
    
    order = Order(
        user_id=current_user.id, 
        total_price=total_with_gst, 
        status='pending_verification',
        transaction_id=transaction_id,
        amount_paid=0
    )
    db.session.add(order)
    db.session.flush()
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            unit_price = calculate_price(product, item['customization'])
            if unit_price is not None:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    product_name=product.name,
                    quantity=item['quantity'],
                    price=unit_price,
                    customization=item.get('customization')
                )
                db.session.add(order_item)
    
    db.session.commit()
    session['cart'] = []
    
    send_order_confirmation_email(current_user, order, order.order_items)
    send_admin_notification_email(order, current_user, order.order_items)
    
    return jsonify({'success': True, 'order_id': order.id})

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
    
    # Determine which admin is logged in
    admin_username = current_user.username
    
    if admin_username == 'admin_scaffolding':
        # Show only orders containing scaffolding products
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(
            Product.product_type == 'scaffolding'
        ).distinct().order_by(Order.order_date.desc()).all()
    elif admin_username == 'admin_fabrication':
        # Show only orders containing fabrication products
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(
            Product.product_type == 'fabrication'
        ).distinct().order_by(Order.order_date.desc()).all()
    else:
        # Fallback: show all orders
        orders = Order.query.order_by(Order.order_date.desc()).all()
    
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin_analytics')
@login_required
def admin_analytics():
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    # Get all orders
    orders = Order.query.all()
    
    # Aggregate data by month
    monthly_data = {}
    yearly_data = {}
    category_data = {}
    
    for order in orders:
        # Monthly aggregation
        month_key = order.order_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'revenue': 0, 'orders': 0}
        monthly_data[month_key]['revenue'] += float(order.total_price)
        monthly_data[month_key]['orders'] += 1
        
        # Yearly aggregation
        year_key = order.order_date.strftime('%Y')
        if year_key not in yearly_data:
            yearly_data[year_key] = {'revenue': 0, 'orders': 0}
        yearly_data[year_key]['revenue'] += float(order.total_price)
        yearly_data[year_key]['orders'] += 1
        
        # Category-wise aggregation
        for item in order.items:
            category = item.product.category or 'Other'
            if category not in category_data:
                category_data[category] = {'revenue': 0, 'quantity': 0}
            category_data[category]['revenue'] += float(item.price) * item.quantity
            category_data[category]['quantity'] += item.quantity
    
    # Sort monthly data
    sorted_months = sorted(monthly_data.keys())
    
    # Calculate totals
    total_revenue = sum(order.total_price for order in orders)
    total_orders = len(orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    return render_template('admin_analytics.html',
                         monthly_data=monthly_data,
                         yearly_data=yearly_data,
                         category_data=category_data,
                         sorted_months=sorted_months,
                         total_revenue=total_revenue,
                         total_orders=total_orders,
                         avg_order_value=avg_order_value)

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
        return jsonify({'success': False})
    
    image_url = None
    if 'product_image' in request.files:
        file = request.files['product_image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f"/static/uploads/{filename}"
    
    product = Product(
        name=request.form.get('name'),
        price=float(request.form.get('price')),
        description=request.form.get('description', ''),
        category=request.form.get('category'),
        product_type=request.form.get('product_type'),
        customization_options=None,
        rent_price=float(request.form.get('rent_price')) if request.form.get('rent_price') else None,
        image_url=image_url,
        weight_per_unit=float(request.form.get('weight_per_unit')) if request.form.get('weight_per_unit') else None
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'success': True, 'product_id': product.id})

@app.route('/admin_update_product/<int:product_id>', methods=['POST'])
@login_required
def admin_update_product(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False})
    
    product = Product.query.get_or_404(product_id)
    
    if 'product_image' in request.files:
        file = request.files['product_image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            product.image_url = f"/static/uploads/{filename}"
    
    product.name = request.form.get('name')
    product.price = float(request.form.get('price'))
    product.description = request.form.get('description', '')
    product.category = request.form.get('category')
    product.rent_price = float(request.form.get('rent_price')) if request.form.get('rent_price') else None
    product.weight_per_unit = float(request.form.get('weight_per_unit')) if request.form.get('weight_per_unit') else None
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin_delete_product/<int:product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False})
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin_pricing_matrix/<int:product_id>')
@login_required
def admin_pricing_matrix(product_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    product = Product.query.get_or_404(product_id)
    
    if product.category != 'aluminium':
        flash('Pricing matrix is only available for aluminium products', 'warning')
        return redirect(url_for('admin_scaffoldings'))
    
    pricing_matrix = product.customization_options.get('pricing_matrix', {}) if product.customization_options else {}
    
    return render_template('admin_pricing_matrix.html', product=product, pricing_matrix=pricing_matrix)

@app.route('/admin_update_pricing_matrix/<int:product_id>', methods=['POST'])
@login_required
def admin_update_pricing_matrix(product_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    product = Product.query.get_or_404(product_id)
    
    if product.category != 'aluminium':
        return jsonify({'success': False, 'message': 'Pricing matrix only for aluminium products'})
    
    data = request.json
    pricing_matrix = data.get('pricing_matrix', {})
    
    if not product.customization_options:
        product.customization_options = {}
    
    product.customization_options['pricing_matrix'] = pricing_matrix
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(product, 'customization_options')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Pricing matrix updated successfully'})

@app.route('/download-backup')
def download_backup():
    """Temporary route to download project backup"""
    import os
    backup_path = '/home/runner/workspace/PROJECT_BACKUP.tar.gz'
    if os.path.exists(backup_path):
        return send_file(backup_path, 
                        as_attachment=True, 
                        download_name='national-scaffolding-backup.tar.gz',
                        mimetype='application/gzip')
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
            return jsonify({
                'success': False, 
                'message': 'Invalid amount format. Please enter a valid number.'
            })
        
        if amount_paid <= 0:
            return jsonify({
                'success': False, 
                'message': 'Amount must be greater than zero.'
            })
        
        if amount_paid < order.total_price:
            return jsonify({
                'success': False, 
                'message': f'Amount paid (₹{amount_paid:.2f}) is less than required (₹{order.total_price:.2f})'
            })
        
        order.amount_paid = amount_paid
        order.status = 'completed'
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Payment verified and order approved'
        })
    
    elif action == 'reject':
        order.status = 'rejected'
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Order rejected'
        })
    
    return jsonify({'success': False, 'message': 'Invalid action'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
