#!/usr/bin/env python
"""Test public product visibility and admin updates"""

import os
import sys
from app import app, db
from models import Product, CuplockVerticalSize

def test_public_product_api():
    """Test that the API endpoints return correct data"""
    with app.app_context():
        with app.test_client() as client:
            print("\n" + "="*60)
            print("🌐 TESTING PUBLIC VERTICAL PRODUCT ENDPOINTS")
            print("="*60)
            
            # Test getting product info
            product = Product.query.filter_by(
                category='cuplock',
                cuplock_type='vertical',
                is_active=True
            ).first()
            
            if not product:
                print("❌ No vertical product found!")
                return False
            
            product_id = product.id
            print(f"\n📦 Testing Product ID {product_id}: {product.name}")
            
            # Test API endpoint for sizes
            response = client.get(f'/cuplock/api/vertical/product/{product_id}/sizes')
            print(f"\n  API: /cuplock/api/vertical/product/{product_id}/sizes")
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"  ✅ Response: {data}")
                
                if data.get('success') and data.get('sizes'):
                    print(f"  ✅ Found {len(data['sizes'])} sizes")
                    
                    # Test cups endpoint
                    size_id = data['sizes'][0]['id']
                    cups_response = client.get(f'/cuplock/api/vertical/size/{size_id}/cups')
                    print(f"\n  API: /cuplock/api/vertical/size/{size_id}/cups")
                    print(f"  Status: {cups_response.status_code}")
                    
                    if cups_response.status_code == 200:
                        cups_data = cups_response.get_json()
                        print(f"  ✅ Found {len(cups_data.get('cups', []))} cup options")
                        return True
            
            print(f"  ❌ Failed to fetch sizes")
            return False

def test_admin_update():
    """Test that admin can update product"""
    with app.app_context():
        print("\n" + "="*60)
        print("👨‍💼 TESTING ADMIN UPDATE FUNCTIONALITY")
        print("="*60)
        
        # Get a product
        product = Product.query.filter_by(
            category='cuplock',
            cuplock_type='vertical',
            is_active=True
        ).first()
        
        if not product:
            print("❌ No vertical product found!")
            return False
        
        print(f"\n📦 Product: {product.name}")
        print(f"   Original description: {product.description or 'None'}")
        
        # Simulate admin update
        original_desc = product.description
        product.description = "Updated description for testing"
        db.session.commit()
        
        # Verify update
        updated = Product.query.get(product.id)
        if updated.description == "Updated description for testing":
            print(f"   ✅ Updated successfully")
            
            # Revert
            product.description = original_desc
            db.session.commit()
            print(f"   ✅ Reverted successfully")
            return True
        else:
            print(f"   ❌ Update failed!")
            return False

if __name__ == '__main__':
    try:
        api_ok = test_public_product_api()
        admin_ok = test_admin_update()
        
        print("\n" + "="*60)
        if api_ok and admin_ok:
            print("✅ ALL TESTS PASSED")
            print("="*60)
        else:
            print("❌ SOME TESTS FAILED")
            print("="*60)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
