#!/usr/bin/env python3
"""
Interactive script to hash and update admin password
"""
import sys

print("=" * 70)
print("ADMIN PASSWORD SETUP")
print("=" * 70 + "\n")

# Ask for the password
print("What plain password do you want to use for both admins?")
plain_password = input("Enter password: ").strip()

if not plain_password:
    print("ERROR: Password cannot be empty!")
    exit(1)

print(f"\nPassword entered: {plain_password}")
print("\nNow importing Flask app to hash and update...")

try:
    from app import app, db, Admin
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        # Get both admins
        fab_admin = Admin.query.filter_by(panel_type='fabrication').first()
        scaf_admin = Admin.query.filter_by(panel_type='scaffolding').first()
        
        if not fab_admin or not scaf_admin:
            print("ERROR: Could not find both admin accounts!")
            exit(1)
        
        print(f"Found both admins:")
        print(f"  Fabrication: {fab_admin.username}")
        print(f"  Scaffolding: {scaf_admin.username}")
        
        print(f"\nHashing password...")
        
        # Hash the password
        hashed = generate_password_hash(plain_password, method='pbkdf2:sha256')
        
        print(f"Hash generated: {hashed[:40]}...")
        
        # Update both admins with the same hashed password
        fab_admin.password_hash = hashed
        scaf_admin.password_hash = hashed
        
        db.session.commit()
        
        print("\n" + "=" * 70)
        print("SUCCESS! Passwords updated in database")
        print("=" * 70)
        print("\nBoth admin accounts now have:")
        print(f"  Username: admin")
        print(f"  Password: {plain_password}")
        print("\nYou can now login to either panel!")
        
except Exception as e:
    import traceback
    print(f"\nERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
