#!/usr/bin/env python3
"""Diagnose admin login issues - compare scaffolding vs fabrication"""

from app import app, db
from models import Admin

print("\n" + "="*70)
print("DIAGNOSING ADMIN LOGIN ISSUE")
print("="*70)

with app.app_context():
    # Get both admins
    scaffolding_admin = Admin.query.filter_by(username='admin', panel_type='scaffolding').first()
    fabrication_admin = Admin.query.filter_by(username='admin', panel_type='fabrication').first()
    
    print("\n" + "="*70)
    print("ADMIN ACCOUNTS STATUS")
    print("="*70)
    
    print("\n[SCAFFOLDING ADMIN]")
    if scaffolding_admin:
        print(f"  ID: {scaffolding_admin.id}")
        print(f"  Username: {scaffolding_admin.username}")
        print(f"  Panel Type: {scaffolding_admin.panel_type}")
        print(f"  Password Hash: {scaffolding_admin.password_hash[:50]}...")
        print(f"  Password Verification ('admin123'): {scaffolding_admin.check_password('admin123')}")
    else:
        print("  [ERROR] ACCOUNT NOT FOUND IN DATABASE!")
    
    print("\n[FABRICATION ADMIN]")
    if fabrication_admin:
        print(f"  ID: {fabrication_admin.id}")
        print(f"  Username: {fabrication_admin.username}")
        print(f"  Panel Type: {fabrication_admin.panel_type}")
        print(f"  Password Hash: {fabrication_admin.password_hash[:50]}...")
        print(f"  Password Verification ('admin123'): {fabrication_admin.check_password('admin123')}")
    else:
        print("  [ERROR] ACCOUNT NOT FOUND IN DATABASE!")
    
    print("\n" + "="*70)
    print("DIAGNOSIS")
    print("="*70)
    
    if scaffolding_admin and fabrication_admin:
        scaff_pwd_ok = scaffolding_admin.check_password('admin123')
        fab_pwd_ok = fabrication_admin.check_password('admin123')
        
        print(f"\nScaffolding password check: {'PASS' if scaff_pwd_ok else 'FAIL'}")
        print(f"Fabrication password check: {'PASS' if fab_pwd_ok else 'FAIL'}")
        
        if scaff_pwd_ok and fab_pwd_ok:
            print("\n[OK] Both passwords are correct!")
            print("Issue must be in OTP verification or session handling")
        elif not scaff_pwd_ok and fab_pwd_ok:
            print("\n[ERROR] Scaffolding admin password is WRONG!")
            print("Need to recreate scaffolding admin account with correct password")
        elif scaff_pwd_ok and not fab_pwd_ok:
            print("\n[ERROR] Fabrication admin password is WRONG!")
            print("Need to recreate fabrication admin account with correct password")
        else:
            print("\n[ERROR] Both passwords are WRONG!")
    else:
        print("\n[ERROR] One or both admin accounts missing!")
        print("Need to recreate both accounts")
    
    # Check all admins
    print("\n" + "="*70)
    print("ALL ADMIN ACCOUNTS IN DATABASE")
    print("="*70)
    
    all_admins = Admin.query.all()
    print(f"\nTotal: {len(all_admins)}")
    
    for admin in all_admins:
        pwd_check = admin.check_password('admin123')
        print(f"\n  {admin.username} ({admin.panel_type})")
        print(f"    ID: {admin.id}")
        print(f"    Password 'admin123': {'OK' if pwd_check else 'WRONG'}")

print("\n" + "="*70 + "\n")
