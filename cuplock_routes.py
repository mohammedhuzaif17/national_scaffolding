from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required
from models import db, Product, CuplockVerticalSize, CuplockLedgerSize, CuplockVerticalCup
from sqlalchemy.exc import IntegrityError
import logging
import os
import uuid
from werkzeug.utils import secure_filename

cuplock_bp = Blueprint('cuplock', __name__)
logger = logging.getLogger(__name__)

# ===========================
# FILE UPLOAD CONFIGURATION
# ===========================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff', 'ico', 'jfif', 'pjpeg', 'pjp', 'avif', 'heic', 'heif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# FIXED: Helper function to get the image path for rendering
def get_image_url(image_path):
    """Get the PRIMARY image path for rendering (to be used with url_for in templates)
    
    Handles comma-separated image lists by extracting the FIRST image only.
    Returns the first image path if valid, otherwise returns no-image.png
    
    Args:
        image_path: Single image path, or comma-separated list of paths
        
    Returns:
        A single image path suitable for <img src="{{ url_for('static', filename=path) }}">
    """
    if not image_path:
        return 'images/no-image.png'
    
    # If there are multiple images (comma-separated), take only the FIRST one
    if ',' in image_path:
        image_path = image_path.split(',')[0].strip()
    
    # Handle empty string after splitting
    if not image_path:
        return 'images/no-image.png'
    
    # Normalize path - check which prefix it should have
    if image_path.startswith('uploads/'):
        # Already has uploads/ prefix
        return image_path
    elif image_path.startswith('images/'):
        # Already has images/ prefix (for hardcoded/default images)
        return image_path
    elif image_path.startswith('static/'):
        # Has static/ prefix - remove it and return just the rest
        return image_path.replace('static/', '', 1)
    else:
        # No prefix - it's just a filename, add uploads/ prefix
        return f'uploads/{image_path}'

# ===========================
# PREDEFINED CONFIGURATIONS
# ===========================

LEDGER_SIZES = {
    '0.9m': {'weight': 3.5},
    '1m': {'weight': 4.0},
    '1.2m': {'weight': 4.5},
    '1.5m': {'weight': 5.0},
    '1.8m': {'weight': 6.0},
    '2m': {'weight': 7.0},
    '2.2m': {'weight': 7.5},
    '2.5m': {'weight': 8.0},
    '2.8m': {'weight': 8.5},
    '3m': {'weight': 9.0},
}

VERTICAL_SIZES = ['1m', '1.5m', '2m', '2.5m', '3m']

VERTICAL_CUP_OPTIONS = {
    '1m': [1, 2],
    '1.5m': [2, 3],
    '2m': [2, 3, 4],
    '2.5m': [2, 3, 4],
    '3m': [3, 4, 6],
}

# ===========================
# VERTICAL CUPLOCK ROUTES
# ===========================

@cuplock_bp.route('/admin/vertical')
@login_required
def vertical_list():
    """List all Vertical Cuplock products"""
    try:
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))

        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()

        # FIXED: Process image URLs consistently
        for product in products:
            product.display_image_url = get_image_url(product.image_url)
            logger.info(f"Product {product.id}: DB={product.image_url}, Display={product.display_image_url}")

        return render_template('cuplock_vertical_list.html', products=products)

    except Exception as e:
        logger.error(f"Error loading vertical cuplock list: {e}", exc_info=True)
        flash(f'Error loading Cuplock products. Details: {str(e)}', 'error')
        return redirect(url_for('admin_scaffoldings'))


@cuplock_bp.route('/admin/vertical/create', methods=['GET', 'POST'])
@login_required
def vertical_create():
    """Create new Vertical Cuplock product"""
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description', '')
            price = request.form.get('price', '0')

            if not name:
                flash('Product name is required', 'error')
                return render_template('cuplock_vertical_create.html')

            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0

            # Create product
            product = Product(
                name=name,
                description=description,
                category='cuplock',
                cuplock_type='vertical',
                product_type='scaffolding',
                price=price,
                is_active=True
            )

            # FIXED: Handle image upload - store only filename
            if 'image' in request.files and request.files['image']:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(upload_folder, unique_name)
                        
                        file.save(filepath)
                        # FIXED: Store with uploads/ prefix so get_image_url() doesn't double it
                        product.image_url = f'uploads/{unique_name}'
                        logger.info(f"Created product with image: uploads/{unique_name}")
                    except Exception as e:
                        logger.error(f"Error saving product image during creation: {e}")
                        flash(f'Warning: Image upload failed, but product created. Error: {str(e)}', 'warning')

            db.session.add(product)
            db.session.commit()

            flash('Vertical Cuplock product created! Now add sizes.', 'success')
            return redirect(url_for('cuplock.vertical_edit', product_id=product.id))

        return render_template('cuplock_vertical_create.html')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating vertical product: {e}")
        flash('Error creating product', 'error')
        return redirect(url_for('cuplock.vertical_list'))


