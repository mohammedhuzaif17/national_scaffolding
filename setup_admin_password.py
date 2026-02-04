#!/usr/bin/env python3
"""
Hash a plain password and update admin accounts with it
"""
import sys

try:
    from app import app, db, Admin
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        print("=" * 70)
        print("ADMIN PASSWORD HASHING AND UPDATE")
        print("=" * 70 + "\n")
        
        # Get both admins
        fab_admin = Admin.query.filter_by(panel_type='fabrication').first()
        scaf_admin = Admin.query.filter_by(panel_type='scaffolding').first()
        
        if not fab_admin or not scaf_admin:
            print("ERROR: Could not find both admin accounts!")
            exit(1)
        
        # Ask for the password
        print("What plain password do you want to use for both admins?")
        plain_password = input("Enter password: ").strip()
        
        if not plain_password:
            print("ERROR: Password cannot be empty!")
            exit(1)
        
        print(f"\nHashing password: {plain_password}")
        
        # Hash the password
        hashed = generate_password_hash(plain_password, method='pbkdf2:sha256')
        
        print(f"\nGenerated hash: {hashed[:50]}...\n")
        
        # Update both admins with the same hashed password
        fab_admin.password_hash = hashed
        scaf_admin.password_hash = hashed
        
        db.session.commit()
        
        print("=" * 70)
        print("SUCCESS! Passwords updated")
        print("=" * 70)
        print("\nBoth admin accounts now have:")
        print(f"  Username: admin")
        print(f"  Password: {plain_password}")
        print("\nYou can now login to either panel!")
            
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
