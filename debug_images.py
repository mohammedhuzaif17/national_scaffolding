"""
DEBUG SCRIPT - Run this in Python shell or as a Flask route
to diagnose fabrication product issues
"""

from app import app
from models import Product, db

with app.app_context():
    print("=" * 60)
    print("FABRICATION PRODUCTS DEBUG")
    print("=" * 60)
    
    # 1. Check all products
    all_products = Product.query.filter_by(is_active=True).all()
    print(f"\n✅ Total active products: {len(all_products)}")
    
    # 2. Define scaffolding categories
    scaffolding_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories']
    
    # 3. Separate products
    scaffolding = [p for p in all_products if p.category in scaffolding_categories]
    fabrication = [p for p in all_products if p.category not in scaffolding_categories]
    
    print(f"📐 Scaffolding products: {len(scaffolding)}")
    print(f"🔧 Fabrication products: {len(fabrication)}")
    
    # 4. Show fabrication products
    print("\n" + "=" * 60)
    print("FABRICATION PRODUCTS:")
    print("=" * 60)
    
    if len(fabrication) == 0:
        print("❌ NO FABRICATION PRODUCTS FOUND!")
        print("\nTo fix this, you need to:")
        print("1. Add products with category NOT in:", scaffolding_categories)
        print("2. Or change existing products' category to 'fabrication'")
    else:
        for p in fabrication:
            print(f"\n📦 ID: {p.id}")
            print(f"   Name: {p.name}")
            print(f"   Category: {p.category}")
            print(f"   Price: ₹{p.price}")
            print(f"   Image: {p.image_url[:50] if p.image_url else 'None'}...")
            print(f"   Active: {p.is_active}")
    
    # 5. Check for products with NULL category
    null_category = Product.query.filter(
        Product.category == None,
        Product.is_active == True
    ).all()
    
    if null_category:
        print("\n⚠️ Products with NULL category:")
        for p in null_category:
            print(f"   - ID {p.id}: {p.name}")
    
    # 6. Check image paths
    print("\n" + "=" * 60)
    print("IMAGE PATH CHECK:")
    print("=" * 60)
    
    for p in fabrication[:3]:  # Check first 3
        if p.image_url:
            images = [img.strip() for img in p.image_url.split(',') if img.strip()]
            for img in images:
                # Check if path is correct format
                correct = not img.startswith('/static/') and not img.startswith('static/')
                status = '✅' if correct else '❌'
                print(f"{status} Product {p.id}: {img}")
                
                # Check if file exists
                import os
                file_path = os.path.join('static', img.lstrip('/'))
                exists = os.path.exists(file_path)
                print(f"   File exists: {'✅' if exists else '❌'} ({file_path})")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if len(fabrication) == 0:
        print("❌ You need to add fabrication products!")
        print("\nRun this to create test products:")
        print("""
from models import Product, db
product = Product(
    name='Test Fabrication Item',
    category='fabrication',  # or 'steel', 'custom', etc.
    price=1000.0,
    description='Test product',
    is_active=True
)
db.session.add(product)
db.session.commit()
        """)
    else:
        print("✅ You have fabrication products")
        print("   If you're still seeing errors, check:")
        print("   1. Flask logs for detailed error messages")
        print("   2. Browser console for JavaScript errors")
        print("   3. Network tab for 404 errors on images")

# To run this script:
# 1. Save as debug_fabrication.py
# 2. Run: python -c "exec(open('debug_fabrication.py').read())"
# OR add as a route in app.py:
# @app.route('/debug/fabrication')
# def debug_fabrication():
#     [paste the code here]
#     return "<pre>" + output + "</pre>"