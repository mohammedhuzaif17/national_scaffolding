from app import app, db
from models import Product, Order, OrderItem

with app.app_context():
    print("[TESTING NEW FILTERING LOGIC]")
    
    # Scaffolding categories
    scaffolding_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories', 'vertical']
    scaffolding_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.category.in_(scaffolding_categories)
    ).distinct().all()
    print(f"Scaffolding Admin orders: {len(scaffolding_orders)}")
    
    # Fabrication categories
    fabrication_categories = ['steel', 'custom', 'parts', 'fabrication', 'fabrications']
    fabrication_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.category.in_(fabrication_categories)
    ).distinct().all()
    print(f"Fabrication Admin orders: {len(fabrication_orders)}")
    
    # Check if order 25 and 26 appear in scaffolding
    print(f"\nOrder 25 in scaffolding admin: {any(o.id == 25 for o in scaffolding_orders)}")
    print(f"Order 26 in scaffolding admin: {any(o.id == 26 for o in scaffolding_orders)}")
    
    # Check if order 25 appears in fabrication
    print(f"Order 25 in fabrication admin: {any(o.id == 25 for o in fabrication_orders)}")
