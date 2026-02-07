from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required
from models import db, Product, CuplockVerticalSize, CuplockLedgerSize, CuplockVerticalCup
from sqlalchemy.exc import IntegrityError
import logging
import os
import uuid
from werkzeug.utils import secure_filename
from utils import get_image_url

cuplock_bp = Blueprint('cuplock', __name__)
logger = logging.getLogger(__name__)

# ===========================
# CONFIGURATION
# ===========================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff', 'ico', 'jfif', 'pjpeg', 'pjp', 'avif', 'heic', 'heif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

LEDGER_SIZES = {
    '0.9m': {'weight': 3.5}, '1m': {'weight': 4.0}, '1.2m': {'weight': 4.5},
    '1.5m': {'weight': 5.0}, '1.8m': {'weight': 6.0}, '2m': {'weight': 7.0},
    '2.2m': {'weight': 7.5}, '2.5m': {'weight': 8.0}, '2.8m': {'weight': 8.5},
    '3m': {'weight': 9.0},
}

VERTICAL_SIZES = ['1m', '1.5m', '2m', '2.5m', '3m']
VERTICAL_CUP_OPTIONS = {
    '1M x 1M': [1, 2], '1.5M x 1.5M': [2, 3], '2M x 2M': [2, 3, 4],
    '2.5M x 2.5M': [2, 3, 4], '3M x 3M': [3, 4, 6],
}

# ===========================
# STATIC CONFIGURATION FOR VERTICAL CUPLOCK
# ===========================
STATIC_VERTICAL_CONFIG = [
    {
        'id': 9001, 
        'size_label': '1m', 
        'buy_price': 500.00, 
        'rent_price': 50.00, 
        'deposit': 100.00, 
        'cups': [1, 2] # 1 Cup, 2 Cups
    },
    {
        'id': 9002, 
        'size_label': '1.5m', 
        'buy_price': 750.00, 
        'rent_price': 75.00, 
        'deposit': 150.00, 
        'cups': [2, 3] # 2 Cups, 3 Cups
    },
    {
        'id': 9003, 
        'size_label': '2m', 
        'buy_price': 1000.00, 
        'rent_price': 100.00, 
        'deposit': 200.00, 
        'cups': [2, 3, 4] # 2 Cups, 3 Cups, 4 Cups
    },
    {
        'id': 9004, 
        'size_label': '2.5m', 
        'buy_price': 1250.00, 
        'rent_price': 125.00, 
        'deposit': 250.00, 
        'cups': [2, 3, 4] # 2 Cups, 3 Cups, 4 Cups
    },
    {
        'id': 9005, 
        'size_label': '3m', 
        'buy_price': 1500.00, 
        'rent_price': 150.00, 
        'deposit': 300.00, 
        'cups': [3, 4, 6] # 3 Cups, 4 Cups, 6 Cups
    }
]
# ============================================================================
# DEBUG ROUTE - Add this to your cuplock_routes.py file temporarily
# This will help us see what's actually in the database
# ============================================================================

@cuplock_bp.route('/debug/vertical/product/<int:product_id>/sizes')
def debug_vertical_sizes(product_id):
    """
    Debug route to see what sizes exist in database for this product
    Visit: http://127.0.0.1:5001/cuplock/debug/vertical/product/162/sizes
    """
    try:
        from models import Product, CuplockVerticalSize
        
        # Get the product
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'error': f'Product {product_id} not found in database'
            })
        
        # Get all sizes (including inactive ones for debugging)
        all_sizes = CuplockVerticalSize.query.filter_by(product_id=product_id).all()
        active_sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        
        debug_info = {
            'product_id': product.id,
            'product_name': product.name,
            'product_category': product.category,
            'product_cuplock_type': product.cuplock_type,
            'total_sizes_in_db': len(all_sizes),
            'active_sizes_in_db': len(active_sizes),
            'all_sizes': [],
            'active_sizes': []
        }
        
        # Show ALL sizes
        for size in all_sizes:
            debug_info['all_sizes'].append({
                'id': size.id,
                'size_label': size.size_label,
                'buy_price': float(size.buy_price or 0),
                'rent_price': float(size.rent_price or 0),
                'deposit': float(size.deposit or 0),
                'weight': float(size.weight or 0) if hasattr(size, 'weight') else 0,
                'is_active': size.is_active
            })
        
        # Show ACTIVE sizes
        for size in active_sizes:
            debug_info['active_sizes'].append({
                'id': size.id,
                'size_label': size.size_label,
                'buy_price': float(size.buy_price or 0),
                'rent_price': float(size.rent_price or 0),
                'deposit': float(size.deposit or 0),
                'weight': float(size.weight or 0) if hasattr(size, 'weight') else 0,
                'is_active': size.is_active
            })
        
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================================================
# ALSO - Check if 'weight' column exists in CuplockVerticalSize table
# ============================================================================

