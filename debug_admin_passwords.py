#!/usr/bin/env python3
"""
Check and fix admin passwords in Neon database using Flask app context
"""
import sys

try:
    from app import app, db, Admin
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        print("=" * 70)
        print("ADMIN CREDENTIALS IN NEON DATABASE")
        print("=" * 70 + "\n")
        
        # Query all admins
        admins = Admin.query.all()
        
        if not admins:
            print("NO admins found in database!\n")
            exit(1)
        
        print(f"Found {len(admins)} admin(s):\n")
        
        has_plain_password = False
        
        for admin in admins:
            print(f"ID: {admin.id}")
            print(f"  Username: {admin.username}")
            print(f"  Panel: {admin.panel_type}")
            print(f"  Password Hash: {admin.password_hash}")
            
            # Check if it's hashed
            if admin.password_hash.startswith('pbkdf2:') or admin.password_hash.startswith('bcrypt:'):
                print(f"  Status: PROPERLY HASHED")
            else:
                print(f"  Status: PLAIN PASSWORD (NOT HASHED!)")
                has_plain_password = True
            print()
        
        if has_plain_password:
            print("=" * 70)
            print("ISSUE FOUND!")
            print("=" * 70)
            print("\nSome admins have PLAIN PASSWORDS instead of hashed passwords.")
            print("This is why login is failing!\n")
            print("What is the PLAIN password you want to use for the admins?")
            print("(You need to tell me so I can hash it properly)")
            
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

