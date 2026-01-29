from app import app, db
from models import Product, Order, OrderItem

with app.app_context():
    print("[FINAL VERIFICATION - ORDER FILTERING]")
    print()
    
    # Scaffolding categories
    scaffolding_categories = ['aluminium', 'h-frames', 'cuplock', 'accessories', 'vertical']
    scaffolding_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.category.in_(scaffolding_categories)
    ).distinct().order_by(Order.order_date.desc()).all()
    
    # Fabrication categories
    fabrication_categories = ['steel', 'custom', 'parts', 'fabrication', 'fabrications']
    fabrication_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.category.in_(fabrication_categories)
    ).distinct().order_by(Order.order_date.desc()).all()
    
    print(f"[SCAFFOLDING ADMIN] ({len(scaffolding_orders)} orders)")
    print("Recent pending orders:")
    pending_scaffolding = [o for o in scaffolding_orders if o.status == 'pending_verification'][:3]
    for order in pending_scaffolding:
        print(f"  Order #{order.id}: {order.status} ({len(order.items)} items)")
    
    print()
    print(f"[FABRICATION ADMIN] ({len(fabrication_orders)} orders)")
    print("Recent pending orders:")
    pending_fabrication = [o for o in fabrication_orders if o.status == 'pending_verification'][:3]
    for order in pending_fabrication:
        print(f"  Order #{order.id}: {order.status} ({len(order.items)} items)")
    
    print()
    print(f"[ORDERS #25-26 VISIBILITY]")
    for oid in [25, 26]:
        o = Order.query.get(oid)
        if o:
            in_scaff = any(x.id == oid for x in scaffolding_orders)
            in_fab = any(x.id == oid for x in fabrication_orders)
            print(f"Order #{oid}: {o.status}")
            print(f"  Visible to Scaffolding Admin: {in_scaff}")
            print(f"  Visible to Fabrication Admin: {in_fab}")
