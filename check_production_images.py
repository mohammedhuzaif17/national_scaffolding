#!/usr/bin/env python
"""Check what images exist and fix broken references"""

import os
import sys
from app import app, db
from models import Product

def check_and_fix_images():
    """Check all product images and list what actually exists"""
    with app.app_context():
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        
        print("\n" + "="*70)
        print("📸 CHECKING PRODUCT IMAGES AND FILES")
        print("="*70)
        
        # List actual files
        if os.path.exists(upload_folder):
            files = os.listdir(upload_folder)
            vertical_images = [f for f in files if 'vertical' in f.lower()]
            print(f"\n📁 Files in {upload_folder}:")
            print(f"   Total files: {len(files)}")
            print(f"   Vertical-related: {len(vertical_images)}")
            
            if vertical_images:
                print(f"\n   Available vertical images:")
                for img in vertical_images[:10]:  # Show first 10
                    print(f"   - {img}")
        else:
            print(f"❌ Upload folder not found: {upload_folder}")
            return False
        
        # Check product image references
        print(f"\n📦 PRODUCT IMAGE REFERENCES:")
        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        for product in products:
            print(f"\n   Product {product.id}: {product.name}")
            print(f"   Current image_url: {product.image_url}")
            
            if product.image_url:
                images = [url.strip() for url in product.image_url.split(',')]
                for img in images:
                    # Normalize path
                    normalized = img.lstrip('/')
                    if normalized.startswith('static/'):
                        normalized = normalized.replace('static/', '', 1)
                    
                    filepath = os.path.join(upload_folder, normalized)
                    exists = os.path.exists(filepath)
                    status = "✅ EXISTS" if exists else "❌ MISSING"
                    print(f"   - {status}: {normalized}")
        
        return True

if __name__ == '__main__':
    try:
        check_and_fix_images()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
