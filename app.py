from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Admin, Product, Order, OrderItem
import os
import qrcode
import io
import base64
from datetime import datetime

def calculate_price(product, customization):
    quantity = customization.get('quantity', 1)
    category = product.category
    
    if category == 'aluminium':
        purchase_type = customization.get('purchaseType', 'buy')
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
    return redirect(url_for('national_scaffoldings'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        organization = request.form.get('organization')
        password = request.form.get('password')
        
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
    return redirect(url_for('login'))

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
                    'customization': item['customization']
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
        status='completed',
        transaction_id=transaction_id,
        amount_paid=total_with_gst
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
    
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin_orders.html', orders=orders)

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
    
    data = request.json
    product = Product(
        name=data['name'],
        price=float(data['price']),
        description=data.get('description', ''),
        category=data.get('category'),
        product_type=data['product_type'],
        customization_options=data.get('customization_options'),
        rent_price=float(data['rent_price']) if data.get('rent_price') else None,
        image_url=data.get('image_url'),
        weight_per_unit=float(data['weight_per_unit']) if data.get('weight_per_unit') else None
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
    data = request.json
    
    product.name = data['name']
    product.price = float(data['price'])
    product.description = data.get('description', '')
    product.category = data.get('category')
    product.customization_options = data.get('customization_options')
    product.rent_price = float(data['rent_price']) if data.get('rent_price') else None
    product.image_url = data.get('image_url')
    product.weight_per_unit = float(data['weight_per_unit']) if data.get('weight_per_unit') else None
    
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
