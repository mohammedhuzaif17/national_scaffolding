from app import app, db
from models import Product

with app.app_context():
    print("\n=== CHECKING ALL CUPLOCK PRODUCTS ===\n")
    
    # Get all Cuplock products (active or not)
    all_cuplock = Product.query.filter_by(category='cuplock').all()
    print(f"Total Cuplock products (all): {len(all_cuplock)}")
    
    # Get only active ones
    active_vertical = Product.query.filter_by(
        category='cuplock',
        cuplock_type='vertical',
        is_active=True
    ).all()
    print(f"Active Vertical Cuplock: {len(active_vertical)}")
    
    active_ledger = Product.query.filter_by(
        category='cuplock',
        cuplock_type='ledger',
        is_active=True
    ).all()
    print(f"Active Ledger Cuplock: {len(active_ledger)}")
    
    print("\n=== VERTICAL PRODUCTS (ACTIVE) ===")
    for p in active_vertical:
        print(f"{p.id}: {p.name}")
    
    print("\n=== LEDGER PRODUCTS (ACTIVE) ===")
    for p in active_ledger:
        print(f"{p.id}: {p.name}")
    
    # Check if there are any Cuplock products NOT marked as active
    inactive_cuplock = Product.query.filter_by(
        category='cuplock',
        is_active=False
    ).all()
    print(f"\n\nInactive Cuplock products: {len(inactive_cuplock)}")
    if inactive_cuplock:
        for p in inactive_cuplock:
            print(f"  {p.id}: {p.name} (type={p.cuplock_type})")