@cuplock_bp.route('/debug/vertical/check-schema')
def debug_vertical_schema():
    """
    Check what columns exist in CuplockVerticalSize table
    Visit: http://127.0.0.1:5001/cuplock/debug/vertical/check-schema
    """
    try:
        from models import CuplockVerticalSize
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        columns = inspector.get_columns('cuplock_vertical_size')
        
        column_info = []
        for col in columns:
            column_info.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable']
            })
        
        return jsonify({
            'table': 'cuplock_vertical_size',
            'columns': column_info
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================================================
# INSTRUCTIONS:
# ============================================================================
# 1. Add both debug routes above to your cuplock_routes.py file
# 2. Restart your Flask server
# 3. Visit: http://127.0.0.1:5001/cuplock/debug/vertical/product/162/sizes
# 4. Visit: http://127.0.0.1:5001/cuplock/debug/vertical/check-schema
# 5. Copy the JSON output and share it with me
# 6. This will show us:
#    - If sizes exist in database
#    - If they're marked as active
#    - What columns exist in the table
#    - If there's a 'weight' column issue
# ============================================================================
# ===========================
# ADMIN: VERTICAL CUPLOCK
# ===========================

@cuplock_bp.route('/admin/vertical')
@login_required
def vertical_list():
    try:
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        products = Product.query.filter_by(category='cuplock', cuplock_type='vertical', is_active=True).all()
        for product in products:
            product.display_image_url = get_image_url(product.image_url)
        return render_template('cuplock_vertical_list.html', products=products)
    except Exception as e:
        logger.error(f"Error loading vertical cuplock list: {e}", exc_info=True)
        flash(f'Error loading products: {str(e)}', 'error')
        return redirect(url_for('admin_scaffoldings'))

@cuplock_bp.route('/admin/vertical/create', methods=['GET', 'POST'])
@login_required
def vertical_create():
    try:
        if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description', '')
            price = float(request.form.get('price', 0))
            
            if not name:
                flash('Product name is required', 'error')
                return render_template('cuplock_vertical_create.html')

            product = Product(name=name, description=description, category='cuplock',
                              cuplock_type='vertical', product_type='scaffolding', price=price, is_active=True)

            # Handle Image Upload
            uploaded_images = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                            os.makedirs(upload_folder, exist_ok=True)
                            unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                            filepath = os.path.join(upload_folder, unique_name)
                            file.save(filepath)
                            uploaded_images.append(f'uploads/{unique_name}')
                        except Exception as e:
                            logger.error(f"Error saving image: {e}")
            
            if uploaded_images: product.image_url = ','.join(uploaded_images)
            db.session.add(product)
            db.session.commit()

            # Handle Sizes
            try:
                sizes_data = request.form.to_dict(flat=False)
                size_index = 0
                while True:
                    size_label_key = f'sizes[{size_index}][label]'
                    if size_label_key not in sizes_data: break
                    size_label = sizes_data.get(size_label_key, [None])[0]
                    if not size_label: size_index += 1; continue
                    
                    def safe_float(key): return float(sizes_data.get(key, [None])[0]) if sizes_data.get(key, [None])[0] else 0.0
                    
                    buy_price = safe_float(f'sizes[{size_index}][buy_price]')
                    rent_price = safe_float(f'sizes[{size_index}][rent_price]')
                    deposit = safe_float(f'sizes[{size_index}][deposit]')
                    weight = safe_float(f'sizes[{size_index}][weight]')
                    
                    if buy_price > 0 or rent_price > 0:
                        new_size = CuplockVerticalSize(product_id=product.id, size_label=size_label,
                                                      buy_price=buy_price, rent_price=rent_price,
                                                      deposit=deposit, weight=weight, is_active=True)
                        db.session.add(new_size)
                    size_index += 1
                db.session.commit()
            except Exception as e: logger.warning(f"Error processing sizes: {e}")

            flash('✅ Vertical Cuplock product created successfully!', 'success')
            return redirect(url_for('cuplock.vertical_edit', product_id=product.id))

        return render_template('cuplock_vertical_create.html')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating vertical product: {e}", exc_info=True)
        flash('Error creating product', 'error')
        return redirect(url_for('cuplock.vertical_list'))

@cuplock_bp.route('/admin/vertical/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def vertical_edit(product_id):
    try:
        if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
        product = Product.query.get_or_404(product_id)

        if request.method == 'POST':
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', '')
            
            if 'images' in request.files:
                files = request.files.getlist('images')
                uploaded_images = []
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                            os.makedirs(upload_folder, exist_ok=True)
                            unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                            filepath = os.path.join(upload_folder, unique_name)
                            file.save(filepath)
                            uploaded_images.append(f'uploads/{unique_name}')
                        except Exception as e: logger.error(f"Error saving image: {e}")
                if uploaded_images: product.image_url = ','.join(uploaded_images)
            
            db.session.commit()
            flash('✅ Product updated successfully!', 'success')
            return redirect(url_for('cuplock.vertical_edit', product_id=product_id))

        sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        image_url = get_image_url(product.image_url) if product.image_url else 'images/no-image.png'
        return render_template('cuplock_vertical_edit.html', product=product, sizes=sizes,
                               available_sizes=VERTICAL_SIZES, cup_options=VERTICAL_CUP_OPTIONS, image_url=image_url)
    except Exception as e:
        logger.error(f"Error editing vertical product: {e}", exc_info=True)
        flash('Error loading product', 'error')
        return redirect(url_for('cuplock.vertical_list'))

@cuplock_bp.route('/admin/vertical/product/<int:product_id>/delete', methods=['POST'])
@login_required
def vertical_delete_product(product_id):
    try:
        if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Admin access required'}), 403
        product = Product.query.get_or_404(product_id)
        product.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.exception("Error deleting vertical product")
        return jsonify({'success': False, 'message': 'Server error occurred'}), 500

@cuplock_bp.route('/admin/vertical/<int:product_id>/size/add', methods=['POST'])
@login_required
def vertical_add_size(product_id):
    try:
        if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        size_label = request.form.get('size_label')
        if not size_label or size_label not in VERTICAL_SIZES: return jsonify({'success': False, 'message': 'Invalid size'}), 400
        
        existing = CuplockVerticalSize.query.filter_by(product_id=product_id, size_label=size_label, is_active=True).first()
        if existing: return jsonify({'success': False, 'message': 'Size already exists'}), 400
        
        def safe_decimal(val): return float(val) if val else 0.0
        buy_price = safe_decimal(request.form.get('buy_price'))
        rent_price = safe_decimal(request.form.get('rent_price'))
        
        if buy_price == 0 and rent_price == 0: return jsonify({'success': False, 'message': 'Set at least one price'}), 400

        size = CuplockVerticalSize(product_id=product_id, size_label=size_label, weight=safe_decimal(request.form.get('weight')),
                                  buy_price=buy_price, rent_price=rent_price, deposit=safe_decimal(request.form.get('deposit')), is_active=True)
        db.session.add(size)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Size added successfully'})
    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding vertical size")
        return jsonify({'success': False, 'message': 'Server error occurred'}), 500

@cuplock_bp.route('/admin/vertical/size/<int:size_id>/cup/add', methods=['POST'])
@login_required
def vertical_add_cup(size_id):
    try:
        if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        size = CuplockVerticalSize.query.get_or_404(size_id)
        cup_count = request.form.get('cup_count')
        if not cup_count: return jsonify({'success': False, 'message': 'Cup count required'}), 400
        
        existing = CuplockVerticalCup.query.filter_by(vertical_size_id=size_id, cup_count=int(cup_count)).first()
        if existing: return jsonify({'success': False, 'message': 'Cup count already exists'}), 400
        
        cup_image_url = ''
        if 'cup_image' in request.files and request.files['cup_image']:
            file = request.files['cup_image']
            if file and file.filename and allowed_file(file.filename):
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                filepath = os.path.join(upload_folder, unique_name)
                try:
                    file.save(filepath)
                    cup_image_url = unique_name
                except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500
        
        cup = CuplockVerticalCup(vertical_size_id=size_id, cup_count=int(cup_count), cup_image_url=cup_image_url,
                                 weight_kg=float(request.form.get('weight_kg') or 0),
                                 buy_price=float(request.form.get('buy_price') or 0),
                                 rent_price=float(request.form.get('rent_price') or 0),
                                 deposit_amount=float(request.form.get('deposit') or 0))
        db.session.add(cup)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cup configuration added'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding cup configuration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@cuplock_bp.route('/admin/vertical/size/<int:size_id>/delete', methods=['POST'])
@login_required
def vertical_delete_size(size_id):
    try: size = CuplockVerticalSize.query.get_or_404(size_id); size.is_active = False; db.session.commit(); return jsonify({'success': True})
    except Exception as e: db.session.rollback(); logger.error(f"Error deleting vertical size: {e}"); return jsonify({'success': False, 'message': str(e)}), 500

@cuplock_bp.route('/admin/vertical/cup/<int:cup_id>/delete', methods=['POST'])
@login_required
def vertical_delete_cup(cup_id):
    try: cup = CuplockVerticalCup.query.get_or_404(cup_id); db.session.delete(cup); db.session.commit(); return jsonify({'success': True, 'message': 'Cup configuration deleted'})
    except Exception as e: db.session.rollback(); logger.error(f"Error deleting cup: {e}"); return jsonify({'success': False, 'message': str(e)}), 500

# ===========================
# ADMIN: LEDGER CUPLOCK
# ===========================

@cuplock_bp.route('/admin/ledger')
@login_required
def ledger_list():
    try:
        if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
        products = Product.query.filter_by(category='cuplock', cuplock_type='ledger', is_active=True).all()
        for product in products: product.display_image_url = get_image_url(product.image_url)
        return render_template('cuplock_ledger_list.html', products=products)
    except Exception as e: logger.error(f"Error loading ledger list: {e}"); flash('Error loading products', 'error'); return redirect(url_for('admin_scaffoldings'))

@cuplock_bp.route('/admin/ledger/create', methods=['GET', 'POST'])
@login_required
def ledger_create():
    try:
        if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
        if request.method == 'POST':
            name = request.form.get('name')
            if not name: flash('Product name is required', 'error'); return render_template('cuplock_ledger_create.html', ledger_sizes=LEDGER_SIZES)
            
            product = Product(name=name, description=request.form.get('description', ''), category='cuplock',
                              cuplock_type='ledger', product_type='scaffolding', price=float(request.form.get('price', 0)), is_active=True)
            
            if 'image' in request.files and request.files['image']:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(upload_folder, unique_name)
                        file.save(filepath)
                        product.image_url = f'uploads/{unique_name}'
                    except Exception as e: logger.error(f"Error saving image: {e}")

            db.session.add(product); db.session.commit()
            flash('Ledger product created — now add sizes.', 'success')
            return redirect(url_for('cuplock.ledger_edit', product_id=product.id))
        return render_template('cuplock_ledger_create.html', ledger_sizes=LEDGER_SIZES)
    except Exception as e: db.session.rollback(); logger.error(f"Error creating ledger product: {e}"); flash('Error creating product', 'error'); return redirect(url_for('cuplock.ledger_list'))

@cuplock_bp.route('/admin/ledger/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def ledger_edit(product_id):
    try:
        if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
        product = Product.query.get_or_404(product_id)
        if request.method == 'POST':
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', '')
            if 'image' in request.files and request.files['image']:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(upload_folder, unique_name)
                        file.save(filepath)
                        product.image_url = f'uploads/{unique_name}'
                    except Exception as e: logger.error(f"Error saving image: {e}")
            db.session.commit(); flash('Product updated!', 'success'); return redirect(url_for('cuplock.ledger_edit', product_id=product_id))

        sizes = CuplockLedgerSize.query.filter_by(product_id=product_id, is_active=True).all()
        image_url = get_image_url(product.image_url)
        return render_template('cuplock_ledger_edit.html', product=product, sizes=sizes, ledger_sizes=LEDGER_SIZES, image_url=image_url)
    except Exception as e: logger.error(f"Error editing ledger product: {e}"); flash('Error loading product', 'error'); return redirect(url_for('cuplock.ledger_list'))

@cuplock_bp.route('/admin/ledger/product/<int:product_id>/delete', methods=['POST'])
@login_required
def ledger_delete_product(product_id):
    try:
        if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Admin access required'}), 403
        product = Product.query.get_or_404(product_id); product.is_active = False; db.session.commit()
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e: db.session.rollback(); logger.exception("Error deleting ledger product"); return jsonify({'success': False, 'message': 'Server error occurred'}), 500

@cuplock_bp.route('/admin/ledger/<int:product_id>/size/add', methods=['POST'])
@login_required
def ledger_add_size(product_id):
    try:
        if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        size_label = request.form.get('size_label')
        if size_label not in LEDGER_SIZES: return jsonify({'success': False, 'message': 'Invalid size'}), 400
        if CuplockLedgerSize.query.filter_by(product_id=product_id, size_label=size_label, is_active=True).first():
            return jsonify({'success': False, 'message': 'Size already exists'}), 400
        
        size = CuplockLedgerSize(product_id=product_id, size_label=size_label, weight_kg=LEDGER_SIZES[size_label]['weight'],
                                 buy_price=float(request.form.get('buy_price') or 0),
                                 rent_price=float(request.form.get('rent_price') or 0),
                                 deposit_amount=float(request.form.get('deposit') or 0), is_active=True)
        db.session.add(size); db.session.commit()
        return jsonify({'success': True, 'message': 'Size added successfully'})
    except Exception as e: db.session.rollback(); logger.error(f"Error adding ledger size: {e}"); return jsonify({'success': False, 'message': str(e)}), 500

@cuplock_bp.route('/admin/ledger/size/<int:size_id>/delete', methods=['POST'])
@login_required
def ledger_delete_size(size_id):
    try: size = CuplockLedgerSize.query.get_or_404(size_id); size.is_active = False; db.session.commit(); return jsonify({'success': True})
    except Exception as e: db.session.rollback(); logger.error(f"Error deleting ledger size: {e}"); return jsonify({'success': False, 'message': str(e)}), 500

# ===========================
# USER-FACING PAGES
# ===========================

@cuplock_bp.route('/product/vertical/<int:product_id>')
def vertical_product_page(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        if product.category != 'cuplock' or product.cuplock_type != 'vertical':
            flash('Invalid product type', 'error')
            return redirect(url_for('national_scaffoldings'))
        
        # ==========================================
        # CALCULATE IMAGE URL
        # ==========================================
        # We use the same logic that makes your main page work
        raw_image = product.image_url
        calculated_url = get_image_url(raw_image) if raw_image else '/static/images/no-image.png'
        
        print(f"*** DEBUG: Sending Image URL to Template: {calculated_url} ***")
        # ==========================================

        # Minimal queries to prevent crash
        sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        sizes_data = [{'id': s.id, 'size_label': s.size_label} for s in sizes]
        cups_data = []

        return render_template(
            'cuplock_vertical.html',
            product=product,
            sizes=sizes_data,
            cups=cups_data,
            # ✅ WE PASS THE IMAGE AS A STANDALONE VARIABLE
            single_image_url=calculated_url 
        )
        
    except Exception as e:
        logger.error(f"Error loading vertical product {product_id}: {e}", exc_info=True)
        flash('Error loading product details.', 'error')
        return redirect(url_for('national_scaffoldings', category='cuplock'))

@cuplock_bp.route('/product/ledger/<int:product_id>')
def ledger_product_page(product_id):
    product = Product.query.filter_by(id=product_id, category='cuplock', cuplock_type='ledger', is_active=True).first_or_404()
    sizes = CuplockLedgerSize.query.filter_by(product_id=product.id, is_active=True).all()
    product.display_image_url = get_image_url(product.image_url)
    return render_template('cuplock_ledger.html', product=product, sizes=sizes)

# ===========================
# API ENDPOINTS
# ===========================

    try:
        # 1. Try to get from Database first
        db_sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        
        # 2. If DB is empty, use our STATIC CONFIGURATION
        if not db_sizes:
            # Return the hardcoded sizes you asked for
            return jsonify({
                'success': True, 
                'sizes': STATIC_VERTICAL_CONFIG
            })
        
        # 3. If DB has data, return DB data
        return jsonify({
            'success': True, 
            'sizes': [
                {
                    'id': s.id, 
                    'size_label': s.size_label, 
                    'weight': float(s.weight or 0), 
                    'buy_price': float(s.buy_price or 0), 
                    'rent_price': float(s.rent_price or 0), 
                    'deposit': float(s.deposit or 0)
                } 
                for s in db_sizes
            ]
        })
    except Exception as e: 
        logger.error(f"Error fetching vertical sizes: {e}"); 
        return jsonify({'success': False, 'message': 'Error fetching sizes'}), 500

@cuplock_bp.route('/admin/api/ledger/<int:product_id>/sizes')
def admin_api_ledger_sizes(product_id):
    sizes = CuplockLedgerSize.query.filter_by(product_id=product_id, is_active=True).order_by(CuplockLedgerSize.size_label).all()
    return jsonify([{"id": s.id, "label": s.size_label, "weight": float(s.weight_kg or 0), "buy_price": float(s.buy_price or 0), "rent_price": float(s.rent_price or 0), "deposit": float(s.deposit_amount or 0)} for s in sizes])

@cuplock_bp.route('/admin/api/vertical/<int:product_id>/sizes')
def api_admin_vertical_sizes(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        return jsonify([{"id": s.id, "label": s.size_label, "weight": float(s.weight) if s.weight else 0, "buy_price": float(s.buy_price) if s.buy_price else 0, "rent_price": float(s.rent_price) if s.rent_price else 0, "deposit": float(s.deposit) if s.deposit else 0, "cups": VERTICAL_CUP_OPTIONS.get(s.size_label, [])} for s in sizes])
    except Exception as e: logger.error(f"Error loading vertical sizes API: {e}"); return jsonify({"error": True, "message": str(e)}), 500

# ============================================================================
# FIXED API ENDPOINTS FOR VERTICAL CUPLOCK - cuplock_routes.py
# Replace these two functions in your cuplock_routes.py file
# ============================================================================
# ============================================================================
# COMPLETE FIX FOR VERTICAL CUPLOCK SIZES NOT SHOWING
# ============================================================================

# PROBLEM IDENTIFIED:
# Your CuplockVerticalSize model doesn't have a 'weight' column
# But your API is trying to read it, causing a 500 error

# ============================================================================
# SOLUTION - Choose ONE of these options:
# ============================================================================

# ─────────────────────────────────────────────────────────────────────────
# OPTION 1: FIX THE API (RECOMMENDED - Faster, No DB Changes)
# ─────────────────────────────────────────────────────────────────────────

# In cuplock_routes.py, replace your api_vertical_sizes function with this:

@cuplock_bp.route('/api/vertical/product/<int:product_id>/sizes')
def api_vertical_sizes(product_id):
    """
    ✅ FIXED: Removed 'weight' field access since it doesn't exist in model
    """
    try:
        # 1. Try to get from Database first
        db_sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        
        # 2. If DB has data, return DB data
        if db_sizes:
            return jsonify({
                'success': True, 
                'sizes': [
                    {
                        'id': s.id, 
                        'size_label': s.size_label, 
                        # ✅ REMOVED: 'weight' field (doesn't exist in model)
                        'buy_price': float(s.buy_price or 0), 
                        'rent_price': float(s.rent_price or 0), 
                        'deposit': float(s.deposit or 0)
                    } 
                    for s in db_sizes
                ]
            })
        
        # 3. If DB is empty, use STATIC CONFIG
        static_sizes = []
        for config in STATIC_VERTICAL_CONFIG:
            static_sizes.append({
                'id': config['id'],
                'size_label': config['size_label'],
                'buy_price': config['buy_price'],
                'rent_price': config['rent_price'],
                'deposit': config['deposit']
            })
        
        return jsonify({
            'success': True, 
            'sizes': static_sizes
        })
        
    except Exception as e: 
        logger.error(f"❌ Error fetching vertical sizes for product {product_id}: {e}", exc_info=True)
        return jsonify({
            'success': False, 
            'message': f'Error: {str(e)}',
            'sizes': []
        }), 200
    # ============================================================================
# QUICK DATABASE CHECK - Do you actually have cups data?
# ============================================================================

# Add this route to cuplock_routes.py to check if cups exist:

@cuplock_bp.route('/debug/product/<int:product_id>/full-check')
def debug_product_full_check(product_id):
    """
    Complete check of product, sizes, and cups
    Visit: http://127.0.0.1:5001/cuplock/debug/product/162/full-check
    """
    try:
        from models import Product, CuplockVerticalSize, CuplockVerticalCup
        
        # Get product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': f'Product {product_id} not found'})
        
        # Get sizes
        sizes = CuplockVerticalSize.query.filter_by(
            product_id=product_id, 
            is_active=True
        ).all()
        
        result = {
            'product': {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'cuplock_type': product.cuplock_type
            },
            'sizes_count': len(sizes),
            'sizes': []
        }
        
        # For each size, check cups
        for size in sizes:
            cups = CuplockVerticalCup.query.filter_by(
                vertical_size_id=size.id
            ).all()
            
            size_info = {
                'size_id': size.id,
                'size_label': size.size_label,
                'buy_price': float(size.buy_price or 0),
                'rent_price': float(size.rent_price or 0),
                'deposit': float(size.deposit or 0),
                'cups_count': len(cups),
                'cups': []
            }
            
            for cup in cups:
                size_info['cups'].append({
                    'id': cup.id,
                    'cup_count': cup.cup_count,
                    'buy_price': float(cup.buy_price or 0),
                    'rent_price': float(cup.rent_price or 0),
                    'deposit_amount': float(cup.deposit_amount or 0)
                })
            
            result['sizes'].append(size_info)
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================================================
# HOW TO USE THIS DEBUG ROUTE:
# ============================================================================

# 1. Add the route above to cuplock_routes.py
# 2. Restart Flask
# 3. Visit: http://127.0.0.1:5001/cuplock/debug/product/162/full-check
# 4. You'll see a complete breakdown:
#    - Product details
#    - How many sizes exist
#    - For each size: how many cups exist
#    - All the prices for sizes and cups

# This will tell you if the problem is:
# A) No sizes in database → Need to add sizes via admin
# B) Sizes exist but no cups → Need to add cups via admin
# C) Everything exists → It's an API bug (use the fix above)

# ============================================================================


# ============================================================================
# FIX FOR CUPS NOT SHOWING IN VERTICAL CUPLOCK
# ============================================================================

# The same issue is likely happening with cups - the API is trying to access
# fields that don't exist in the CuplockVerticalCup model

# ============================================================================
# STEP 1: Check your models.py CuplockVerticalCup class
# ============================================================================

# Your model has these fields:
# - id
# - vertical_size_id
# - cup_count
# - cup_image_url
# - weight_kg
# - buy_price
# - rent_price
# - deposit_amount
# - created_at

# ============================================================================
# STEP 2: Fix the API in cuplock_routes.py
# ============================================================================

# Replace the api_vertical_size_cups function with this FIXED version:

# ============================================================================
# FIX FOR CUPS 404 ERROR
# ============================================================================

# PROBLEM IDENTIFIED:
# The cups API endpoint is returning 404 (NOT FOUND)
# This means either:
# A) The route doesn't exist in cuplock_routes.py
# B) The route path is wrong
# C) The blueprint isn't registered properly

# ============================================================================
# STEP 1: Verify the route EXISTS in cuplock_routes.py
# ============================================================================

# Make sure you have this EXACT route in cuplock_routes.py:

# ============================================================================
# UPDATED STATIC_VERTICAL_CONFIG for cuplock_routes.py
# Replace the existing STATIC_VERTICAL_CONFIG in your cuplock_routes.py
# ============================================================================

STATIC_VERTICAL_CONFIG = [
    {
        'id': 9001, 
        'size_label': '1m', 
        'buy_price': 500.00, 
        'rent_price': 50.00, 
        'deposit': 100.00, 
        'cups': [1, 2]  # 1 Cup, 2 Cups
    },
    {
        'id': 9002, 
        'size_label': '1.5m', 
        'buy_price': 750.00, 
        'rent_price': 75.00, 
        'deposit': 150.00, 
        'cups': [2, 3]  # 2 Cups, 3 Cups
    },
    {
        'id': 9003, 
        'size_label': '2m', 
        'buy_price': 1000.00, 
        'rent_price': 100.00, 
        'deposit': 200.00, 
        'cups': [2, 3, 4]  # 2 Cups, 3 Cups, 4 Cups
    },
    {
        'id': 9004, 
        'size_label': '2.5m', 
        'buy_price': 1250.00, 
        'rent_price': 125.00, 
        'deposit': 250.00, 
        'cups': [2, 3, 4]  # 2 Cups, 3 Cups, 4 Cups
    },
    {
        'id': 9005, 
        'size_label': '3m', 
        'buy_price': 1500.00, 
        'rent_price': 150.00, 
        'deposit': 300.00, 
        'cups': [3, 4, 6]  # 3 Cups, 4 Cups, 6 Cups
    }
]

# ============================================================================
# CUP PRICING STRUCTURE (Static)
# This ensures all sizes use the same cup prices
# ============================================================================

CUP_PRICES = {
    1: {'buy_price': 100.00, 'rent_price': 10.00, 'deposit': 20.00},
    2: {'buy_price': 150.00, 'rent_price': 15.00, 'deposit': 30.00},
    3: {'buy_price': 200.00, 'rent_price': 20.00, 'deposit': 40.00},
    4: {'buy_price': 250.00, 'rent_price': 25.00, 'deposit': 50.00},
    6: {'buy_price': 350.00, 'rent_price': 35.00, 'deposit': 70.00}
}


# ============================================================================
# UPDATED api_vertical_size_cups FUNCTION
# Replace your existing function with this:
# ============================================================================

@cuplock_bp.route('/api/vertical/size/<int:size_id>/cups')
def api_vertical_size_cups(size_id):
    """
    Get cups for a specific vertical size
    ✅ Uses static cup pricing for consistency
    """
    try:
        logger.info(f"🔍 Fetching cups for size_id: {size_id}")
        
        # 1. Check if this is a STATIC configuration size (9001-9005)
        static_size = next((item for item in STATIC_VERTICAL_CONFIG if item['id'] == size_id), None)
        
        if static_size:
            logger.info(f"📦 Using static config for size {size_id}")
            cups_data = []
            for cup_count in static_size['cups']:
                # ✅ Use standard cup pricing
                cup_pricing = CUP_PRICES.get(cup_count, {
                    'buy_price': 50.00 * cup_count,
                    'rent_price': 5.00 * cup_count,
                    'deposit': 10.00 * cup_count
                })
                
                cups_data.append({
                    'id': f"static-{size_id}-{cup_count}",
                    'cup_count': cup_count,
                    'price': cup_pricing['buy_price'],
                    'rent_price': cup_pricing['rent_price'],
                    'deposit': cup_pricing['deposit']
                })
            
            return jsonify({
                'success': True, 
                'size_label': static_size['size_label'], 
                'cups': cups_data
            })
        
        # 2. Try to get size from database
        size = CuplockVerticalSize.query.get(size_id)
        if not size:
            logger.warning(f"⚠️ Size {size_id} not found in database")
            return jsonify({
                'success': True, 
                'size_label': 'Unknown', 
                'cups': []
            }), 200
        
        # 3. Get cups from database
        cups = CuplockVerticalCup.query.filter_by(
            vertical_size_id=size_id
        ).order_by(CuplockVerticalCup.cup_count).all()
        
        logger.info(f"📊 Found {len(cups)} cups for size {size_id}")
        
        # If no cups, return empty array
        if not cups:
            logger.info(f"ℹ️ No cups found for size_id {size_id}")
            return jsonify({
                'success': True, 
                'size_label': size.size_label, 
                'cups': []
            })
        
        # 4. Build response
        cups_data = []
        for cup in cups:
            cups_data.append({
                'id': cup.id, 
                'cup_count': cup.cup_count,
                'price': float(cup.buy_price or 0),
                'rent_price': float(cup.rent_price or 0),
                'deposit': float(cup.deposit_amount or 0)
            })
        
        logger.info(f"✅ Returning {len(cups_data)} cups for size {size_id}")
        
        return jsonify({
            'success': True, 
            'size_label': size.size_label, 
            'cups': cups_data
        })
        
    except Exception as e: 
        logger.error(f"❌ Error fetching cups for size {size_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e),
            'cups': []
        }), 200


# ============================================================================
# INSTRUCTIONS:
# ============================================================================
# 1. Replace STATIC_VERTICAL_CONFIG in cuplock_routes.py
# 2. Add CUP_PRICES dictionary to cuplock_routes.py
# 3. Replace api_vertical_size_cups function
# 4. Save the file
# ============================================================================



# ============================================================================
# STEP 2: Verify blueprint is registered in app.py
# ============================================================================

# In app.py, make sure you have this line:
# app.register_blueprint(cuplock_bp, url_prefix='/cuplock')

# Check the EXACT line - it should be:
# from cuplock_routes import cuplock_bp
# app.register_blueprint(cuplock_bp, url_prefix='/cuplock')


# ============================================================================
# STEP 3: Check the frontend JavaScript is calling the correct URL
# ============================================================================

# In cuplock_vertical.html, find the loadCups() function
# The fetch URL should be:
# fetch('/cuplock/api/vertical/size/' + encodeURIComponent(sizeId) + '/cups')

# NOT:
# fetch('/api/vertical/size/' + sizeId + '/cups')  ❌ Missing /cuplock prefix


# ============================================================================
# STEP 4: Add a test route to verify blueprint is working
# ============================================================================

@cuplock_bp.route('/test')
def test_route():
    """Test route to verify blueprint is registered"""
    return jsonify({
        'success': True,
        'message': 'Cuplock blueprint is working!',
        'blueprint_name': 'cuplock_bp'
    })

# After adding this, visit:
# http://127.0.0.1:5001/cuplock/test
# 
# If you get 404 → Blueprint is not registered properly
# If you get JSON response → Blueprint is working


# ============================================================================
# COMPLETE TROUBLESHOOTING CHECKLIST
# ============================================================================

# 1. ✅ Check cuplock_routes.py has the route
# 2. ✅ Check app.py registers the blueprint
# 3. ✅ Check frontend calls correct URL (/cuplock/api/...)
# 4. ✅ Restart Flask server
# 5. ✅ Hard refresh browser (Ctrl + Shift + R)
# 6. ✅ Check Flask console for any import errors
# 7. ✅ Visit /cuplock/test to verify blueprint works

# ============================================================================
# QUICK FIX - If blueprint registration is the issue:
# ============================================================================

# In app.py, find this line:
# app.register_blueprint(cuplock_bp, url_prefix='/cuplock')

# Make sure it's AFTER the blueprint import and BEFORE if __name__ == '__main__':

# Correct order:
# 1. from cuplock_routes import cuplock_bp
# 2. app.register_blueprint(cuplock_bp, url_prefix='/cuplock')
# 3. Other routes...
# 4. if __name__ == '__main__':

# ============================================================================


# ============================================================================
# STEP 3: Add debug route to check what cups exist
# ============================================================================

@cuplock_bp.route('/debug/vertical/size/<int:size_id>/cups')
def debug_vertical_cups(size_id):
    """
    Debug route to see what cups exist for this size
    Visit: http://127.0.0.1:5001/cuplock/debug/vertical/size/YOUR_SIZE_ID/cups
    """
    try:
        from models import CuplockVerticalSize, CuplockVerticalCup
        
        # Get the size
        size = CuplockVerticalSize.query.get(size_id)
        
        if not size:
            return jsonify({
                'error': f'Size {size_id} not found in database'
            })
        
        # Get all cups for this size
        all_cups = CuplockVerticalCup.query.filter_by(vertical_size_id=size_id).all()
        
        debug_info = {
            'size_id': size.id,
            'size_label': size.size_label,
            'total_cups': len(all_cups),
            'cups': []
        }
        
        # Show all cups with their actual field values
        for cup in all_cups:
            debug_info['cups'].append({
                'id': cup.id,
                'cup_count': cup.cup_count,
                'buy_price': float(cup.buy_price or 0),
                'rent_price': float(cup.rent_price or 0),
                'deposit_amount': float(cup.deposit_amount or 0),
                'weight_kg': float(cup.weight_kg or 0),
                'cup_image_url': cup.cup_image_url
            })
        
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================================================
# INSTRUCTIONS TO FIX:
# ============================================================================

# 1. Open cuplock_routes.py
# 2. Find the function: api_vertical_size_cups
# 3. Replace the ENTIRE function with the fixed version above
# 4. Add the debug route (optional, for testing)
# 5. Restart your Flask server
# 6. Hard refresh your browser (Ctrl + Shift + R)
# 7. Test the page again

# ============================================================================
# TROUBLESHOOTING IF CUPS STILL DON'T SHOW:
# ============================================================================

# 1. Visit the debug route to check if cups exist in database:
#    http://127.0.0.1:5001/cuplock/debug/vertical/size/YOUR_SIZE_ID/cups
#    (Replace YOUR_SIZE_ID with the actual ID from the sizes dropdown)

# 2. Check browser console for errors (F12)

# 3. Check Flask server logs for error messages

# 4. If cups don't exist in database, you need to add them via admin panel:
#    - Go to admin panel
#    - Edit the vertical cuplock product
#    - Add cup configurations for each size

# ============================================================================
# ============================================================================
# INSTRUCTIONS:
# ============================================================================
# 1. Open your cuplock_routes.py file
# 2. Find the function: api_vertical_sizes (around line 808)
# 3. Replace the ENTIRE function with the first function above
# 4. Find the function: api_vertical_size_cups
# 5. Replace the ENTIRE function with the second function above
# 6. Save the file
# 7. Restart your Flask server
# 8. Test the page again
# ============================================================================
    try:
        cups_data = []
        
        # 1. Check if this size_id belongs to our STATIC CONFIGURATION (IDs 9001-9005)
        static_size = next((item for item in STATIC_VERTICAL_CONFIG if item['id'] == size_id), None)
        
        if static_size:
            # Use the hardcoded cup counts from the config
            for cup_count in static_size['cups']:
                cups_data.append({
                    'id': f"{size_id}-{cup_count}", # Create a fake ID
                    'cup_count': cup_count,
                    'price': 50.00 * cup_count, # Dummy price: 50 per cup
                    'rent_price': 10.00 * cup_count, # Dummy rent
                    'deposit': 0
                })
            return jsonify({'success': True, 'size_label': static_size['size_label'], 'cups': cups_data})
        
        # 2. If not static, try to fetch from Database
        size = CuplockVerticalSize.query.get_or_404(size_id)
        cups = CuplockVerticalCup.query.filter_by(vertical_size_id=size_id).order_by(CuplockVerticalCup.cup_count).all()
        cups_data = [{'id': c.id, 'cup_count': c.cup_count, 'price': float(c.buy_price or 0), 'rent_price': float(c.rent_price or 0), 'deposit': float(c.deposit_amount or 0)} for c in cups]
        return jsonify({'success': True, 'size_label': size.size_label, 'cups': cups_data})
        
    except Exception as e: 
        logger.error(f"Error fetching cups: {e}"); 
        return jsonify({'success': False, 'message': 'Error fetching cups'}), 404