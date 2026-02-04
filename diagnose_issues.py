#!/usr/bin/env python3
"""Diagnose admin login, orders, and database issues"""

import sys
from app import app, db
from models import Admin, Order, User

def check_database():
    """Check database connection and data"""
    print("\n" + "="*60)
    print("DATABASE DIAGNOSTICS")
    print("="*60)
    
    try:
        with app.app_context():
            # Test connection
            result = db.session.execute("SELECT 1")
            print("✅ Database connection: OK")
            
            # Check admins
            admins = Admin.query.all()
            print(f"\n👤 Total Admins: {len(admins)}")
            for admin in admins:
                print(f"   - ID: {admin.id}")
                print(f"     Username: {admin.username}")
                print(f"     Panel Type: {admin.panel_type}")
                print(f"     Email: {admin.email}")
                print()
            
            # Check orders
            orders = Order.query.all()
            print(f"\n📦 Total Orders: {len(orders)}")
            
            if orders:
                print("\n⚠️  Recent Orders:")
                for order in orders[-10:]:
                    user = User.query.get(order.user_id)
                    print(f"   - Order {order.id}:")
                    print(f"     User: {user.username if user else 'UNKNOWN'}")
                    print(f"     Status: {order.status}")
                    print(f"     Total: ₹{order.total_price}")
                    print(f"     Created: {order.order_date}")
                    print()
            else:
                print("   ⚠️  No orders found in database")
            
            return True
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_admin_login():
    """Test admin login logic"""
    print("\n" + "="*60)
    print("ADMIN LOGIN DIAGNOSTICS")
    print("="*60)
    
    with app.app_context():
        # Check if admin exists for scaffolding
        admin = Admin.query.filter_by(username='admin', panel_type='scaffolding').first()
        
        if admin:
            print("✅ Scaffolding admin found:")
            print(f"   - Username: {admin.username}")
            print(f"   - Password hash exists: {bool(admin.password_hash)}")
            print(f"   - Panel type: {admin.panel_type}")
        else:
            print("❌ Scaffolding admin NOT found")
            print("   Creating default scaffolding admin...")
            try:
                from werkzeug.security import generate_password_hash
                new_admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    email='admin@nationalscaffolding.com',
                    panel_type='scaffolding'
                )
                db.session.add(new_admin)
                db.session.commit()
                print("✅ Default scaffolding admin created")
                print("   - Username: admin")
                print("   - Password: admin123")
            except Exception as e:
                print(f"❌ Error creating admin: {str(e)}")
        
        # Check fabrication admin
        fab_admin = Admin.query.filter_by(username='admin', panel_type='fabrication').first()
        if fab_admin:
            print("\n✅ Fabrication admin found")
        else:
            print("\n❌ Fabrication admin NOT found")
            try:
                from werkzeug.security import generate_password_hash
                new_admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    email='admin@nationalscaffolding.com',
                    panel_type='fabrication'
                )
                db.session.add(new_admin)
                db.session.commit()
                print("✅ Default fabrication admin created")
            except Exception as e:
                print(f"❌ Error creating admin: {str(e)}")

def check_admin_orders_route():
    """Check admin_orders route logic"""
    print("\n" + "="*60)
    print("ADMIN ORDERS ROUTE DIAGNOSTICS")
    print("="*60)
    
    with app.app_context():
        # Get all orders
        all_orders = Order.query.all()
        print(f"Total orders in DB: {len(all_orders)}")
        
        # Simulate what admin_orders route does
        print("\n📋 Scaffolding Admin would see:")
        scaffolding_orders = Order.query.all()
        print(f"   Orders: {len(scaffolding_orders)}")
        
        print("\n📋 Fabrication Admin would see:")
        fabrication_orders = Order.query.all()
        print(f"   Orders: {len(fabrication_orders)}")
        
        # Check order items
        print("\n📦 Order Item Counts:")
        for order in all_orders[-5:]:
            item_count = len(order.items) if order.items else 0
            print(f"   Order {order.id}: {item_count} items")

def main():
    print("\n🔍 NATIONAL SCAFFOLDING - ISSUE DIAGNOSTICS")
    print("="*60)
    
    check_database()
    check_admin_login()
    check_admin_orders_route()
    
    print("\n" + "="*60)
    print("DIAGNOSTICS COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
