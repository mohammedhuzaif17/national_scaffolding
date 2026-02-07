# ============================================================================
# ADD DEFAULT SIZES AND CUPS FOR VERTICAL CUPLOCK PRODUCT 162
# Save this as: setup_vertical_cuplock.py
# ============================================================================

from app import app, db
from models import Product, CuplockVerticalSize, CuplockVerticalCup

# Configuration for sizes and their cups
VERTICAL_CONFIG = [
    {
        'size_label': '1m',
        'buy_price': 500.00,
        'rent_price': 50.00,
        'deposit': 100.00,
        'cups': [
            {'cup_count': 1, 'buy_price': 100.00, 'rent_price': 10.00, 'deposit': 20.00},
            {'cup_count': 2, 'buy_price': 150.00, 'rent_price': 15.00, 'deposit': 30.00}
        ]
    },
    {
        'size_label': '1.5m',
        'buy_price': 750.00,
        'rent_price': 75.00,
        'deposit': 150.00,
        'cups': [
            {'cup_count': 2, 'buy_price': 150.00, 'rent_price': 15.00, 'deposit': 30.00},
            {'cup_count': 3, 'buy_price': 200.00, 'rent_price': 20.00, 'deposit': 40.00}
        ]
    },
    {
        'size_label': '2m',
        'buy_price': 1000.00,
        'rent_price': 100.00,
        'deposit': 200.00,
        'cups': [
            {'cup_count': 2, 'buy_price': 150.00, 'rent_price': 15.00, 'deposit': 30.00},
            {'cup_count': 3, 'buy_price': 200.00, 'rent_price': 20.00, 'deposit': 40.00},
            {'cup_count': 4, 'buy_price': 250.00, 'rent_price': 25.00, 'deposit': 50.00}
        ]
    },
    {
        'size_label': '2.5m',
        'buy_price': 1250.00,
        'rent_price': 125.00,
        'deposit': 250.00,
        'cups': [
            {'cup_count': 2, 'buy_price': 150.00, 'rent_price': 15.00, 'deposit': 30.00},
            {'cup_count': 3, 'buy_price': 200.00, 'rent_price': 20.00, 'deposit': 40.00},
            {'cup_count': 4, 'buy_price': 250.00, 'rent_price': 25.00, 'deposit': 50.00}
        ]
    },
    {
        'size_label': '3m',
        'buy_price': 1500.00,
        'rent_price': 150.00,
        'deposit': 300.00,
        'cups': [
            {'cup_count': 3, 'buy_price': 200.00, 'rent_price': 20.00, 'deposit': 40.00},
            {'cup_count': 4, 'buy_price': 250.00, 'rent_price': 25.00, 'deposit': 50.00},
            {'cup_count': 6, 'buy_price': 350.00, 'rent_price': 35.00, 'deposit': 70.00}
        ]
    }
]

def setup_vertical_cuplock(product_id=162):
    """
    Add sizes and cups to vertical cuplock product
    """
    with app.app_context():
        print("=" * 60)
        print("SETTING UP VERTICAL CUPLOCK SIZES AND CUPS")
        print("=" * 60)
        
        # 1. Check if product exists
        product = Product.query.get(product_id)
        if not product:
            print(f"❌ Product {product_id} not found!")
            return
        
        print(f"✅ Found product: {product.name}")
        print()
        
        # 2. Delete existing sizes and cups (clean slate)
        print("🧹 Cleaning existing sizes and cups...")
        existing_sizes = CuplockVerticalSize.query.filter_by(product_id=product_id).all()
        for size in existing_sizes:
            # Delete cups for this size
            CuplockVerticalCup.query.filter_by(vertical_size_id=size.id).delete()
            # Delete size
            db.session.delete(size)
        db.session.commit()
        print(f"✅ Deleted {len(existing_sizes)} old sizes")
        print()
        
        # 3. Add new sizes and cups
        print("📦 Adding new sizes and cups...")
        print()
        
        total_sizes = 0
        total_cups = 0
        
        for size_config in VERTICAL_CONFIG:
            # Create size
            new_size = CuplockVerticalSize(
                product_id=product_id,
                size_label=size_config['size_label'],
                buy_price=size_config['buy_price'],
                rent_price=size_config['rent_price'],
                deposit=size_config['deposit'],
                is_active=True
            )
            db.session.add(new_size)
            db.session.flush()  # Get the ID
            
            print(f"✅ Added size: {size_config['size_label']}")
            print(f"   Buy: ₹{size_config['buy_price']}, Rent: ₹{size_config['rent_price']}, Deposit: ₹{size_config['deposit']}")
            
            total_sizes += 1
            
            # Add cups for this size
            for cup_config in size_config['cups']:
                new_cup = CuplockVerticalCup(
                    vertical_size_id=new_size.id,
                    cup_count=cup_config['cup_count'],
                    buy_price=cup_config['buy_price'],
                    rent_price=cup_config['rent_price'],
                    deposit_amount=cup_config['deposit'],
                    weight_kg=0
                )
                db.session.add(new_cup)
                
                print(f"   🔹 {cup_config['cup_count']} Cups - Buy: ₹{cup_config['buy_price']}, Rent: ₹{cup_config['rent_price']}")
                total_cups += 1
            
            print()
        
        # 4. Commit all changes
        db.session.commit()
        
        print("=" * 60)
        print(f"✅ SUCCESS!")
        print(f"   Added {total_sizes} sizes")
        print(f"   Added {total_cups} cup options")
        print("=" * 60)
        print()
        print("🎉 Setup complete! Now test your product page:")
        print(f"   http://127.0.0.1:5001/cuplock/product/vertical/{product_id}")
        print()

if __name__ == '__main__':
    setup_vertical_cuplock(162)