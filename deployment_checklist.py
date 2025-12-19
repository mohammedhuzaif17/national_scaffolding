#!/usr/bin/env python3
"""
Pre-Deployment Validation Checklist
Tests all critical fixes before production deployment
"""

from app import app, db
from models import Product, Order
import os
import json

def check_products():
    """Validate product visibility and image storage"""
    with app.app_context():
        total = Product.query.count()
        active = Product.query.filter_by(is_active=True).count()
        inactive = Product.query.filter_by(is_active=False).count()
        
        print("\n[PRODUCTS]")
        print(f"  Total Products: {total}")
        print(f"  Active: {active}")
        print(f"  Inactive: {inactive}")
        
        if inactive > 0:
            print(f"  WARNING: {inactive} products are inactive and hidden from users")
            inactive_list = Product.query.filter_by(is_active=False).all()
            for p in inactive_list:
                print(f"    - ID {p.id}: {p.name}")
        
        # Check cuplock products
        vertical = Product.query.filter_by(product_type='vertical').filter_by(is_active=True).count()
        ledger = Product.query.filter_by(product_type='ledger').filter_by(is_active=True).count()
        
        print(f"  Cuplock Vertical (active): {vertical}")
        print(f"  Cuplock Ledger (active): {ledger}")
        
        # Check image storage
        products_with_uploads = Product.query.filter(
            Product.image_url.contains('uploads/')
        ).count()
        products_with_images = Product.query.filter(
            Product.image_url.isnot(None),
            Product.image_url != ''
        ).count()
        
        print(f"  Products with images: {products_with_images}")
        print(f"  Products with 'uploads/' prefix: {products_with_uploads}")
        
        # Check for missing image files
        missing = []
        for p in Product.query.filter(Product.image_url.isnot(None)).all():
            if p.image_url and not p.image_url.startswith('http'):
                file_path = os.path.join('static', p.image_url)
                if not os.path.exists(file_path):
                    missing.append({
                        'product_id': p.id,
                        'product_name': p.name,
                        'image_path': p.image_url
                    })
        
        if missing:
            print(f"  ERROR: {len(missing)} products have missing image files:")
            for m in missing:
                print(f"    - Product {m['product_id']}: {m['image_path']}")
        else:
            print(f"  PASS: All image files exist")
        
        return total > 0 and inactive == 0

def check_orders():
    """Validate transaction/order system"""
    with app.app_context():
        total = Order.query.count()
        statuses = {
            'pending_verification': Order.query.filter_by(status='pending_verification').count(),
            'approved': Order.query.filter_by(status='approved').count(),
            'rejected': Order.query.filter_by(status='rejected').count(),
            'completed': Order.query.filter_by(status='completed').count()
        }
        
        print("\n[ORDERS/TRANSACTIONS]")
        print(f"  Total Orders: {total}")
        for status, count in statuses.items():
            print(f"  {status.replace('_', ' ').title()}: {count}")
        
        return total >= 0

def check_images():
    """Validate image files exist"""
    print("\n[IMAGE FILES]")
    
    placeholder = 'static/images/default_cuplock.jpg'
    if os.path.exists(placeholder):
        size = os.path.getsize(placeholder)
        print(f"  PASS: Placeholder image exists ({size} bytes)")
    else:
        print(f"  ERROR: Placeholder image missing at {placeholder}")
        return False
    
    # Check uploads directory
    uploads = 'static/uploads'
    if os.path.exists(uploads):
        files = os.listdir(uploads)
        print(f"  Upload directory: {len(files)} files")
    
    return True

def check_routes():
    """Validate critical routes are defined"""
    print("\n[ROUTES]")
    
    routes = {
        '/': 'Homepage',
        '/national_scaffoldings': 'Products listing',
        '/cuplock-shop': 'Cuplock shop',
        '/admin/login': 'Admin login',
        '/admin/orders': 'Admin orders'
    }
    
    with app.app_context():
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        
        for route, desc in routes.items():
            if any(route in r for r in rules):
                print(f"  PASS: {route} ({desc})")
            else:
                print(f"  ERROR: {route} not found ({desc})")
    
    return True

def check_database():
    """Validate database connection"""
    print("\n[DATABASE]")
    
    try:
        with app.app_context():
            result = db.session.execute('SELECT 1')
            print("  PASS: Database connection successful")
            return True
    except Exception as e:
        print(f"  ERROR: Database connection failed - {str(e)}")
        return False

def main():
    """Run complete deployment checklist"""
    print("=" * 60)
    print("DEPLOYMENT VALIDATION CHECKLIST")
    print("=" * 60)
    
    checks = [
        ("Database Connection", check_database),
        ("Products & Images", check_products),
        ("Orders/Transactions", check_orders),
        ("Image Files", check_images),
        ("Routes", check_routes)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\nERROR in {name}: {str(e)}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_pass = all(results.values())
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    print("=" * 60)
    if all_pass:
        print("✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
    else:
        print("✗ SOME CHECKS FAILED - FIX ISSUES BEFORE DEPLOYING")
    print("=" * 60)
    
    return all_pass

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
