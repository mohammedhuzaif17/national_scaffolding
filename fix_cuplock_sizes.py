from models import db, Product, CuplockVerticalSize, CuplockLedgerSize
from app import app
from sqlalchemy import text

with app.app_context():
    print("Adding missing sizes to cuplock products...")
    
    try:
        # Clear existing (in case there are duplicates)
        db.session.execute(text("DELETE FROM cuplock_vertical_sizes WHERE product_id IN (161, 163)"))
        db.session.execute(text("DELETE FROM cuplock_ledger_sizes WHERE product_id = 136"))
        
        # Add vertical sizes for product 161
        db.session.execute(text("""
            INSERT INTO cuplock_vertical_sizes (product_id, size_label, weight, buy_price, rent_price, deposit, is_active)
            VALUES 
            (161, '1M x 1M', 25, 500, 100, 200, 1),
            (161, '1.5M x 1.5M', 40, 750, 150, 300, 1),
            (161, '2M x 2M', 60, 1000, 200, 400, 1)
        """))
        
        # Add vertical sizes for product 163  
        db.session.execute(text("""
            INSERT INTO cuplock_vertical_sizes (product_id, size_label, weight, buy_price, rent_price, deposit, is_active)
            VALUES 
            (163, '1.5M x 1.5M', 40, 800, 160, 320, 1),
            (163, '2M x 2M', 60, 1200, 240, 480, 1),
            (163, '2.5M x 2.5M', 80, 1500, 300, 600, 1)
        """))
        
        # Add ledger sizes for product 136
        db.session.execute(text("""
            INSERT INTO cuplock_ledger_sizes (product_id, size_label, weight_kg, buy_price, rent_price, deposit_amount, is_active)
            VALUES 
            (136, '2M', 50, 400, 80, 150, 1),
            (136, '2.5M', 60, 500, 100, 200, 1),
            (136, '3M', 75, 600, 120, 250, 1)
        """))
        
        db.session.commit()
        print("SUCCESS: All sizes added!")
        
        # Verify
        print("\nVerifying...")
        v161 = CuplockVerticalSize.query.filter_by(product_id=161, is_active=True).count()
        v163 = CuplockVerticalSize.query.filter_by(product_id=163, is_active=True).count()
        l136 = CuplockLedgerSize.query.filter_by(product_id=136, is_active=True).count()
        
        print(f"Product 161: {v161} sizes")
        print(f"Product 163: {v163} sizes")
        print(f"Product 136: {l136} sizes")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
