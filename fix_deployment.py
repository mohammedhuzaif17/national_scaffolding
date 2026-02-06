"""
Deployment Fix Script for National Scaffolding
Run this after replacing models.py to fix the database
"""

from app import app, db
from models import Admin, CuplockVerticalSize, CuplockLedgerSize
from sqlalchemy import inspect, text

def check_and_fix_database():
    """Check database schema and fix issues"""
    with app.app_context():
        try:
            print("=" * 60)
            print("CHECKING DATABASE SCHEMA")
            print("=" * 60)
            
            inspector = inspect(db.engine)
            
            # Check if tables exist
            tables = inspector.get_table_names()
            print(f"\n✅ Found {len(tables)} tables in database")
            
            required_tables = [
                'users', 'admins', 'admin_otps', 'products',
                'cuplock_vertical_size', 'cuplock_vertical_cups',
                'cuplock_ledger_sizes', 'orders', 'order_items'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"\n⚠️  Missing tables: {missing_tables}")
                print("Creating missing tables...")
                db.create_all()
                print("✅ Tables created successfully")
            else:
                print("✅ All required tables exist")
            
            # Check cuplock_vertical_size columns
            if 'cuplock_vertical_size' in tables:
                columns = [col['name'] for col in inspector.get_columns('cuplock_vertical_size')]
                print(f"\n✅ cuplock_vertical_size columns: {columns}")
                
                required_columns = ['id', 'product_id', 'size_label', 'buy_price', 'rent_price', 'deposit', 'is_active']
                missing_cols = [c for c in required_columns if c not in columns]
                
                if missing_cols:
                    print(f"⚠️  Missing columns in cuplock_vertical_size: {missing_cols}")
                    # Add missing columns
                    with db.engine.connect() as conn:
                        for col in missing_cols:
                            if col == 'is_active':
                                conn.execute(text("ALTER TABLE cuplock_vertical_size ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                            elif col in ['buy_price', 'rent_price', 'deposit']:
                                conn.execute(text(f"ALTER TABLE cuplock_vertical_size ADD COLUMN {col} NUMERIC(10,2)"))
                        conn.commit()
                    print("✅ Added missing columns")
            
            # Check foreign keys
            fks = inspector.get_foreign_keys('cuplock_vertical_cups')
            print(f"\n✅ Foreign keys in cuplock_vertical_cups: {len(fks)}")
            
            has_vertical_size_fk = any(
                fk['referred_table'] == 'cuplock_vertical_size' 
                for fk in fks
            )
            
            if has_vertical_size_fk:
                print("✅ Foreign key relationship exists between cuplock_vertical_cups and cuplock_vertical_size")
            else:
                print("⚠️  Foreign key relationship missing - this may cause issues")
            
            print("\n" + "=" * 60)
            print("DATABASE CHECK COMPLETE")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Database check failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def create_admin_accounts():
    """Create default admin accounts"""
    with app.app_context():
        try:
            print("\n" + "=" * 60)
            print("CREATING ADMIN ACCOUNTS")
            print("=" * 60)
            
            # Create scaffolding admin
            scaffolding_admin = Admin.query.filter_by(
                username='admin_scaffolding',
                panel_type='scaffolding'
            ).first()
            
            if not scaffolding_admin:
                scaffolding_admin = Admin(
                    username='admin_scaffolding',
                    panel_type='scaffolding'
                )
                scaffolding_admin.set_password('admin123')
                db.session.add(scaffolding_admin)
                print("✅ Created scaffolding admin")
            else:
                scaffolding_admin.set_password('admin123')
                print("✅ Updated scaffolding admin password")
            
            # Create fabrication admin
            fabrication_admin = Admin.query.filter_by(
                username='admin_fabrication',
                panel_type='fabrication'
            ).first()
            
            if not fabrication_admin:
                fabrication_admin = Admin(
                    username='admin_fabrication',
                    panel_type='fabrication'
                )
                fabrication_admin.set_password('admin123')
                db.session.add(fabrication_admin)
                print("✅ Created fabrication admin")
            else:
                fabrication_admin.set_password('admin123')
                print("✅ Updated fabrication admin password")
            
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("ADMIN CREDENTIALS:")
            print("=" * 60)
            print("Scaffolding: admin_scaffolding / admin123")
            print("Fabrication: admin_fabrication / admin123")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating admins: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Run all fixes"""
    print("\n🔧 STARTING DEPLOYMENT FIXES")
    print("=" * 60)
    
    # Step 1: Check and fix database
    if not check_and_fix_database():
        print("\n❌ Database check failed. Please review errors above.")
        return
    
    # Step 2: Create admin accounts
    create_admin_accounts()
    
    print("\n✅ DEPLOYMENT FIXES COMPLETE!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Restart your application")
    print("2. Login with admin credentials above")
    print("3. Test the /national_scaffoldings page")
    print("\n")


if __name__ == "__main__":
    main()