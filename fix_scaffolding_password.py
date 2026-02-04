#!/usr/bin/env python3
"""
Reset scaffolding admin password to match fabrication admin password
"""
from app import app, db, Admin

with app.app_context():
    print("=" * 70)
    print("RESETTING SCAFFOLDING ADMIN PASSWORD")
    print("=" * 70)

    # Get fabrication admin password hash
    fab_admin = Admin.query.filter_by(username='admin', panel_type='fabrication').first()
    if not fab_admin:
        print("❌ ERROR: Fabrication admin not found!")
        exit(1)

    print(f"\n✓ Fabrication admin found")
    fab_hash = fab_admin.password_hash

    # Get scaffolding admin
    scaf_admin = Admin.query.filter_by(username='admin', panel_type='scaffolding').first()
    if not scaf_admin:
        print("❌ ERROR: Scaffolding admin not found!")
        exit(1)

    print(f"✓ Scaffolding admin found")

    # Update scaffolding password
    scaf_admin.password_hash = fab_hash
    db.session.commit()

    print("\n" + "=" * 70)
    print("✅ SUCCESS! Password updated in database")
    print("=" * 70)
    print("\nBoth admins now have the SAME password:")
    print(f"  Fabrication: {fab_admin.password_hash[:30]}...{fab_admin.password_hash[-10:]}")
    print(f"  Scaffolding: {scaf_admin.password_hash[:30]}...{scaf_admin.password_hash[-10:]}")
    print("\nYou can now login to BOTH panels with:")
    print("  Username: admin")
    print("  Password: [your fabrication password]")
