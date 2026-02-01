#!/usr/bin/env python3
"""
Fix product 161 (vertical product) to point to an existing image
"""

from app import app, db
from models import Product

def fix_product_161():
    with app.app_context():
        prod = Product.query.get(161)
        
        if not prod:
            print("❌ Product ID 161 not found!")
            return
        
        print(f"\nProduct found: {prod.name}")
        print(f"Old image_url: {prod.image_url}")
        
        # Update to use an existing vertical image
        new_image = "uploads/25737961c4ea496ebb6daec677118fc2_vertical.jpg"
        prod.image_url = new_image
        
        try:
            db.session.commit()
            print(f"✓ Updated image_url to: {new_image}")
            print("✓ Product 161 should now display with a vertical image!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating: {e}")

if __name__ == '__main__':
    fix_product_161()
