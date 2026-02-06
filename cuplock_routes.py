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
            flash('Invalid product type', 'error'); return redirect(url_for('national_scaffoldings'))
        
        sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        if not sizes:
            if session.get('user_type') == 'admin':
                flash(f'⚠️ No sizes configured. Please add sizes.', 'warning')
                return redirect(url_for('cuplock.vertical_edit', product_id=product_id))
            flash('⚠️ Product is being configured.', 'info')
            return redirect(url_for('national_scaffoldings', category='cuplock'))
        
        product.display_image_url = get_image_url(product.image_url)
        if product.image_url:
            product.image_urls = [get_image_url(url.strip()) for url in product.image_url.split(',') if url.strip()]
        else:
            product.image_urls = ['/static/images/no-image.png']
        
        sizes_data = [{'id': s.id, 'size_label': s.size_label, 'buy_price': float(s.buy_price or 0),
                       'rent_price': float(s.rent_price or 0), 'deposit': float(s.deposit or 0)} for s in sizes]
        
        cups_data = []
        try:
            # FIX: Get size IDs and query cups by those IDs
            size_ids = [s.id for s in sizes]
            if size_ids:
                cups = CuplockVerticalCup.query.filter(CuplockVerticalCup.vertical_size_id.in_(size_ids)).all()
                cups_data = [{'id': c.id, 'vertical_size_id': c.vertical_size_id, 'cup_label': f"{c.cup_count} Cups",
                              'cup_count': c.cup_count, 'price': float(c.buy_price or 0),
                              'rent_price': float(c.rent_price or 0), 'deposit': float(c.deposit_amount or 0)} for c in cups]
        except Exception as cup_error: logger.error(f"Error loading cups: {cup_error}")

        return render_template('cuplock_vertical.html', product=product, sizes=sizes_data, cups=cups_data)
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

@cuplock_bp.route('/api/vertical/product/<int:product_id>/sizes')
def api_vertical_sizes(product_id):
    try:
        sizes = CuplockVerticalSize.query.filter_by(product_id=product_id, is_active=True).all()
        return jsonify({'success': True, 'sizes': [{'id': s.id, 'size_label': s.size_label, 'weight': float(s.weight or 0), 'buy_price': float(s.buy_price or 0), 'rent_price': float(s.rent_price or 0), 'deposit': float(s.deposit or 0)} for s in sizes]})
    except Exception as e: logger.error(f"Error fetching vertical sizes: {e}"); return jsonify({'success': False, 'message': 'Error fetching sizes'}), 500

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

@cuplock_bp.route('/api/vertical/size/<int:size_id>/cups')
def api_vertical_size_cups(size_id):
    try:
        size = CuplockVerticalSize.query.get_or_404(size_id)
        cups = CuplockVerticalCup.query.filter_by(vertical_size_id=size_id).order_by(CuplockVerticalCup.cup_count).all()
        cups_data = [{'id': c.id, 'cup_count': c.cup_count, 'price': float(c.buy_price or 0), 'rent_price': float(c.rent_price or 0), 'deposit': float(c.deposit_amount or 0)} for c in cups]
        return jsonify({'success': True, 'size_label': size.size_label, 'cups': cups_data})
    except Exception as e: logger.error(f"Error fetching cups: {e}"); return jsonify({'success': False, 'message': 'Error fetching cups'}), 404