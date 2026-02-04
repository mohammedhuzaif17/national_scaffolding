#!/usr/bin/env python3
"""
Check admin credentials in database and test password verification
"""
from app import app, db, Admin
from werkzeug.security import check_password_hash

with app.app_context():
    print("=" * 70)
    print("ADMIN CREDENTIALS CHECK")
    print("=" * 70)
    
    # Get all admins
    admins = Admin.query.all()
    
    if not admins:
        print("\n❌ No admins found in database!")
        exit(1)
    
    print(f"\n Found {len(admins)} admin(s):\n")
    for admin in admins:
        print(f"ID: {admin.id}")
        print(f"  Username: {admin.username}")
        print(f"  Panel Type: {admin.panel_type}")
        print(f"  Password Hash: {admin.password_hash[:40]}...")
        print(f"  Hash Type: {admin.password_hash.split(':')[0] if ':' in admin.password_hash else 'UNKNOWN'}")
        
        # Check if it's a plain password (not hashed)
        if not admin.password_hash.startswith('pbkdf2:') and not admin.password_hash.startswith('bcrypt:'):
            print(f"  ⚠️  WARNING: This looks like a PLAIN PASSWORD, not hashed!")
        print()
    
    print("=" * 70)
    print("WHAT YOU NEED TO DO:")
    print("=" * 70)
    print("\n1. Get the plain password you set in Neon")
    print("2. Run this script: python hash_admin_password.py 'your_password'")
    print("3. Update the admin in Neon with the hashed password")
    print("\nOR let me hash it for you. What's the new plain password?")
