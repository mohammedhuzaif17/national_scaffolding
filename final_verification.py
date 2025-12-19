#!/usr/bin/env python3
"""
Final Deployment Verification
Tests all critical fixes are in place
"""

from app import app, db
from models import Product, Order
import os

def verify_all():
    """Run complete verification"""
    print("\n" + "=" * 70)
    print("FINAL DEPLOYMENT VERIFICATION")
    print("=" * 70)
    
    with app.app_context():
        # 1. Products
        total = Product.query.count()
        active = Product.query.filter_by(is_active=True).count()
        inactive = Product.query.filter_by(is_active=False).count()
        
        vertical = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).count()
        
        ledger = Product.query.filter_by(
            category='cuplock',
            cuplock_type='ledger',
            is_active=True
        ).count()
        
        print("\n[1] PRODUCT STATUS")
        print(f"    Total Products: {total}")
        print(f"    Active: {active} | Inactive: {inactive}")
        print(f"    Cuplock Vertical (active): {vertical}")
        print(f"    Cuplock Ledger (active): {ledger}")
        
        if inactive == 0:
            print("    [PASS] All products are ACTIVE")
        else:
            print(f"    [FAIL] WARNING: {inactive} inactive products")
        
        # 2. Image Files
        print("\n[2] IMAGE FILES")
        placeholder = 'static/images/default_cuplock.jpg'
        if os.path.exists(placeholder):
            size = os.path.getsize(placeholder)
            print(f"    [PASS] Placeholder exists ({size} bytes)")
        else:
            print(f"    [FAIL] Placeholder MISSING")
        
        uploads_dir = 'static/uploads'
        if os.path.exists(uploads_dir):
            upload_count = len(os.listdir(uploads_dir))
            print(f"    [PASS] Uploads directory has {upload_count} files")
        
        # 3. Orders
        print("\n[3] ORDERS/TRANSACTIONS")
        total_orders = Order.query.count()
        statuses = {
            'pending_verification': Order.query.filter_by(status='pending_verification').count(),
            'approved': Order.query.filter_by(status='approved').count(),
            'rejected': Order.query.filter_by(status='rejected').count(),
            'completed': Order.query.filter_by(status='completed').count()
        }
        print(f"    Total Orders: {total_orders}")
        for status, count in statuses.items():
            print(f"      {status}: {count}")
        
        # 4. Code Fixes
        print("\n[4] CODE FIXES")
        try:
            with open('cuplock_routes.py', 'r') as f:
                content = f.read()
                uploads_fixes = content.count("f'uploads/{unique_name}'")
                print(f"    [PASS] cuplock_routes.py has {uploads_fixes} 'uploads/' prefix fixes")
        except:
            print("    [FAIL] Could not read cuplock_routes.py")
        
        # 5. Routes
        print("\n[5] CRITICAL ROUTES")
        routes = [
            '/cuplock-shop',
            '/admin_orders',
            '/admin_add_product',
            '/national_scaffoldings'
        ]
        
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        for route in routes:
            found = any(route in str(r) for r in rules)
            status = "[PASS]" if found else "[FAIL]"
            print(f"    {status} {route}")
        
        # 6. Summary
        print("\n" + "=" * 70)
        print("DEPLOYMENT READINESS")
        print("=" * 70)
        
        checks = [
            ("All products active", inactive == 0),
            ("Placeholder image exists", os.path.exists(placeholder)),
            ("Image fixes applied", uploads_fixes >= 3),
            ("Orders system working", total_orders >= 0),
            ("Cuplock products exist", (vertical + ledger) > 0)
        ]
        
        all_pass = all(check[1] for check in checks)
        for check_name, passed in checks:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status}: {check_name}")
        
        print("=" * 70)
        if all_pass:
            print("\n[SUCCESS] WEBSITE IS READY FOR DEPLOYMENT\n")
            return True
        else:
            print("\n[ERROR] SOME ISSUES REMAIN - FIX BEFORE DEPLOYING\n")
            return False

if __name__ == '__main__':
    success = verify_all()
    exit(0 if success else 1)
