# ==========================================
# DYNAMIC IMPORT (Handles both structures)
# ==========================================
app = None
db = None
User = None
Product = None
Order = None
Admin = None
CuplockVerticalSize = None

try:
    # ATTEMPT 1: Standard structure (models are in models.py)
    from models import db, User, Product, Order, Admin, CuplockVerticalSize
    from app import app
    print("ℹ️  Imported models from models.py")
except ImportError:
    try:
        # ATTEMPT 2: Single file structure (models are in app.py)
        from app import app, db, User, Product, Order, Admin, CuplockVerticalSize
        print("ℹ️  Imported models from app.py")
    except ImportError as e:
        print("❌ CRITICAL ERROR: Could not import models.")
        print(f"   Error details: {e}")
        print("   Make sure your models are defined in either 'app.py' or 'models.py'")
        exit()

def check_data():
    with app.app_context():
        print("=" * 50)
        print("📊 CHECKING DATABASE DATA")
        print("=" * 50)

        # 1. Check USERS
        try:
            user_count = db.session.query(db.func.count(User.id)).scalar()
            print(f"\n✅ Users Table:")
            print(f"   Total Count: {user_count}")
            if user_count > 0:
                first_user = User.query.first()
                print(f"   First User: {first_user.username} ({first_user.email})")
            else:
                print("   ⚠️  No users found.")
        except Exception as e:
            print(f"   ❌ Error fetching Users: {e}")

        # 2. Check PRODUCTS
        try:
            prod_count = db.session.query(db.func.count(Product.id)).scalar()
            print(f"\n✅ Products Table:")
            print(f"   Total Count: {prod_count}")
            if prod_count > 0:
                first_prod = Product.query.first()
                print(f"   First Product: {first_prod.name}")
                print(f"   Price: {first_prod.price}")
                # Safety check for image_url in case column name differs
                img = getattr(first_prod, 'image_url', 'No image URL column')
                print(f"   Image URL: {img}")
            else:
                print("   ⚠️  No products found.")
        except Exception as e:
            print(f"   ❌ Error fetching Products: {e}")

        # 3. Check CUPLOCK VERTICAL SIZES
        try:
            size_count = db.session.query(db.func.count(CuplockVerticalSize.id)).scalar()
            print(f"\n✅ Cuplock Vertical Sizes Table:")
            print(f"   Total Count: {size_count}")
            if size_count > 0:
                first_size = CuplockVerticalSize.query.first()
                print(f"   First Size Label: {first_size.size_label}")
        except Exception as e:
            print(f"   ❌ Error fetching Vertical Sizes: {e}")

        # 4. Check ORDERS
        try:
            order_count = db.session.query(db.func.count(Order.id)).scalar()
            print(f"\n✅ Orders Table:")
            print(f"   Total Count: {order_count}")
            if order_count > 0:
                first_order = Order.query.first()
                print(f"   Latest Order Status: {first_order.status}")
        except Exception as e:
            print(f"   ❌ Error fetching Orders: {e}")

        print("\n" + "=" * 50)
        print("CHECK COMPLETE")
        print("=" * 50)

if __name__ == "__main__":
    check_data()