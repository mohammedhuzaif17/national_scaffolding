#!/usr/bin/env python3
"""
Add a size to vertical product 161
"""

from app import app, db
from models import Product, CuplockVerticalSize

def add_vertical_size():
    with app.app_context():
        prod = Product.query.get(161)
        if not prod:
            print("❌ Product 161 not found")
            return
        
        print(f"Product: {prod.name}")
        print(f"Current active sizes: {len(CuplockVerticalSize.query.filter_by(product_id=161, is_active=True).all())}")
        
        # Check if 1m size already exists
        existing = CuplockVerticalSize.query.filter_by(
            product_id=161,
            size_label='1m'
        ).first()
        
        if existing:
            print(f"Size 1m already exists (active={existing.is_active})")
            if not existing.is_active:
                existing.is_active = True
                db.session.commit()
                print("✓ Activated existing 1m size")
            return
        
        # Create new size
        size = CuplockVerticalSize(
            product_id=161,
            size_label='1m',
            weight=5.0,
            buy_price=600.00,
            rent_price=120.00,
            deposit=250.00,
            is_active=True
        )
        
        db.session.add(size)
        db.session.commit()
        
        print("✓ Added 1m size to vertical product")
        print(f"  Buy Price: ₹600.00")
        print(f"  Rent Price: ₹120.00")
        print(f"  Deposit: ₹250.00")

if __name__ == '__main__':
    add_vertical_size()
