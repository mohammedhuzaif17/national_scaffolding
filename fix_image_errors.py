#!/usr/bin/env python
"""Fix image URL issues in database"""

from app import app, db
from models import Product
import os

def fix_image_errors():
    with app.app_context():
        # Find products with test_image.jpg
        test_image_products = Product.query.filter(
            Product.image_url.like('%test_image%')
        ).all()
        
        print(f'\n1. Fixing {len(test_image_products)} products with test_image.jpg')
        for p in test_image_products:
            print(f'   Clearing: {p.name}')
            p.image_url = None
        
        # Find products with comma-separated URLs (multiple images)
        comma_products = Product.query.filter(
            Product.image_url.like('%,%')
        ).all()
        
        print(f'\n2. Fixing {len(comma_products)} products with multiple images')
        for p in comma_products:
            print(f'   Product: {p.name}')
            print(f'   Old URL: {p.image_url}')
            # Keep only the first image
            images = p.image_url.split(',')
            first_image = images[0].strip()
            p.image_url = first_image
            print(f'   New URL: {p.image_url}')
        
        # Commit changes
        db.session.commit()
        print('\n✅ All fixes applied successfully!')

if __name__ == '__main__':
    fix_image_errors()
