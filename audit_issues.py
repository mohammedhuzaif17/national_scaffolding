#!/usr/bin/env python
"""
Comprehensive audit of all issues before deployment
"""

from app import app, db
from models import Product, User, Admin, Order
import os

def audit_products():
    """Check product visibility issues"""
    with app.app_context():
        print("\n" + "="*100)
        print("ISSUE #1: NEW PRODUCTS NOT VISIBLE TO USERS")
        print("="*100)
        
        all_products = Product.query.all()
        active_products = Product.query.filter_by(is_active=True).all()
        inactive_products = Product.query.filter_by(is_active=False).all()
        
        print(f"Total Products: {len(all_products)}")
        print(f"Active Products (visible to users): {len(active_products)}")
        print(f"Inactive Products (hidden from users): {len(inactive_products)}")
        
        if inactive_products:
            print("\nInactive Products (NOT showing to users):")
            for p in inactive_products:
                print(f"  ID {p.id}: {p.name} | Category: {p.category}")
        
        # Check products created recently
        from datetime import datetime, timedelta
        recent = Product.query.order_by(Product.id.desc()).limit(5).all()
        print("\nLast 5 Products Added:")
        for p in recent:
            status = "✓ VISIBLE" if p.is_active else "✗ HIDDEN"
            print(f"  ID {p.id}: {p.name} | is_active: {p.is_active} | {status}")

def audit_transactions():
    """Check transaction view issues"""
    with app.app_context():
        print("\n" + "="*100)
        print("ISSUE #2: TRANSACTION VIEW FILTERING")
        print("="*100)
        
        all_orders = Order.query.all()
        pending = Order.query.filter_by(status='pending').all()
        approved = Order.query.filter_by(status='approved').all()
        rejected = Order.query.filter_by(status='rejected').all()
        
        print(f"Total Orders: {len(all_orders)}")
        print(f"Pending: {len(pending)}")
        print(f"Approved: {len(approved)}")
        print(f"Rejected: {len(rejected)}")
        
        # Check if status column exists
        try:
            status_col = Order.__table__.columns.get('status')
            if status_col:
                print(f"✓ Status column exists in Order table")
            else:
                print(f"✗ Status column NOT found in Order table")
        except Exception as e:
            print(f"Error checking status column: {e}")

def audit_images():
    """Check image handling issues"""
    with app.app_context():
        print("\n" + "="*100)
        print("ISSUE #3: MULTIPLE IMAGES & IMAGE EDITING")
        print("="*100)
        
        # Products with comma-separated images
        all_prods = Product.query.all()
        multi_image = [p for p in all_prods if p.image_url and ',' in str(p.image_url)]
        single_image = [p for p in all_prods if p.image_url and ',' not in str(p.image_url)]
        no_image = [p for p in all_prods if not p.image_url]
        
        print(f"Products with Multiple Images (comma-separated): {len(multi_image)}")
        if multi_image:
            for p in multi_image[:3]:
                imgs = str(p.image_url).split(',')
                print(f"  ID {p.id}: {p.name} | Count: {len(imgs)}")
        
        print(f"\nProducts with Single Image: {len(single_image)}")
        print(f"Products with NO Image: {len(no_image)}")
        
        # Check if images exist on disk
        missing_images = []
        for p in all_prods:
            if p.image_url:
                imgs = str(p.image_url).split(',')
                for img in imgs:
                    img = img.strip()
                    path = os.path.join('static', img)
                    if not os.path.exists(path):
                        missing_images.append({'product': p.name, 'image': img})
        
        if missing_images:
            print(f"\n✗ Missing Images on Disk: {len(missing_images)}")
            for item in missing_images[:5]:
                print(f"  {item['product']}: {item['image']}")
        else:
            print(f"\n✓ All images exist on disk")

def audit_homepage():
    """Check homepage visibility"""
    with app.app_context():
        print("\n" + "="*100)
        print("ISSUE #4: HOMEPAGE PRODUCTS NOT VISIBLE WITHOUT LOGIN")
        print("="*100)
        
        # Check what products would be visible on homepage
        valid_types = ['Aluminium Scaffolding', 'H-Frames', 'Cuplock', 'Accessories', 'scaffolding', 'cuplock_vertical', 'cuplock_ledger']
        homepage_products = Product.query.filter(
            Product.product_type.in_(valid_types),
            Product.is_active == True
        ).all()
        
        print(f"Products visible on /national_scaffoldings (no login needed): {len(homepage_products)}")
        
        if len(homepage_products) == 0:
            print("✗ NO PRODUCTS VISIBLE - This is the bug!")
        else:
            print(f"✓ {len(homepage_products)} products should be visible")

if __name__ == '__main__':
    print("STARTING COMPREHENSIVE AUDIT...")
    print("This will identify all issues before deployment\n")
    
    try:
        audit_products()
        audit_transactions()
        audit_images()
        audit_homepage()
        
        print("\n" + "="*100)
        print("AUDIT COMPLETE")
        print("="*100)
    except Exception as e:
        print(f"Error during audit: {e}")
        import traceback
        traceback.print_exc()
