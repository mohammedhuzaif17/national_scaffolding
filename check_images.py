#!/usr/bin/env python
"""Check image statistics"""

from app import app, db
from models import Product

with app.app_context():
    # Get statistics
    total = Product.query.filter_by(is_active=True).count()
    with_images = Product.query.filter_by(is_active=True).filter(Product.image_url.isnot(None)).count()
    without_images = total - with_images
    
    print(f'\nProduct Statistics:')
    print(f'  Total Active: {total}')
    print(f'  With Images: {with_images}')
    print(f'  Without Images (Showing Placeholder): {without_images}')
    print()
    
    # Show first few with images
    print('Products WITH Images (sample):')
    print('='*80)
    with_img = Product.query.filter_by(is_active=True).filter(Product.image_url.isnot(None)).limit(5).all()
    for p in with_img:
        print(f'✓ {p.name}')
    
    print()
    print('Products WITHOUT Images (showing placeholder):')
    print('='*80)
    without_img = Product.query.filter_by(is_active=True).filter(Product.image_url.is_(None)).limit(5).all()
    for p in without_img:
        print(f'✗ {p.name}')
