#!/usr/bin/env python3
"""
Check pricing for all 3 cuplock products and their sizes
"""

from app import app, db
from models import Product, CuplockVerticalSize, CuplockLedgerSize

def check_pricing():
    with app.app_context():
        print("\n" + "="*100)
        print("CUPLOCK PRODUCTS PRICING CHECK")
        print("="*100)
        
        # Get all cuplock products
        products = Product.query.filter(
            db.or_(
                db.and_(Product.category.ilike('%cuplock%'), Product.cuplock_type.ilike('%vertical%')),
                db.and_(Product.category.ilike('%cuplock%'), Product.cuplock_type.ilike('%ledger%'))
            )
        ).all()
        
        for prod in products:
            prod_type = prod.cuplock_type or "unknown"
            print(f"\n{'='*100}")
            print(f"Product ID: {prod.id} | {prod.name} | Type: {prod_type.upper()}")
            print(f"  Product-level price: {prod.price}")
            print(f"{'='*100}")
            
            if prod_type.lower() == 'vertical':
                sizes = CuplockVerticalSize.query.filter_by(product_id=prod.id, is_active=True).all()
                if not sizes:
                    print("  ⚠️  NO ACTIVE SIZES CONFIGURED!")
                else:
                    print(f"  Total Sizes: {len(sizes)}\n")
                    for sz in sizes:
                        buy = float(sz.buy_price or 0)
                        rent = float(sz.rent_price or 0)
                        deposit = float(sz.deposit or 0)
                        print(f"    Size: {sz.size_label}")
                        print(f"      Buy Price:     ₹{buy:>8,.2f}")
                        print(f"      Rent Price:    ₹{rent:>8,.2f}")
                        print(f"      Deposit:       ₹{deposit:>8,.2f}")
                        print()
            
            elif prod_type.lower() == 'ledger':
                sizes = CuplockLedgerSize.query.filter_by(product_id=prod.id, is_active=True).all()
                if not sizes:
                    print("  ⚠️  NO ACTIVE SIZES CONFIGURED!")
                else:
                    print(f"  Total Sizes: {len(sizes)}\n")
                    for sz in sizes:
                        buy = float(sz.buy_price or 0)
                        rent = float(sz.rent_price or 0)
                        deposit = float(sz.deposit_amount or 0)
                        print(f"    Size: {sz.size_label}")
                        print(f"      Buy Price:     ₹{buy:>8,.2f}")
                        print(f"      Rent Price:    ₹{rent:>8,.2f}")
                        print(f"      Deposit:       ₹{deposit:>8,.2f}")
                        print()
        
        print("\n" + "="*100)
        print("PRICING ISSUES TO CHECK:")
        print("="*100)
        print("""
1. Are buy prices consistent for the same size across products?
2. Are rent prices (if any) reasonable?
3. Are deposits reasonable (typically 30-50% of buy price)?
4. Do all sizes have at least a buy price or rent price set?
5. Are there any prices that look wrong (too high/low)?

If you want to update any prices, let me know:
- Which product (ID or name)
- Which size
- New buy price / rent price / deposit
        """)

if __name__ == '__main__':
    check_pricing()
