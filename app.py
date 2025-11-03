from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Admin, Product, Order, OrderItem
import os
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)

if not os.environ.get('SESSION_SECRET'):
    raise RuntimeError("SESSION_SECRET environment variable is required for security. Please set it in your environment.")

app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'user')
        
        if user_type == 'admin':
            user = Admin.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                session['user_type'] = 'admin'
                session['panel_type'] = user.panel_type
                if user.panel_type == 'scaffolding':
                    return redirect(url_for('admin_scaffoldings'))
                else:
                    return redirect(url_for('admin_fabrication'))
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                session['user_type'] = 'user'
                session['cart'] = session.get('cart', [])
                return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

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

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    if session.get('user_type') == 'admin':
        return jsonify({'success': False, 'message': 'Admins cannot purchase items'})
    
    data = request.json
    cart = session.get('cart', [])
    
    cart_item = {
        'product_id': data['product_id'],
        'product_name': data['product_name'],
        'price': data['price'],
        'quantity': data.get('quantity', 1),
        'customization': data.get('customization', {})
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
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

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
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    qr_data = f"upi://pay?pa=nationalscaffolding@upi&pn=National Scaffolding&am={total}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('qr_scanner.html', total=total, qr_code=qr_code_base64)

@app.route('/complete_order', methods=['POST'])
@login_required
def complete_order():
    if session.get('user_type') == 'admin':
        return jsonify({'success': False})
    
    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'success': False})
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    order = Order(user_id=current_user.id, total_price=total, status='completed')
    db.session.add(order)
    db.session.flush()
    
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product_id'],
            product_name=item['product_name'],
            quantity=item['quantity'],
            price=item['price'],
            customization=item.get('customization')
        )
        db.session.add(order_item)
    
    db.session.commit()
    session['cart'] = []
    
    return jsonify({'success': True})

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
        rent_price=data.get('rent_price')
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
    product.rent_price = data.get('rent_price')
    
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
