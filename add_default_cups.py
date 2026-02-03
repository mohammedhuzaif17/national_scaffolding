#!/usr/bin/env python
"""Add default cup options to vertical sizes"""

import os
import sys
from app import app, db
from models import CuplockVerticalSize, CuplockVerticalCup

def add_default_cups():
    """Add default cup options to all vertical sizes that don't have cups"""
    with app.app_context():
        print("\n" + "="*60)
        print("➕ ADDING DEFAULT CUP OPTIONS")
        print("="*60)
        
        # Get all vertical sizes without cups
        sizes = CuplockVerticalSize.query.filter_by(is_active=True).all()
        
        added_count = 0
        for size in sizes:
            existing_cups = CuplockVerticalCup.query.filter_by(
                vertical_size_id=size.id
            ).count()
            
            if existing_cups == 0:
                print(f"\n  📏 Size {size.size_label} (ID: {size.id}) - Adding cups...")
                
                # Add default cup options: 1, 2, 3, 4 cups
                # With prices relative to size
                cup_configs = [
                    {'count': 1, 'price_multiplier': 0.5},
                    {'count': 2, 'price_multiplier': 1.0},
                    {'count': 3, 'price_multiplier': 1.5},
                    {'count': 4, 'price_multiplier': 2.0},
                ]
                
                base_price = float(size.buy_price or 500)
                rent_price = float(size.rent_price or 0)
                deposit_amount = float(size.deposit or 0)
                
                for config in cup_configs:
                    cup = CuplockVerticalCup(
                        vertical_size_id=size.id,
                        cup_count=config['count'],
                        buy_price=base_price * config['price_multiplier'],
                        rent_price=rent_price * config['price_multiplier'],
                        deposit_amount=deposit_amount * config['price_multiplier']
                    )
                    db.session.add(cup)
                    print(f"    ✅ {config['count']} cup(s): ₹{cup.buy_price}")
                    added_count += 1
        
        db.session.commit()
        print(f"\n✅ Added {added_count} cup options successfully")
        print("="*60)

if __name__ == '__main__':
    try:
        add_default_cups()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
