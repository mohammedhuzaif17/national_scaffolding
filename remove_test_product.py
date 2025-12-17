#!/usr/bin/env python3
"""Remove the 'bro bro' test product from database"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Product

if __name__ == '__main__':
    with app.app_context():
        # Find the product named "bro bro"
        product = Product.query.filter_by(name='bro bro').first()
        
        if product:
            print(f"Found product: ID={product.id}, Name={product.name}, Category={product.category}")
            print(f"Cuplock Type: {product.cuplock_type}")
            print(f"Is Active: {product.is_active}")
            
            # Delete it
            product_id = product.id
            db.session.delete(product)
            db.session.commit()
            print(f"\n✅ Product 'bro bro' (ID: {product_id}) has been deleted successfully!")
        else:
            print("❌ Product 'bro bro' not found in database")
            
            # Show all cuplock products
            all_products = Product.query.filter_by(category='cuplock').all()
            if all_products:
                print(f"\nAvailable Cuplock products:")
                for p in all_products:
                    print(f"  ID: {p.id}, Name: {p.name}, Type: {p.cuplock_type}, Active: {p.is_active}")
            else:
                print("\nNo Cuplock products found")
