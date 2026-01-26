from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required
from models import db, Product, CuplockVerticalSize, CuplockLedgerSize, CuplockVerticalCup
from sqlalchemy.exc import IntegrityError
import logging
import os
import uuid
from werkzeug.utils import secure_filename
from flask import render_template, abort, current_app
from models import Product, CuplockVerticalSize
from utils import get_image_url

from models import Product, CuplockLedgerSize

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
    if not image_path:
        return 'images/no-image.png'

    # If multiple images exist, take only the first one
    if ',' in image_path:
        image_path = image_path.split(',')[0].strip()

    if not image_path:
        return 'images/no-image.png'

    # Remove static/ if present
    if image_path.startswith('static/'):
        image_path = image_path.replace('static/', '', 1)

    # Valid prefixes
    if image_path.startswith(('uploads/', 'images/')):
        return image_path

    # Plain filename → assume uploads/
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
            flash('Admin access required', 'error')
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

            # ✅ Handle multiple images upload
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
                            logger.info(f"Uploaded image: uploads/{unique_name}")
                            
                        except Exception as e:
                            logger.error(f"Error saving image: {e}")
                            flash(f'Warning: Failed to upload image {file.filename}', 'warning')
            
            # Join multiple images with comma
            if uploaded_images:
                product.image_url = ','.join(uploaded_images)
                logger.info(f"Product images: {product.image_url}")
            else:
                logger.warning("No images uploaded for new product")

            db.session.add(product)
            db.session.commit()

            flash('✅ Vertical Cuplock product created! Now add sizes and cup configurations.', 'success')
            
            # ✅ FIX: Redirect to ADMIN edit page, not user product page
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
    """Edit Vertical Cuplock product - ADMIN ONLY"""
    try:
        # ✅ CRITICAL: Check admin access FIRST
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))

        product = Product.query.get_or_404(product_id)

        if request.method == 'POST':
            # Update product name and description
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', '')
            
            # ✅ Handle multiple image uploads
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
                            logger.info(f"Updated product image: uploads/{unique_name}")
                        except Exception as e:
                            logger.error(f"Error saving product image: {e}")
                            flash(f'Error saving image: {str(e)}', 'error')
                
                # Only update if new images were uploaded
                if uploaded_images:
                    product.image_url = ','.join(uploaded_images)
            
            db.session.commit()
            flash('✅ Product information updated successfully!', 'success')
            return redirect(url_for('cuplock.vertical_edit', product_id=product_id))

        sizes = CuplockVerticalSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()

        # ✅ Get display URL for template
        image_url = get_image_url(product.image_url) if product.image_url else 'images/no-image.png'

        return render_template('cuplock_vertical_edit.html',
                               product=product,
                               sizes=sizes,
                               available_sizes=VERTICAL_SIZES,
                               cup_options=VERTICAL_CUP_OPTIONS,
                               image_url=image_url)

    except Exception as e:
        logger.error(f"Error editing vertical product: {e}", exc_info=True)
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

        buy_price = safe_decimal(request.form.get('buy_price'))
        rent_price = safe_decimal(request.form.get('rent_price'))
        
        # ✅ VALIDATION: Ensure at least one price is set
        if buy_price == 0 and rent_price == 0:
            return jsonify({
                'success': False,
                'message': 'At least one price (buy or rent) must be greater than 0'
            }), 400

        size = CuplockVerticalSize(
            product_id=product_id,
            size_label=size_label,
            weight=safe_decimal(request.form.get('weight')),
            buy_price=buy_price,
            rent_price=rent_price,
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
        weight_kg = request.form.get('weight_kg', 0)  # Default to 0 if not provided
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
        
        # Handle file upload
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
                    cup_image_url = unique_name
                    logger.info(f"Saved cup image: {cup_image_url}")
                except Exception as e:
                    logger.error(f"Error saving cup image: {e}")
                    return jsonify({'success': False, 'message': f'Error saving image: {str(e)}'}), 500
        
        # FIXED: Ensure weight_kg has a value (default to 0.0 if not provided)
        weight_value = float(weight_kg) if weight_kg and str(weight_kg).strip() else 0.0
        
        # Create new cup configuration
        cup = CuplockVerticalCup(
            vertical_size_id=size_id,
            cup_count=int(cup_count),
            cup_image_url=cup_image_url,
            weight_kg=weight_value,  # Always provide a value
            buy_price=float(buy_price) if buy_price and str(buy_price).strip() else 0,
            rent_price=float(rent_price) if rent_price and str(rent_price).strip() else 0,
            deposit_amount=float(deposit) if deposit and str(deposit).strip() else 0
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
    """User-facing vertical product page - PUBLIC"""
    try:
        # ✅ NO admin check here - this is for customers
        
        product = Product.query.filter_by(
            id=product_id,
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).first_or_404()

        sizes = CuplockVerticalSize.query.filter_by(
            product_id=product.id,
            is_active=True
        ).order_by(CuplockVerticalSize.size_label).all()

        if not sizes:
            current_app.logger.warning(f"No sizes found for vertical product {product_id}")
            flash('This product has no sizes configured. Please contact support.', 'warning')
            return redirect(url_for('debug_products'))

        # Validate and clean sizes data
        valid_sizes = []
        has_valid_prices = False
        
        for size in sizes:
            buy_price = float(size.buy_price) if size.buy_price and size.buy_price > 0 else 0
            rent_price = float(size.rent_price) if size.rent_price and size.rent_price > 0 else 0
            deposit = float(size.deposit) if size.deposit and size.deposit >= 0 else 0
            
            if buy_price > 0 or rent_price > 0:
                has_valid_prices = True
            
            size.buy_price = buy_price
            size.rent_price = rent_price
            size.deposit = deposit
            
            valid_sizes.append(size)
            
            if buy_price == 0 and rent_price == 0:
                current_app.logger.warning(
                    f"Product {product_id}, Size {size.size_label}: Both prices are 0"
                )

        if not valid_sizes:
            current_app.logger.error(f"No valid sizes for product {product_id}")
            flash('This product is not properly configured.', 'error')
            return redirect(url_for('debug_products'))
        
        if not has_valid_prices:
            flash('⚠️ This product has no prices configured. Please contact admin.', 'warning')

        base_price = float(valid_sizes[0].buy_price or 0)

        # Fix image path
        if product.image_url:
            image_urls = [url.strip() for url in product.image_url.split(',') if url.strip()]
            if image_urls:
                first_image = image_urls[0]
                if not first_image.startswith(('uploads/', 'images/', 'static/')):
                    first_image = f'uploads/{first_image}'
                if first_image.startswith('static/'):
                    first_image = first_image.replace('static/', '', 1)
                product.display_image_url = first_image
            else:
                product.display_image_url = 'images/no-image.png'
        else:
            product.display_image_url = 'images/no-image.png'

        return render_template(
            'cuplock_vertical.html',
            product=product,
            sizes=valid_sizes,
            cup_options=VERTICAL_CUP_OPTIONS,
            base_price=base_price
        )

    except Exception as e:
        current_app.logger.error(f"Vertical product error: {e}", exc_info=True)
        flash('Error loading product. Please try again.', 'error')
        return redirect(url_for('debug_products'))


@cuplock_bp.route('/product/ledger/<int:product_id>')
def ledger_product_page(product_id):
    product = Product.query.filter_by(
        id=product_id,
        category='cuplock',
        cuplock_type='ledger',
        is_active=True
    ).first_or_404()

    sizes = CuplockLedgerSize.query.filter_by(
        product_id=product.id,
        is_active=True
    ).all()

    product.display_image_url = get_image_url(product.image_url)

    return render_template(
        'cuplock_ledger.html',
        product=product,
        sizes=sizes
    )


# ===========================
# API ENDPOINTS
# ===========================
@cuplock_bp.route('/cuplock/api/vertical/product/<int:product_id>/sizes')
def api_vertical_sizes(product_id):
    """API endpoint to get sizes for a vertical cuplock product"""
    try:
        from models import CuplockVerticalSize
        
        sizes = CuplockVerticalSize.query.filter_by(
            product_id=product_id,
            is_active=True
        ).order_by(CuplockVerticalSize.display_order.asc(), CuplockVerticalSize.size_label.asc()).all()
        
        size_data = []
        for size in sizes:
            size_data.append({
                'id': size.id,
                'size_label': size.size_label,
                'weight': float(size.weight) if size.weight else 0,
                'buy_price': float(size.buy_price) if size.buy_price else 0,
                'rent_price': float(size.rent_price) if size.rent_price else 0,
                'deposit': float(size.deposit) if size.deposit else 0
            })
        
        return jsonify({
            'success': True,
            'sizes': size_data
        })
    except Exception as e:
        logger.error(f"Error fetching vertical sizes: {e}")
        return jsonify({
            'success': False,
            'message': 'Error fetching sizes'
        }), 500
 

@cuplock_bp.route('/admin/api/ledger/<int:product_id>/sizes')
def admin_api_ledger_sizes(product_id):
    sizes = CuplockLedgerSize.query.filter_by(
        product_id=product_id,
        is_active=True
    ).order_by(CuplockLedgerSize.size_label).all()

    return jsonify([
        {
            "id": s.id,
            "label": s.size_label,
            "weight": float(s.weight_kg or 0),
            "buy_price": float(s.buy_price or 0),
            "rent_price": float(s.rent_price or 0),
            "deposit": float(s.deposit_amount or 0)
        }
        for s in sizes
    ])


@cuplock_bp.route('/admin/api/vertical/<int:product_id>/sizes')
def api_admin_vertical_sizes(product_id):
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