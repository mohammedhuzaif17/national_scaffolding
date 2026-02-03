#!/usr/bin/env python
"""Add default sizes to products without sizes"""

import os
import sys
from app import app, db
from models import Product, CuplockVerticalSize, CuplockVerticalCup

def add_default_sizes_and_cups():
    """Add default sizes and cups to vertical products that lack them"""
    with app.app_context():
        print("\n" + "="*60)
        print("📏 ADDING DEFAULT SIZES AND CUPS")
        print("="*60)
        
        # Get all vertical products
        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        for product in products:
            existing_sizes = CuplockVerticalSize.query.filter_by(
                product_id=product.id,
                is_active=True
            ).count()
            
            if existing_sizes == 0:
                print(f"\n  📦 Product ID {product.id}: {product.name}")
                print(f"     Adding default sizes...")
                
                # Default vertical sizes with prices
                default_sizes = [
                    {'label': '1m', 'buy': 500, 'rent': 100, 'deposit': 200},
                    {'label': '1.5m', 'buy': 750, 'rent': 150, 'deposit': 300},
                    {'label': '2m', 'buy': 1000, 'rent': 200, 'deposit': 400},
                ]
                
                for size_config in default_sizes:
                    size = CuplockVerticalSize(
                        product_id=product.id,
                        size_label=size_config['label'],
                        buy_price=size_config['buy'],
                        rent_price=size_config['rent'],
                        deposit=size_config['deposit'],
                        weight=float(size_config['label'].rstrip('m')),
                        is_active=True
                    )
                    db.session.add(size)
                    db.session.flush()  # Get the ID
                    
                    print(f"     ✅ Size {size_config['label']}: Buy=₹{size_config['buy']}, Rent=₹{size_config['rent']}")
                    
                    # Add cup options for this size
                    cup_configs = [
                        {'count': 1, 'multiplier': 0.5},
                        {'count': 2, 'multiplier': 1.0},
                        {'count': 3, 'multiplier': 1.5},
                        {'count': 4, 'multiplier': 2.0},
                    ]
                    
                    for cup_config in cup_configs:
                        cup = CuplockVerticalCup(
                            vertical_size_id=size.id,
                            cup_count=cup_config['count'],
                            buy_price=size_config['buy'] * cup_config['multiplier'],
                            rent_price=size_config['rent'] * cup_config['multiplier'],
                            deposit_amount=size_config['deposit'] * cup_config['multiplier']
                        )
                        db.session.add(cup)
        
        db.session.commit()
        print(f"\n✅ Sizes and cups added successfully")
        print("="*60)

if __name__ == '__main__':
    try:
        add_default_sizes_and_cups()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
