#!/usr/bin/env python3
"""
Fix ledger products (136, 138) to point to existing ledger images
"""

from app import app, db
from models import Product

def fix_ledger_products():
    with app.app_context():
        # Product 136: Test Ledger Cuplock
        prod136 = Product.query.get(136)
        if prod136:
            prod136.image_url = "uploads/cb233ff786104f33889066f14707fe72_ledger_01.png"
            print(f"Product 136 ({prod136.name}): Updated to ledger_01.png")
        
        # Product 138: Cuplock Ledger System
        prod138 = Product.query.get(138)
        if prod138:
            prod138.image_url = "uploads/19863a059f2e4d7c84be9255051fe173_ledger_02.png"
            print(f"Product 138 ({prod138.name}): Updated to ledger_02.png")
        
        try:
            db.session.commit()
            print("\n✓ All ledger products updated successfully!")
            print("\nRestart your Flask app now:")
            print("  flask run")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    fix_ledger_products()