@cuplock_bp.route('/admin/vertical/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def vertical_edit(product_id):
    """Edit Vertical Cuplock product"""
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))

        product = Product.query.get_or_404(product_id)

        if request.method == 'POST':
            # Update product name and description
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', '')
            
            # FIXED: Handle product image upload
            if 'image' in request.files and request.files['image']:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(upload_folder, unique_name)
                        
                        file.save(filepath)
                        # FIXED: Store with uploads/ prefix so templates display correctly
                        product.image_url = f'uploads/{unique_name}'
                        logger.info(f"Updated product image: uploads/{unique_name}")
                    except Exception as e:
                        logger.error(f"Error saving product image: {e}")
                        flash(f'Error saving image: {str(e)}', 'error')
            
            db.session.commit()
            flash('Product information updated successfully!', 'success')
            return redirect(url_for('cuplock.vertical_edit', product_id=product_id))

        sizes = CuplockVerticalSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()

        # FIXED: Get display URL for template
        image_url = get_image_url(product.image_url)

        return render_template('cuplock_vertical_edit.html',
                               product=product,
                               sizes=sizes,
                               available_sizes=VERTICAL_SIZES,
                               cup_options=VERTICAL_CUP_OPTIONS,
                               image_url=image_url)

    except Exception as e:
        logger.error(f"Error editing vertical product: {e}")
        flash('Error loading product', 'error')
        return redirect(url_for('cuplock.vertical_list'))


@cuplock_bp.route('/admin/vertical/product/<int:product_id>/delete', methods=['POST'])
@login_required
def vertical_delete_product(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403

        product = Product.query.get_or_404(product_id)

        # Soft delete - set is_active to False
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
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        if not request.form:
            return jsonify({'success': False, 'message': 'Invalid form data'}), 400

        size_label = request.form.get('size_label')
        if not size_label or size_label not in VERTICAL_SIZES:
            return jsonify({
                'success': False,
                'message': f'Invalid size. Must be: {", ".join(VERTICAL_SIZES)}'
            }), 400

        existing = CuplockVerticalSize.query.filter_by(
            product_id=product_id,
            size_label=size_label,
            is_active=True
        ).first()

        if existing:
            return jsonify({'success': False, 'message': 'Size already exists'}), 400

        def safe_decimal(val):
            try:
                return float(val) if val else 0.0
            except (TypeError, ValueError):
                return 0.0

        size = CuplockVerticalSize(
            product_id=product_id,
            size_label=size_label,
            weight=safe_decimal(request.form.get('weight')),
            buy_price=safe_decimal(request.form.get('buy_price')),
            rent_price=safe_decimal(request.form.get('rent_price')),
            deposit=safe_decimal(request.form.get('deposit')),
            is_active=True
        )

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
    """Add cup configuration to a size"""
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        size = CuplockVerticalSize.query.get_or_404(size_id)
        
        # Get cup configuration data
        cup_count = request.form.get('cup_count')
        weight_kg = request.form.get('weight_kg', 0)
        buy_price = request.form.get('buy_price', 0)
        rent_price = request.form.get('rent_price', 0)
        deposit = request.form.get('deposit', 0)
        
        if not cup_count:
            return jsonify({'success': False, 'message': 'Cup count is required'}), 400
        
        # Check for duplicate cup count
        existing = CuplockVerticalCup.query.filter_by(
            vertical_size_id=size_id,
            cup_count=int(cup_count)
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'This cup count already exists for this size'}), 400
        
        cup_image_url = ''
        
        # FIXED: Handle file upload consistently
        if 'cup_image' in request.files and request.files['cup_image']:
            file = request.files['cup_image']
            if file and file.filename and allowed_file(file.filename):
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(upload_folder, unique_name)
                
                try:
                    file.save(filepath)
                    # Store only the filename
                    cup_image_url = unique_name
                    logger.info(f"Saved cup image: {cup_image_url}")
                except Exception as e:
                    logger.error(f"Error saving cup image: {e}")
                    return jsonify({'success': False, 'message': f'Error saving image: {str(e)}'}), 500
            else:
                return jsonify({'success': False, 'message': 'Invalid image file'}), 400
        
        # Create new cup configuration
        cup = CuplockVerticalCup(
            vertical_size_id=size_id,
            cup_count=int(cup_count),
            cup_image_url=cup_image_url,
            weight_kg=float(weight_kg) if weight_kg else None,
            buy_price=float(buy_price) if buy_price else 0,
            rent_price=float(rent_price) if rent_price else 0,
            deposit_amount=float(deposit) if deposit else 0
        )
        
        db.session.add(cup)
        db.session.commit()
        
        logger.info(f"Added cup configuration {cup_count} cups to size {size_id}")
        return jsonify({'success': True, 'message': 'Cup configuration added successfully'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding cup configuration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@cuplock_bp.route('/admin/vertical/size/<int:size_id>/delete', methods=['POST'])
@login_required
def vertical_delete_size(size_id):
    """Delete vertical size (soft delete)"""
    try:
        size = CuplockVerticalSize.query.get_or_404(size_id)
        size.is_active = False
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting vertical size: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@cuplock_bp.route('/admin/vertical/cup/<int:cup_id>/delete', methods=['POST'])
@login_required
def vertical_delete_cup(cup_id):
    """Delete a cup configuration"""
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        cup = CuplockVerticalCup.query.get_or_404(cup_id)
        db.session.delete(cup)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cup configuration deleted'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting cup: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ===========================
# LEDGER CUPLOCK ROUTES
# ===========================

@cuplock_bp.route('/admin/ledger')
@login_required
def ledger_list():
    """List all Ledger Cuplock products"""
    try:
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))

        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='ledger',
            is_active=True
        ).all()

        # FIXED: Process image URLs consistently
        for product in products:
            product.display_image_url = get_image_url(product.image_url)
            logger.info(f"Product {product.id}: DB={product.image_url}, Display={product.display_image_url}")

        return render_template('cuplock_ledger_list.html', products=products)

    except Exception as e:
        logger.error(f"Error loading ledger list: {e}")
        flash('Error loading products', 'error')
        return redirect(url_for('admin_scaffoldings'))


