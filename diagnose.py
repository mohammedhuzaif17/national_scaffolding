"""
Diagnostic Script to Find the Exact Error
Run this to see what's breaking
"""

import sys
import traceback

print("=" * 60)
print("DIAGNOSTIC: Testing Application Startup")
print("=" * 60)

try:
    print("\n1. Testing imports...")
    from app import app, db
    print("✅ App and db imported successfully")
    
    print("\n2. Testing models import...")
    from models import (
        User, Admin, AdminOTP, Product, 
        CuplockVerticalSize, CuplockVerticalCup,
        CuplockLedgerSize, Order, OrderItem
    )
    print("✅ All models imported successfully")
    
    print("\n3. Testing database connection...")
    with app.app_context():
        try:
            # Try a simple query
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    print("\n4. Testing model queries...")
    with app.app_context():
        try:
            # Test each model
            admin_count = Admin.query.count()
            print(f"✅ Admin query works ({admin_count} admins)")
            
            product_count = Product.query.count()
            print(f"✅ Product query works ({product_count} products)")
            
            # Test the problematic model
            vertical_count = CuplockVerticalSize.query.count()
            print(f"✅ CuplockVerticalSize query works ({vertical_count} sizes)")
            
            cup_count = CuplockVerticalCup.query.count()
            print(f"✅ CuplockVerticalCup query works ({cup_count} cups)")
            
        except Exception as e:
            print(f"❌ Model query failed: {e}")
            traceback.print_exc()
            raise
    
    print("\n5. Testing route handlers...")
    with app.test_client() as client:
        try:
            # Test home route
            response = client.get('/')
            print(f"✅ Home route: {response.status_code}")
            
            # Test the problematic route
            response = client.get('/national_scaffoldings')
            print(f"✅ National scaffoldings route: {response.status_code}")
            
            if response.status_code == 500:
                print(f"❌ Route returned 500. Response data:")
                print(response.data.decode('utf-8')[:500])
            
        except Exception as e:
            print(f"❌ Route test failed: {e}")
            traceback.print_exc()
            raise
    
    print("\n" + "=" * 60)
    print("✅ ALL DIAGNOSTICS PASSED")
    print("=" * 60)
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ DIAGNOSTIC FAILED")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\n" + "=" * 60)
    sys.exit(1)