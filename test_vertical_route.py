#!/usr/bin/env python3
"""
Test the vertical product page to see what error occurs
"""

from app import app
from models import Product, CuplockVerticalSize

def test_vertical_product():
    with app.app_context():
        prod = Product.query.get(161)
        
        print("\n" + "="*100)
        print("TESTING VERTICAL PRODUCT PAGE")
        print("="*100)
        print(f"\nProduct ID 161: {prod.name if prod else 'NOT FOUND'}")
        
        if not prod:
            print("❌ Product not found!")
            return
        
        print(f"  is_active: {prod.is_active}")
        print(f"  category: {prod.category}")
        print(f"  cuplock_type: {prod.cuplock_type}")
        print(f"  image_url: {prod.image_url}")
        
        sizes = CuplockVerticalSize.query.filter_by(
            product_id=161,
            is_active=True
        ).all()
        
        print(f"\n  Active sizes: {len(sizes)}")
        for sz in sizes:
            print(f"    - {sz.size_label}: buy={sz.buy_price}, rent={sz.rent_price}")
        
        # Now test the route
        print("\n" + "="*100)
        print("TESTING ROUTE /product/vertical/161")
        print("="*100)
        
        client = app.test_client()
        response = client.get('/product/vertical/161')
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        
        if response.status_code == 200:
            if 'text/html' in response.content_type:
                print("✓ Returns HTML (good!)")
                if len(response.data) > 200:
                    print(f"  Response length: {len(response.data)} bytes")
            else:
                print(f"❌ Returns {response.content_type} instead of HTML")
                print("\nResponse preview:")
                print(response.data.decode('utf-8')[:500])
        else:
            print(f"❌ Status {response.status_code}")
            print("\nResponse:")
            print(response.data.decode('utf-8')[:800])

if __name__ == '__main__':
    test_vertical_product()