@cuplock_bp.route('/admin/ledger/create', methods=['GET', 'POST'])
@login_required
def ledger_create():
    """Create new Ledger Cuplock product"""
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description', '')
            price = request.form.get('price', '0')

            if not name:
                flash('Product name is required', 'error')
                return render_template('cuplock_ledger_create.html', ledger_sizes=LEDGER_SIZES)

            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0

            product = Product(
                name=name,
                description=description,
                category='cuplock',
                cuplock_type='ledger',
                product_type='scaffolding',
                price=price,
                is_active=True
            )

            # FIXED: Handle image upload - store only filename
            if 'image' in request.files and request.files['image']:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(upload_folder, unique_name)
                        
                        file.save(filepath)
                        # FIXED: Store with uploads/ prefix so templates display correctly
                        product.image_url = f'uploads/{unique_name}'
                        logger.info(f"Created product with image: uploads/{unique_name}")
                    except Exception as e:
                        logger.error(f"Error saving product image during creation: {e}")
                        flash(f'Warning: Image upload failed, but product created. Error: {str(e)}', 'warning')

            db.session.add(product)
            db.session.commit()

            flash('Ledger product created — now add sizes.', 'success')
            return redirect(url_for('cuplock.ledger_edit', product_id=product.id))

        return render_template('cuplock_ledger_create.html', ledger_sizes=LEDGER_SIZES)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating ledger product: {e}")
        flash('Error creating product', 'error')
        return redirect(url_for('cuplock.ledger_list'))


