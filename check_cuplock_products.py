from app import app, db
from models import Product

with app.app_context():
    # Count all Cuplock vertical products
    vertical_products = Product.query.filter_by(
        category='cuplock',
        cuplock_type='vertical'
    ).all()
    
    print(f"\n=== CUPLOCK VERTICAL PRODUCTS ===")
    print(f"Total found: {len(vertical_products)}\n")
    
    for p in vertical_products:
        print(f"ID: {p.id}")
        print(f"  Name: {p.name}")
        print(f"  Is Active: {p.is_active}")
        print(f"  Description: {p.description}")
        print(f"  Image URL: {p.image_url}")
        print()
