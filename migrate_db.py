#!/usr/bin/env python3
"""
Migration script to add cuplock_type column and set up cuplock products
Run this after updating your models.py
"""

from app import app
from models import db, Product
import json

def add_cuplock_type_column():
    """Add cuplock_type column to products table"""
    with app.app_context():
        try:
            # Check if the column already exists
            result = db.session.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' AND column_name = 'cuplock_type'
            """)).fetchone()
            
            if not result:
                # Add the cuplock_type column
                db.session.execute(db.text("""
                    ALTER TABLE products 
                    ADD COLUMN cuplock_type VARCHAR(50)
                """))
                db.session.commit()
                print("✅ Added cuplock_type column to products table")
            else:
                print("ℹ️ cuplock_type column already exists")
                
        except Exception as e:
            print(f"❌ Error adding cuplock_type column: {e}")
            db.session.rollback()


def create_sample_cuplock_products():
    """Create sample cuplock products for testing"""
    with app.app_context():
        try:
            # Check if cuplock products already exist
            existing = Product.query.filter_by(category='cuplock').first()
            if existing:
                print("ℹ️ Cuplock products already exist")
                return
            
            # Create Vertical Cuplock Product
            vertical_pricing = {
                "cuplock_type": "vertical",
                "pricing_matrix": {
                    "rent": {
                        "1m": {"price": 50, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "1.5m": {"price": 60, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "2m": {"price": 70, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "2.5m": {"price": 80, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "3m": {"price": 90, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]}
                    },
                    "buy": {
                        "1m": {
                            "1_cup": {"price_per_kg": 78, "weight_kg": 5},
                            "2_cup": {"price_per_kg": 78, "weight_kg": 6}
                        },
                        "1.5m": {
                            "2_cup": {"price_per_kg": 78, "weight_kg": 7},
                            "3_cup": {"price_per_kg": 78, "weight_kg": 8}
                        },
                        "2m": {
                            "2_cup": {"price_per_kg": 78, "weight_kg": 9},
                            "3_cup": {"price_per_kg": 78, "weight_kg": 10},
                            "4_cup": {"price_per_kg": 78, "weight_kg": 11}
                        },
                        "2.5m": {
                            "2_cup": {"price_per_kg": 78, "weight_kg": 12},
                            "3_cup": {"price_per_kg": 78, "weight_kg": 13},
                            "4_cup": {"price_per_kg": 78, "weight_kg": 14}
                        },
                        "3m": {
                            "2_cup": {"price_per_kg": 78, "weight_kg": 15},
                            "3_cup": {"price_per_kg": 78, "weight_kg": 16},
                            "4_cup": {"price_per_kg": 78, "weight_kg": 17},
                            "6_cup": {"price_per_kg": 78, "weight_kg": 20}
                        }
                    }
                }
            }
            
            vertical_product = Product(
                name="Cuplock Vertical",
                price=390.00,  # Default price
                description="High-quality cuplock vertical scaffolding with multiple size and cup configuration options",
                category="cuplock",
                cuplock_type="vertical",
                product_type="scaffolding",
                customization_options=vertical_pricing,
                rent_price=50.00,
                deposit_amount=0,
                weight_per_unit=5.0
            )
            
            db.session.add(vertical_product)
            
            # Create Ledger Cuplock Product
            ledger_pricing = {
                "cuplock_type": "ledger",
                "pricing_matrix": {
                    "rent": {
                        "0.9m": {"price": 30, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "1m": {"price": 35, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "1.2m": {"price": 40, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "1.5m": {"price": 45, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "1.8m": {"price": 50, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "2m": {"price": 55, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "2.2m": {"price": 60, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "2.5m": {"price": 65, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "2.8m": {"price": 70, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]},
                        "3m": {"price": 75, "quantity_options": [1, 2, 3, 5, 10, 20, 50, 100]}
                    },
                    "buy": {
                        "0.9m": {"price_per_kg": 78, "weight_kg": 3.5},
                        "1m": {"price_per_kg": 78, "weight_kg": 4},
                        "1.2m": {"price_per_kg": 78, "weight_kg": 4.5},
                        "1.5m": {"price_per_kg": 78, "weight_kg": 5},
                        "1.8m": {"price_per_kg": 78, "weight_kg": 6},
                        "2m": {"price_per_kg": 78, "weight_kg": 7},
                        "2.2m": {"price_per_kg": 78, "weight_kg": 7.5},
                        "2.5m": {"price_per_kg": 78, "weight_kg": 8},
                        "2.8m": {"price_per_kg": 78, "weight_kg": 8.5},
                        "3m": {"price_per_kg": 78, "weight_kg": 9}
                    }
                }
            }
            
            ledger_product = Product(
                name="Cuplock Ledger",
                price=273.00,  # Default price (3.5kg * 78)
                description="Durable cuplock ledger scaffolding available in multiple sizes for buy or rent",
                category="cuplock",
                cuplock_type="ledger",
                product_type="scaffolding",
                customization_options=ledger_pricing,
                rent_price=30.00,
                deposit_amount=0,
                weight_per_unit=3.5
            )
            
            db.session.add(ledger_product)
            
            db.session.commit()
            print("✅ Created sample cuplock products (Vertical and Ledger)")
            
        except Exception as e:
            print(f"❌ Error creating sample cuplock products: {e}")
            db.session.rollback()


def update_existing_cuplock_products():
    """Update any existing cuplock products to use the new structure"""
    with app.app_context():
        try:
            cuplock_products = Product.query.filter_by(category='cuplock').all()
            
            for product in cuplock_products:
                # Set default cuplock_type if not set
                if not product.cuplock_type:
                    product.cuplock_type = 'vertical'  # Default
                    print(f"✅ Set cuplock_type for product: {product.name}")
                
                # Ensure customization_options has proper structure
                if not product.customization_options or 'pricing_matrix' not in product.customization_options:
                    print(f"⚠️ Product {product.name} needs pricing configuration")
            
            db.session.commit()
            print("✅ Updated existing cuplock products")
            
        except Exception as e:
            print(f"❌ Error updating existing cuplock products: {e}")
            db.session.rollback()


if __name__ == "__main__":
    print("=" * 60)
    print("Cuplock Migration Script")
    print("=" * 60)
    
    # Step 1: Add column
    print("\n1. Adding cuplock_type column...")
    add_cuplock_type_column()
    
    # Step 2: Create sample products (optional)
    print("\n2. Creating sample cuplock products...")
    create_sample_cuplock_products()
    
    # Step 3: Update existing products
    print("\n3. Updating existing cuplock products...")
    update_existing_cuplock_products()
    
    print("\n" + "=" * 60)
    print("Migration completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update your models.py to add the cuplock_type field")
    print("2. Add the new routes from cuplock_routes.py to your app.py")
    print("3. Create the admin_cuplock_pricing.html template")
    print("4. Update product_detail.html with cuplock customization")
    print("5. Test the cuplock functionality")
    print("=" * 60)