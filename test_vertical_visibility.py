#!/usr/bin/env python
"""Test vertical product visibility and data sync"""

import os
import sys
from app import app, db
from models import Product, CuplockVerticalSize, CuplockVerticalCup

def test_vertical_products():
    """Check if vertical products exist and have sizes"""
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VERTICAL PRODUCTS VISIBILITY TEST")
        print("="*60)
        
        # Check for vertical products
        vertical_products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        print(f"\n✅ Found {len(vertical_products)} active vertical products:")
        
        for product in vertical_products:
            print(f"\n  📦 Product ID {product.id}: {product.name}")
            print(f"     Image URL: {product.image_url or 'No image'}")
            print(f"     Description: {product.description[:50] if product.description else 'None'}...")
            
            # Check sizes
            sizes = CuplockVerticalSize.query.filter_by(
                product_id=product.id,
                is_active=True
            ).all()
            
            print(f"     📏 Sizes: {len(sizes)} configured")
            for size in sizes:
                print(f"        - {size.size_label}: Buy=₹{size.buy_price}, Rent=₹{size.rent_price}, Deposit=₹{size.deposit}")
                
                cups = CuplockVerticalCup.query.filter_by(
                    vertical_size_id=size.id
                ).all()
                print(f"          🥤 {len(cups)} cup options")
                for cup in cups:
                    print(f"             - {cup.cup_count} cups (₹{cup.buy_price})")
        
        if not vertical_products:
            print("  ❌ No vertical products found!")
            return False
        
        print("\n" + "="*60)
        print("✅ TEST PASSED: Products are visible in database")
        print("="*60)
        return True

if __name__ == '__main__':
    try:
        test_vertical_products()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
