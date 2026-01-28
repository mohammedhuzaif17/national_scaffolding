#!/usr/bin/env python
"""
Add cup options for all vertical cuplock sizes
"""
from app import app, db
from models import CuplockVerticalSize, CuplockVerticalCup

def add_cups():
    """Add cup configurations for vertical sizes"""
    
    # Define cup configurations for each size
    # Format: {size_label: [cup_counts]}
    cups_config = {
        '1M x 1M': [1, 2],
        '1.5M x 1.5M': [2, 3],
        '2M x 2M': [2, 3, 4],
        '2.5M x 2.5M': [2, 3, 4],
        '3M x 3M': [3, 4, 6],
    }
    
    # Cup pricing (incremental cost per additional cup)
    cup_price_multiplier = 150  # Base price per cup
    
    with app.app_context():
        try:
            # Get all vertical sizes
            sizes = CuplockVerticalSize.query.all()
            
            if not sizes:
                print("No vertical sizes found!")
                return
            
            added_count = 0
            
            for size in sizes:
                print(f"\nProcessing size: {size.size_label} (ID: {size.id})")
                
                # Get cup counts for this size
                cup_counts = cups_config.get(size.size_label, [])
                
                if not cup_counts:
                    print(f"  No cup configuration for this size")
                    continue
                
                for cup_count in cup_counts:
                    # Check if this cup configuration already exists
                    existing = CuplockVerticalCup.query.filter_by(
                        vertical_size_id=size.id,
                        cup_count=cup_count
                    ).first()
                    
                    if existing:
                        print(f"  - {cup_count} cup(s): Already exists (ID: {existing.id})")
                        continue
                    
                    # Calculate cup price based on cup count
                    # First cup is free (included in size), each additional cup costs more
                    cup_additional_cost = (cup_count - 1) * cup_price_multiplier
                    
                    # Create new cup record
                    new_cup = CuplockVerticalCup(
                        vertical_size_id=size.id,
                        cup_count=cup_count,
                        buy_price=float(size.buy_price or 0) + cup_additional_cost,
                        rent_price=float(size.rent_price or 0) + (cup_additional_cost / 20),  # Rent is ~5% of buy
                        deposit_amount=float(size.deposit or 0) + (cup_additional_cost / 5),  # Deposit is ~20% of buy
                        display_order=cup_count
                    )
                    
                    db.session.add(new_cup)
                    added_count += 1
                    print(f"  + {cup_count} cup(s): buy={new_cup.buy_price:.2f}, rent={new_cup.rent_price:.2f}, deposit={new_cup.deposit_amount:.2f}")
            
            # Commit all changes
            db.session.commit()
            
            print("\n" + "="*70)
            print(f"SUCCESS: Added {added_count} cup configurations!")
            
            # Verify
            print("\nVERIFYING...")
            for size in sizes:
                cups = CuplockVerticalCup.query.filter_by(vertical_size_id=size.id).all()
                print(f"  {size.size_label}: {len(cups)} cup options")
                
        except Exception as e:
            print(f"ERROR: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_cups()
