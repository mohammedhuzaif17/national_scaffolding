from app import app, db
from models import Product

with app.app_context():
    # Find the product named "bro bro"
    product = Product.query.filter_by(name='bro bro').first()
    
    if product:
        print(f"Found product: ID={product.id}, Name={product.name}, Category={product.category}")
        print(f"Cuplock Type: {product.cuplock_type}")
        print(f"Is Active: {product.is_active}")
        
        # Delete it
        db.session.delete(product)
        db.session.commit()
        print(f"\n✅ Product '{product.name}' (ID: {product.id}) has been deleted successfully!")
    else:
        print("❌ Product 'bro bro' not found in database")
        
        # Show all cuplock products
        all_products = Product.query.filter_by(category='cuplock').all()
        print(f"\nAvailable Cuplock products:")
        for p in all_products:
            print(f"  ID: {p.id}, Name: {p.name}, Type: {p.cuplock_type}")
