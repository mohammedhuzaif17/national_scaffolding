from app import app, db
from models import Order, OrderItem, Product

with app.app_context():
    print("[ALL PENDING ORDERS]")
    pending_orders = Order.query.filter_by(status='pending_verification').all()
    print(f"Total pending_verification orders: {len(pending_orders)}")
    for order in pending_orders:
        print(f"\n  Order #{order.id}")
        print(f"    Status: {order.status}")
        print(f"    Items count: {len(order.items)}")
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                print(f"      - {product.name} (Category: {product.category})")
            else:
                print(f"      - Product ID {item.product_id} NOT FOUND")
    
    print("\n\n[CHECKING IF PENDING ORDERS ARE JOINABLE]")
    # Orders that have items
    orders_with_items = db.session.query(Order).filter_by(status='pending_verification').join(OrderItem).distinct().all()
    print(f"Pending orders with items (via join): {len(orders_with_items)}")
    
    # Check if Orders 25-26 exist
    print("\n[CHECKING SPECIFIC ORDERS]")
    for order_id in [25, 26]:
        order = Order.query.get(order_id)
        if order:
            print(f"\nOrder #{order_id}: EXISTS")
            print(f"  Status: {order.status}")
            print(f"  Items: {len(order.items)}")
            for item in order.items:
                product = Product.query.get(item.product_id)
                print(f"    - {product.name if product else 'PRODUCT NOT FOUND'} (Cat: {product.category if product else 'N/A'})")
        else:
            print(f"\nOrder #{order_id}: NOT FOUND")
