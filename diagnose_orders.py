#!/usr/bin/env python3
"""Diagnose and fix orders with missing items"""

from app import app, db
from models import Order, OrderItem, Product, User
from sqlalchemy import text

def diagnose_orders():
    """Check detailed order information"""
    print("\n" + "="*60)
    print("DETAILED ORDER DIAGNOSIS")
    print("="*60)
    
    with app.app_context():
        all_orders = Order.query.all()
        
        print(f"\nTotal orders: {len(all_orders)}\n")
        
        orders_with_items = []
        orders_without_items = []
        
        for order in all_orders:
            if not order.items or len(order.items) == 0:
                orders_without_items.append(order)
            else:
                orders_with_items.append(order)
        
        print(f"✅ Orders WITH items: {len(orders_with_items)}")
        print(f"❌ Orders WITHOUT items: {len(orders_without_items)}")
        
        print("\n📦 ORDERS WITH ITEMS:")
        for order in orders_with_items:
            user = User.query.get(order.user_id)
            print(f"\n   Order #{order.id}:")
            print(f"   - User: {user.username if user else 'UNKNOWN'}")
            print(f"   - Items: {len(order.items)}")
            print(f"   - Total: ₹{order.total_price}")
            print(f"   - Status: {order.status}")
            
            for item in order.items:
                product = Product.query.get(item.product_id)
                category = (product.category or 'NONE').lower() if product else 'NONE'
                print(f"     └─ Product {item.product_id}: {category} (Qty: {item.quantity})")
        
        print("\n" + "="*60)
        print("❌ ORDERS WITHOUT ITEMS (These won't be visible):")
        for order in orders_without_items[:10]:  # Show first 10
            user = User.query.get(order.user_id)
            print(f"\n   Order #{order.id}:")
            print(f"   - User: {user.username if user else 'UNKNOWN'}")
            print(f"   - Created: {order.order_date}")
            print(f"   - Status: {order.status}")
            print(f"   - Total: ₹{order.total_price}")
        
        if len(orders_without_items) > 10:
            print(f"\n   ... and {len(orders_without_items) - 10} more orders without items")

def check_order_items_table():
    """Check OrderItem records"""
    print("\n" + "="*60)
    print("ORDER ITEMS TABLE CHECK")
    print("="*60)
    
    with app.app_context():
        items = OrderItem.query.all()
        print(f"\nTotal OrderItems in database: {len(items)}")
        
        # Count by order
        from sqlalchemy import func
        order_item_counts = db.session.query(
            OrderItem.order_id, 
            func.count(OrderItem.id)
        ).group_by(OrderItem.order_id).all()
        
        print(f"\nOrders with items: {len(order_item_counts)}")

def main():
    print("\n🔍 ORDER VISIBILITY ANALYSIS")
    print("="*60)
    
    diagnose_orders()
    check_order_items_table()
    
    print("\n" + "="*60)
    print("ROOT CAUSE ANALYSIS")
    print("="*60)
    print("""
The issue is that orders are being created but ORDER ITEMS are NOT being 
inserted into the OrderItem table. This causes the admin_orders route to 
filter them out because it checks if order.items is empty.

Likely causes:
1. The add_to_cart → complete_order flow is not properly inserting OrderItems
2. The checkout process is creating Order records but not OrderItem records
3. Database transaction issues preventing OrderItems from being saved

Next steps:
1. Check the complete_order route in app.py
2. Verify the add_to_cart → complete_order flow
3. Ensure OrderItems are being created before orders are marked complete
    """)

if __name__ == '__main__':
    main()