@cuplock_bp.route('/admin/ledger/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def ledger_edit(product_id):
    """Edit Ledger Cuplock product"""
    try:
        if session.get('user_type') != 'admin':
            return redirect(url_for('dashboard'))

        product = Product.query.get_or_404(product_id)

        if request.method == 'POST':
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', '')
            
            # FIXED: Handle product image upload
            if 'image' in request.files and request.files['image']:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(upload_folder, unique_name)
                        
                        file.save(filepath)
                        # FIXED: Store with uploads/ prefix so templates display correctly
                        product.image_url = f'uploads/{unique_name}'
                        logger.info(f"Updated product image: uploads/{unique_name}")
                    except Exception as e:
                        logger.error(f"Error saving product image: {e}")
                        flash(f'Error saving image: {str(e)}', 'error')
            
            db.session.commit()
            flash('Product updated!', 'success')
            return redirect(url_for('cuplock.ledger_edit', product_id=product.id))

        sizes = CuplockLedgerSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()

        # FIXED: Get display URL for template
        image_url = get_image_url(product.image_url)

        return render_template('cuplock_ledger_edit.html',
                               product=product,
                               sizes=sizes,
                               ledger_sizes=LEDGER_SIZES,
                               image_url=image_url)

    except Exception as e:
        logger.error(f"Error editing ledger product: {e}")
        flash('Error loading product', 'error')
        return redirect(url_for('cuplock.ledger_list'))


@cuplock_bp.route('/admin/ledger/product/<int:product_id>/delete', methods=['POST'])
@login_required
def ledger_delete_product(product_id):
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403

        product = Product.query.get_or_404(product_id)

        # Soft delete - set is_active to False
        product.is_active = False
        db.session.commit()

        return jsonify({'success': True, 'message': 'Product deleted successfully'})

    except Exception as e:
        db.session.rollback()
        logger.exception("Error deleting ledger product")
        return jsonify({'success': False, 'message': 'Server error occurred'}), 500


@cuplock_bp.route('/admin/ledger/<int:product_id>/size/add', methods=['POST'])
@login_required
def ledger_add_size(product_id):
    """Add a new size to Ledger Cuplock"""
    try:
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        size_label = request.form.get('size_label')

        if size_label not in LEDGER_SIZES:
            return jsonify({'success': False,
                            'message': f"Size must be one of: {', '.join(LEDGER_SIZES.keys())}"}), 400

        existing = CuplockLedgerSize.query.filter_by(
            product_id=product_id,
            size_label=size_label,
            is_active=True
        ).first()

        if existing:
            return jsonify({'success': False, 'message': 'This size already exists'}), 400

        def safe_decimal(val):
            try:
                return float(val) if val else 0.0
            except (TypeError, ValueError):
                return 0.0

        weight_kg = LEDGER_SIZES[size_label]['weight']

        size = CuplockLedgerSize(
            product_id=product_id,
            size_label=size_label,
            weight_kg=weight_kg,
            buy_price=safe_decimal(request.form.get('buy_price')),
            rent_price=safe_decimal(request.form.get('rent_price')),
            deposit_amount=safe_decimal(request.form.get('deposit')),
            is_active=True
        )

        db.session.add(size)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Size added successfully'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding ledger size: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@cuplock_bp.route('/admin/ledger/size/<int:size_id>/delete', methods=['POST'])
@login_required
def ledger_delete_size(size_id):
    """Delete a ledger size (soft delete)"""
    try:
        size = CuplockLedgerSize.query.get_or_404(size_id)
        size.is_active = False
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting ledger size: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ===========================
# USER-FACING PRODUCT PAGES
# ===========================

@cuplock_bp.route('/product/vertical/<int:product_id>')
def vertical_product_page(product_id):
    product = Product.query.get_or_404(product_id)

    product.display_image_url = get_image_url(product.image_url)

    sizes = CuplockVerticalSize.query.filter_by(
        product_id=product_id,
        is_active=True
    ).all()

    return render_template(
        'cuplock_vertical.html',
        product=product,
        sizes=sizes,
        cup_options=VERTICAL_CUP_OPTIONS,
        base_price=float(product.price or 0)
    )

# ===========================
# PRICE CALCULATION HELPERS
# ===========================

def calculate_vertical_price(product, size_id, cup_id, mode='buy'):
    base_price = float(product.price or 0)

    unit_price = 0
    deposit = 0

    if mode == 'buy':
        # BUY = base + cup
        cup = CuplockVerticalCup.query.get(cup_id)
        if not cup:
            return None

        unit_price = base_price + float(cup.buy_price or 0)

    else:
        # RENT = rent + deposit
        size = CuplockVerticalSize.query.get(size_id)
        if not size:
            return None

        unit_price = float(size.rent_price or 0)
        deposit = float(size.deposit or 0)

    return {
        'price': round(unit_price, 2),
        'deposit': round(deposit, 2)
    }


@cuplock_bp.route('/product/ledger/<int:product_id>')

def ledger_product_page(product_id):
    """User page for Ledger Cuplock product"""
    try:
        logger.info(f"Loading ledger product page for product_id: {product_id}")
        
        product = Product.query.get_or_404(product_id)
        
        # FIXED: Get display URL for template
        product.display_image_url = get_image_url(product.image_url)
        
        logger.info(f"Found product: {product.name}, Image: {product.display_image_url}")

        sizes = CuplockLedgerSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()
        logger.info(f"Found {len(sizes)} sizes for this product")

        # Prepare a JSON-serializable structure for client-side use
        sizes_json = []
        for s in sizes:
            try:
                size_data = {
                    'id': s.id,
                    'label': s.size_label,
                    'weight': float(s.weight_kg or 0),
                    'buy_price': float(s.buy_price or 0),
                    'rent_price': float(s.rent_price or 0),
                    'deposit': float(s.deposit_amount or 0)
                }
                sizes_json.append(size_data)
                logger.debug(f"Added size data: {size_data}")
            except Exception as size_error:
                logger.error(f"Error processing size {s.id}: {size_error}")
                raise

        logger.info(f"Successfully prepared {len(sizes_json)} sizes for JSON")

        return render_template('cuplock_ledger.html',
                               product=product,
                               sizes=sizes,
                               sizes_json=sizes_json,
                               ledger_sizes=LEDGER_SIZES)

    except Exception as e:
        logger.error(f"Error loading ledger product page: {e}", exc_info=True)
        flash('Error loading product', 'error')
        return redirect(url_for('national_scaffoldings'))


# ===========================
# API ENDPOINTS
# ===========================

@cuplock_bp.route('/admin/api/ledger/<int:product_id>/sizes')
def api_ledger_sizes(product_id):
    """Return all sizes for this ledger product (for frontend JS)."""
    try:
        product = Product.query.get_or_404(product_id)

        sizes = CuplockLedgerSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()

        output = []
        for s in sizes:
            output.append({
                "id": s.id,
                "label": s.size_label,
                "weight": float(s.weight_kg or 0),
                "buy_price": float(s.buy_price or 0),
                "rent_price": float(s.rent_price or 0),
                "deposit": float(s.deposit_amount or 0)
            })

        return jsonify(output)

    except Exception as e:
        logger.error(f"Error loading ledger sizes API: {e}")
        return jsonify({"error": True, "message": str(e)}), 500


@cuplock_bp.route('/admin/api/vertical/<int:product_id>/sizes')
def api_vertical_sizes(product_id):
    """Return all vertical cuplock sizes for frontend JS."""
    try:
        product = Product.query.get_or_404(product_id)

        sizes = CuplockVerticalSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()

        output = []
        for s in sizes:
            output.append({
                "id": s.id,
                "label": s.size_label,
                "weight": float(s.weight) if s.weight else 0,
                "buy_price": float(s.buy_price) if s.buy_price else 0,
                "rent_price": float(s.rent_price) if s.rent_price else 0,
                "deposit": float(s.deposit) if s.deposit else 0,
                "cups": VERTICAL_CUP_OPTIONS.get(s.size_label, [])
            })

        return jsonify(output)

    except Exception as e:
        logger.error(f"Error loading vertical sizes API: {e}")
        return jsonify({"error": True, "message": str(e)}), 500


@cuplock_bp.route('/api/vertical/size/<int:size_id>/cups')
def api_vertical_cups(size_id):
    """Return all cup configurations belonging to a specific Vertical size."""
    try:
        size = CuplockVerticalSize.query.get_or_404(size_id)

        cups = CuplockVerticalCup.query.filter_by(
            vertical_size_id=size_id
        ).order_by(CuplockVerticalCup.display_order, CuplockVerticalCup.cup_count).all()

        output = []
        for c in cups:
            # FIXED: Get display URL for cup images
            image_url = get_image_url(c.cup_image_url)
            
            output.append({
                "id": c.id,
                "cup_count": c.cup_count,
                "image_url": image_url,
                "weight": float(c.weight_kg) if c.weight_kg else 0,
                "buy_price": float(c.buy_price) if c.buy_price else 0,
                "rent_price": float(c.rent_price) if c.rent_price else 0,
                "deposit": float(c.deposit_amount) if c.deposit_amount else 0
            })

        return jsonify(output)

    except Exception as e:
        logger.error(f"Error loading vertical cup API: {e}")
        return jsonify({"error": True, "message": str(e)}), 500