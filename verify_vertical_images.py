#!/usr/bin/env python
"""Verify vertical product images are correctly configured"""

from app import app
from models import Product

def verify_vertical_images():
    with app.app_context():
        print("\n" + "="*70)
        print("🔍 VERTICAL PRODUCT IMAGE VERIFICATION")
        print("="*70)
        
        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        for product in products:
            print(f"\n📦 Product {product.id}: {product.name}")
            print(f"   Database image_url: {product.image_url}")
            
            # Check if file exists
            import os
            if product.image_url:
                # Try different path formats
                paths_to_check = [
                    product.image_url,
                    f"static/{product.image_url}",
                    f"static/images/{product.image_url.replace('images/', '')}",
                ]
                
                for path in paths_to_check:
                    if os.path.exists(path):
                        print(f"   ✅ File exists at: {path}")
                        break
                else:
                    print(f"   ⚠️  File not found at any path")
            else:
                print(f"   ❌ No image_url in database")

if __name__ == '__main__':
    verify_vertical_images()
