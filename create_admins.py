"""
Admin Creation Script for National Scaffolding
Creates two admin accounts with plain text passwords
"""

from app import app, db
from models import Admin

def create_default_admins():
    """Create default admin accounts"""
    with app.app_context():
        try:
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
                # Update password if admin exists
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
                # Update password if admin exists
                fabrication_admin.set_password('admin123')
                print("✅ Updated fabrication admin password")
            
            db.session.commit()
            print("\n✅ All admin accounts ready!")
            print("=" * 50)
            print("ADMIN CREDENTIALS:")
            print("=" * 50)
            print("Scaffolding Admin:")
            print("  Username: admin_scaffolding")
            print("  Password: admin123")
            print("  Panel: Scaffolding")
            print()
            print("Fabrication Admin:")
            print("  Username: admin_fabrication")
            print("  Password: admin123")
            print("  Panel: Fabrication")
            print("=" * 50)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admins: {e}")
            raise

if __name__ == "__main__":
    create_default_admins()