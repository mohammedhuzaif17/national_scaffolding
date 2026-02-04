#!/usr/bin/env python3
"""
Update admin usernames to 'admin' for both panels
"""
import sys

try:
    from app import app, db, Admin
    
    with app.app_context():
        print("=" * 70)
        print("UPDATING ADMIN USERNAMES")
        print("=" * 70 + "\n")
        
        # Get both admins
        fab_admin = Admin.query.filter_by(panel_type='fabrication').first()
        scaf_admin = Admin.query.filter_by(panel_type='scaffolding').first()
        
        if not fab_admin or not scaf_admin:
            print("ERROR: Could not find both admin accounts!")
            exit(1)
        
        print(f"Before update:")
        print(f"  Fabrication: {fab_admin.username} -> changing to: admin")
        print(f"  Scaffolding: {scaf_admin.username} -> changing to: admin\n")
        
        # Update usernames
        fab_admin.username = 'admin'
        scaf_admin.username = 'admin'
        
        db.session.commit()
        
        print("=" * 70)
        print("SUCCESS! Usernames updated")
        print("=" * 70)
        print("\nBoth admin panels now have:")
        print("  Username: admin")
        print("  Password: [your current password]\n")
        print("You can now login to either panel with username 'admin'")
            
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
