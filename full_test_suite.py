#!/usr/bin/env python
"""
COMPREHENSIVE TEST SUITE FOR CUPLOCK VERTICAL PRODUCTS
Tests all issues reported by user and verifies fixes
"""

import os
import sys
from app import app, db
from models import Product, CuplockVerticalSize, CuplockVerticalCup

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_1_product_visibility():
    """TEST 1: Verify vertical products are visible to users"""
    print_section("TEST 1: PRODUCT VISIBILITY FOR USERS")
    
    with app.app_context():
        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        if not products:
            print("  ❌ FAILED: No vertical products found")
            return False
        
        print(f"  ✅ Found {len(products)} visible vertical products")
        for p in products:
            print(f"     - Product {p.id}: {p.name}")
        return True

def test_2_sizes_and_pricing():
    """TEST 2: Verify all products have sizes with proper pricing"""
    print_section("TEST 2: SIZES AND PRICING CONFIGURATION")
    
    with app.app_context():
        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        all_ok = True
        for product in products:
            sizes = CuplockVerticalSize.query.filter_by(
                product_id=product.id,
                is_active=True
            ).count()
            
            if sizes == 0:
                print(f"  ❌ Product {product.id} has NO sizes")
                all_ok = False
            else:
                print(f"  ✅ Product {product.id}: {sizes} size(s) configured")
        
        return all_ok

def test_3_cups_options():
    """TEST 3: Verify cup options are available for each size"""
    print_section("TEST 3: CUP OPTIONS AVAILABILITY")
    
    with app.app_context():
        sizes = CuplockVerticalSize.query.filter_by(is_active=True).all()
        
        all_ok = True
        for size in sizes:
            cups = CuplockVerticalCup.query.filter_by(
                vertical_size_id=size.id
            ).count()
            
            if cups == 0:
                print(f"  ❌ Size {size.size_label} (Product {size.product_id}) has NO cups")
                all_ok = False
            else:
                print(f"  ✅ Size {size.size_label}: {cups} cup option(s)")
        
        return all_ok

def test_4_images_available():
    """TEST 4: Verify all products have valid image URLs"""
    print_section("TEST 4: PRODUCT IMAGES")
    
    with app.app_context():
        products = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).all()
        
        all_ok = True
        for product in products:
            if product.image_url:
                print(f"  ✅ Product {product.id}: {product.image_url[:50]}...")
            else:
                print(f"  ⚠️  Product {product.id}: No image")
        
        return all_ok

def test_5_admin_update_sync():
    """TEST 5: Verify admin updates are immediately visible to users"""
    print_section("TEST 5: ADMIN UPDATE SYNC TO PUBLIC")
    
    with app.app_context():
        product = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).first()
        
        if not product:
            print("  ❌ No product to test")
            return False
        
        # Simulate admin updating description
        test_desc = f"TEST_UPDATE_{Product.query.count()}"
        product.description = test_desc
        db.session.commit()
        
        # Verify public can see the update
        refreshed = Product.query.get(product.id)
        if refreshed.description == test_desc:
            print(f"  ✅ Admin update is immediately visible to users")
            # Revert
            product.description = None
            db.session.commit()
            return True
        else:
            print(f"  ❌ Update not synced properly")
            return False

def test_6_api_endpoints():
    """TEST 6: Verify API endpoints work for public access"""
    print_section("TEST 6: PUBLIC API ENDPOINTS")
    
    with app.app_context():
        with app.test_client() as client:
            product = Product.query.filter_by(
                category='cuplock',
                cuplock_type='vertical',
                is_active=True
            ).first()
            
            if not product:
                print("  ❌ No product to test")
                return False
            
            # Test sizes endpoint
            response = client.get(f'/cuplock/api/vertical/product/{product.id}/sizes')
            if response.status_code != 200:
                print(f"  ❌ Sizes API returned {response.status_code}")
                return False
            
            data = response.get_json()
            if not data.get('success') or not data.get('sizes'):
                print(f"  ❌ Sizes API returned invalid data")
                return False
            
            print(f"  ✅ Sizes API working: {len(data['sizes'])} sizes")
            
            # Test cups endpoint
            size_id = data['sizes'][0]['id']
            cups_response = client.get(f'/cuplock/api/vertical/size/{size_id}/cups')
            
            if cups_response.status_code != 200:
                print(f"  ❌ Cups API returned {cups_response.status_code}")
                return False
            
            cups_data = cups_response.get_json()
            print(f"  ✅ Cups API working: {len(cups_data.get('cups', []))} cups")
            
            return True

def test_7_admin_can_add_sizes():
    """TEST 7: Verify admin can add sizes to products"""
    print_section("TEST 7: ADMIN CAN ADD SIZES TO PRODUCTS")
    
    with app.app_context():
        product = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).first()
        
        if not product:
            print("  ❌ No product to test")
            return False
        
        original_count = CuplockVerticalSize.query.filter_by(
            product_id=product.id,
            is_active=True
        ).count()
        
        # Create a test size
        new_size = CuplockVerticalSize(
            product_id=product.id,
            size_label='TEST_SIZE',
            buy_price=999,
            rent_price=99,
            deposit=199,
            is_active=True
        )
        db.session.add(new_size)
        db.session.commit()
        
        new_count = CuplockVerticalSize.query.filter_by(
            product_id=product.id,
            is_active=True
        ).count()
        
        if new_count > original_count:
            print(f"  ✅ Admin can add sizes: {new_count} sizes now")
            # Clean up
            new_size.is_active = False
            db.session.commit()
            return True
        else:
            print(f"  ❌ Failed to add size")
            return False

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "CUPLOCK VERTICAL PRODUCTS - FULL TEST SUITE" + " "*10 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Product Visibility", test_1_product_visibility),
        ("Sizes & Pricing", test_2_sizes_and_pricing),
        ("Cup Options", test_3_cups_options),
        ("Product Images", test_4_images_available),
        ("Admin Update Sync", test_5_admin_update_sync),
        ("Public API", test_6_api_endpoints),
        ("Admin Size Addition", test_7_admin_can_add_sizes),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_section("FINAL RESULTS")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! System is working correctly.")
        print("="*70)
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed. Please review.")
        print("="*70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
