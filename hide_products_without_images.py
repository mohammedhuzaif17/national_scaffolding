#!/usr/bin/env python
"""Hide products without images from the shop"""

from app import app, db
from models import Product

def hide_products_without_images():
    with app.app_context():
        # Find products without images
        products = Product.query.filter(
            (Product.image_url.is_(None)) | (Product.image_url == ''),
            Product.is_active == True
        ).all()
        
        print(f'\nFound {len(products)} products without images:')
        print('='*100)
        
        for p in products:
            print(f'Deactivating: {p.name} (Category: {p.category})')
            p.is_active = False
        
        db.session.commit()
        print(f'\n✅ Deactivated {len(products)} products without images')
        print('All remaining products will display with real images!')

if __name__ == '__main__':
    hide_products_without_images()
