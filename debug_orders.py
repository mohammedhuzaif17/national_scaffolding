from app import app, db
from models import Product, Order, OrderItem

with app.app_context():
    # Check distinct categories
    categories = db.session.query(Product.category).distinct().all()
    print("[CATEGORIES]")
    for cat in categories:
        if cat[0]:
            print(f"  - {cat[0]}")
    
    # Check orders count
    total_orders = Order.query.count()
    print(f"\n[TOTAL ORDERS] {total_orders}")
    
    # Check orders with items (with join)
    orders_with_items = db.session.query(Order).join(OrderItem).distinct().count()
    print(f"[ORDERS WITH ITEMS] {orders_with_items}")
    
    # Sample order items
    print("\n[SAMPLE ORDER ITEMS]")
    items = OrderItem.query.limit(5).all()
    for item in items:
        product = Product.query.get(item.product_id)
        if product:
            print(f"  Order {item.order_id}: {product.name} (Category: {product.category})")
    
    # Test filtering for scaffolding admin (with join on Product)
    print("\n[SCAFFOLDING ADMIN - Non-fabrication orders]")
    fabrication_categories = ['steel', 'custom', 'parts', 'fabrication', 'fabrications']
    scaffolding_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        ~Product.category.in_(fabrication_categories)
    ).distinct().all()
    print(f"  Count: {len(scaffolding_orders)}")
    for order in scaffolding_orders[:3]:
        print(f"    Order #{order.id}: {order.status}")
    
    # Test filtering for fabrication admin (with join on Product)
    print("\n[FABRICATION ADMIN - Fabrication orders]")
    fabrication_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.category.in_(fabrication_categories)
    ).distinct().all()
    print(f"  Count: {len(fabrication_orders)}")
    for order in fabrication_orders[:3]:
        print(f"    Order #{order.id}: {order.status}")


