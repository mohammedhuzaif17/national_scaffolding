#!/usr/bin/env python
"""Update product images to point to static/images for production persistence"""

import os
import sys
from app import app, db
from models import Product

def update_image_paths():
    """Update product images to use static/images instead of uploads"""
    with app.app_context():
        print("\n" + "="*70)
        print("🖼️  UPDATING PRODUCT IMAGES FOR PRODUCTION")
        print("="*70)
        
        # Update product 161
        product161 = Product.query.get(161)
        if product161:
            product161.image_url = 'images/vertical_product_161.jpg'
            print(f"\n✅ Product 161: Updated image to images/vertical_product_161.jpg")
        
        # Update product 162
        product162 = Product.query.get(162)
        if product162:
            product162.image_url = 'images/vertical_product_162.jpg'
            print(f"✅ Product 162: Updated image to images/vertical_product_162.jpg")
        
        db.session.commit()
        print(f"\n✅ Database updated successfully")
        print("="*70)

if __name__ == '__main__':
    try:
        update_image_paths()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
